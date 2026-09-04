"""File-upload ingestion routes for ThreatIQ.

Accepts raw security events as multipart file uploads (.json / .csv),
validates them against the EventInput schema (backend/models/event.py),
and runs the shared ThreatPipeline orchestrator (backend/pipeline.py)
exactly like the JSON-body ingestion endpoint in ingest.py.

The pipeline is assembled once at application startup and stored on
``request.app.state.pipeline``; each request rebinds it to the
request-scoped DB session and the current optional services via the
shared ``_run_pipeline`` helper.
"""

import csv
import io
import json
import logging
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile
from pydantic import ValidationError
from sqlalchemy.orm import Session

from backend.api.ingest import MAX_EVENTS_PER_REQUEST, _run_pipeline
from backend.database.db import get_db
from backend.pipeline import ThreatPipeline

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ingest", tags=["ingest"])

# Phase 19-style guard: cap upload size to prevent memory exhaustion.
MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # 5 MB

ALLOWED_EXTENSIONS = (".json", ".csv")

# CSV header aliases -> canonical field names. Both the EventInput
# schema names and the demo dataset names (destination_ip,
# destination_asset, failed_attempts) are accepted.
CSV_COLUMN_ALIASES = {
    "event_id": "event_id",
    "timestamp": "timestamp",
    "source_ip": "source_ip",
    "dest_ip": "dest_ip",
    "destination_ip": "dest_ip",
    "event_type": "event_type",
    "username": "username",
    "attempts": "attempts",
    "failed_attempts": "attempts",
    "bytes_transferred": "bytes_transferred",
    "port": "port",
    "asset": "asset",
    "destination_asset": "asset",
    "asset_criticality": "asset_criticality",
    "protocol": "protocol",
    # Source-only fields consumed by the pipeline (severity/details).
    "raw_severity": "raw_severity",
    "severity": "severity",
    "details": "details",
}

# Canonical fields every upload must provide (required by EventInput;
# event_id is optional - a UUID is generated when omitted).
REQUIRED_EVENT_FIELDS = ("timestamp", "source_ip", "event_type")

# Fields that must carry integer values.
INT_FIELDS = ("attempts", "bytes_transferred", "port")


@router.post("/upload", status_code=201)
async def ingest_upload(
    file: UploadFile,
    request: Request,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Process an uploaded .json or .csv event file through the pipeline."""
    filename = file.filename or ""
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if f".{extension}" not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported file extension "
                f"{('.' + extension) if extension else '(none)'!r}; "
                f"only .json and .csv uploads are accepted."
            ),
        )

    content = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=(
                f"File too large: {len(content)} bytes received; "
                f"maximum allowed is {MAX_UPLOAD_BYTES} bytes (5 MB)."
            ),
        )

    try:
        text = content.decode("utf-8-sig")  # tolerate a UTF-8 BOM
    except UnicodeDecodeError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"File is not valid UTF-8 text: {exc}",
        ) from exc

    if extension == "json":
        raws = _parse_json_events(text)
    else:
        raws = _parse_csv_events(text)

    if not raws:
        raise HTTPException(
            status_code=400,
            detail=f"The uploaded .{extension} file contains no events.",
        )
    if len(raws) > MAX_EVENTS_PER_REQUEST:
        raise HTTPException(
            status_code=413,
            detail=f"Too many events: maximum {MAX_EVENTS_PER_REQUEST} per request",
        )

    _validate_events(raws, source=extension)

    result = _run_pipeline(raws, request, db)
    return {
        "incidents_created": result["incidents_created"],
        "events_processed": result["events_received"],
        "incident_ids": result["incident_ids"],
    }


# ------------------------------------------------------------------ #
# Parsing
# ------------------------------------------------------------------ #


def _parse_json_events(text: str) -> List[Dict[str, Any]]:
    """Parse a JSON upload; it must be a list of event objects."""
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Malformed JSON: {exc.msg} "
                f"(line {exc.lineno}, column {exc.colno})."
            ),
        ) from exc
    if not isinstance(payload, list):
        raise HTTPException(
            status_code=400,
            detail=(
                "JSON upload must be a list of event objects; "
                f"got a {type(payload).__name__} instead."
            ),
        )
    for index, item in enumerate(payload):
        if not isinstance(item, dict):
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Event at index {index} is not a JSON object; "
                    f"got a {type(item).__name__} instead."
                ),
            )
    return payload


def _parse_csv_events(text: str) -> List[Dict[str, Any]]:
    """Parse a CSV upload, mapping header names to event fields."""
    try:
        reader = csv.DictReader(io.StringIO(text))
        fieldnames = reader.fieldnames
        rows = list(reader)
    except csv.Error as exc:
        raise HTTPException(
            status_code=400, detail=f"Malformed CSV: {exc}"
        ) from exc

    if not fieldnames:
        raise HTTPException(
            status_code=400,
            detail="CSV upload is empty or missing its header row.",
        )

    headers = [(h or "").strip() for h in fieldnames]
    unknown = [h for h in headers if h not in CSV_COLUMN_ALIASES]
    if unknown:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unrecognized CSV column(s): {', '.join(unknown)}. "
                f"Supported columns: {', '.join(sorted(CSV_COLUMN_ALIASES))}."
            ),
        )

    canonical_headers = {CSV_COLUMN_ALIASES[h] for h in headers}
    missing = [f for f in REQUIRED_EVENT_FIELDS if f not in canonical_headers]
    if missing:
        raise HTTPException(
            status_code=400,
            detail=(
                f"CSV is missing required column(s): {', '.join(missing)}. "
                f"Required columns: {', '.join(REQUIRED_EVENT_FIELDS)}; "
                f"received columns: {', '.join(headers)}."
            ),
        )

    raws: List[Dict[str, Any]] = []
    for row_number, row in enumerate(rows, start=2):  # row 1 is the header
        if None in row:  # more values than header columns
            raise HTTPException(
                status_code=400,
                detail=(
                    f"CSV row {row_number} has more values than the "
                    f"{len(headers)} header column(s)."
                ),
            )
        raw: Dict[str, Any] = {}
        for header, value in row.items():
            canonical = CSV_COLUMN_ALIASES[header.strip()]
            value = value.strip() if isinstance(value, str) else value
            if value == "":
                value = None
            if value is not None and canonical in INT_FIELDS:
                try:
                    value = int(value)
                except ValueError:
                    raise HTTPException(
                        status_code=400,
                        detail=(
                            f"CSV row {row_number}: column {header!r} must "
                            f"be an integer, got {value!r}."
                        ),
                    ) from None
            raw[canonical] = value
        raws.append(raw)
    return raws


# ------------------------------------------------------------------ #
# Validation
# ------------------------------------------------------------------ #


def _validate_events(raws: List[Dict[str, Any]], *, source: str) -> None:
    """Validate every raw event against the EventInput schema.

    Uses the pipeline's own coercion helper so both the EventInput
    schema and the demo dataset aliases are accepted, and validation
    rules can never drift between the upload endpoint and the pipeline.
    """
    for index, raw in enumerate(raws):
        label = (
            f"CSV row {index + 2}" if source == "csv"
            else f"Event at index {index}"
        )
        try:
            ThreatPipeline._to_event_input(raw)
        except ValidationError as exc:
            problems = "; ".join(
                f"{'.'.join(str(loc) for loc in err['loc']) or 'event'}: "
                f"{err['msg']}"
                for err in exc.errors()
            )
            raise HTTPException(
                status_code=400,
                detail=f"{label} failed validation - {problems}",
            ) from exc
        except (TypeError, ValueError) as exc:
            raise HTTPException(
                status_code=400,
                detail=f"{label} failed validation - {exc}",
            ) from exc
