"""Settings models for ThreatIQ configuration."""

from typing import Literal, Optional
from pydantic import BaseModel, Field


class ThreatIQSettings(BaseModel):
    """Configuration settings for ThreatIQ pipeline, scoring, and workspace."""

    # AI & Detection Engine
    llm_model: str = Field(
        default="gemini-1.5-flash",
        description="LLM model identifier for threat explanation reasoning",
    )
    anomaly_sensitivity: float = Field(
        default=0.85,
        ge=0.50,
        le=0.99,
        description="Isolation Forest anomaly score cut-off threshold",
    )
    enable_fast_detector: bool = Field(
        default=True,
        description="Enable vectorized C-compiled fast anomaly detector",
    )
    cache_explanations: bool = Field(
        default=True,
        description="Enable pre-generated and in-memory LLM response caching",
    )

    # RAG & Knowledge Base
    top_k_documents: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum number of threat intelligence documents to retrieve per incident",
    )
    similarity_threshold: float = Field(
        default=0.65,
        ge=0.30,
        le=0.95,
        description="Minimum cosine similarity cutoff for RAG vector retrieval",
    )
    index_mitre_attack: bool = Field(
        default=True,
        description="Enable MITRE ATT&CK enterprise v14 vector lookup",
    )
    index_cve_database: bool = Field(
        default=True,
        description="Enable NVD/CVE vulnerability vector lookup",
    )

    # Risk Scoring & Criticality Thresholds
    critical_score_threshold: int = Field(
        default=80,
        ge=70,
        le=95,
        description="Composite score threshold for CRITICAL severity classification",
    )
    high_score_threshold: int = Field(
        default=60,
        ge=45,
        le=79,
        description="Composite score threshold for HIGH severity classification",
    )
    medium_score_threshold: int = Field(
        default=30,
        ge=15,
        le=59,
        description="Composite score threshold for MEDIUM severity classification",
    )
    crown_jewel_multiplier: float = Field(
        default=2.0,
        ge=1.0,
        le=3.0,
        description="Multiplier applied to asset criticality for crown-jewel assets",
    )

    # SOC Alerts & Integrations
    webhook_enabled: bool = Field(
        default=False,
        description="Enable outgoing webhook dispatch on high/critical incidents",
    )
    webhook_url: Optional[str] = Field(
        default="",
        description="Destination URL for Slack/Teams/SIEM webhook notifications",
    )
    auto_escalate_critical: bool = Field(
        default=True,
        description="Automatically transition critical incidents (score >= 80) to 'escalated'",
    )
    email_digest: bool = Field(
        default=False,
        description="Send daily summary threat briefings",
    )
    notify_email: Optional[str] = Field(
        default="soc-ops@threatiq.internal",
        description="Target email address for security digests",
    )

    # Analyst Workspace
    analyst_name: str = Field(
        default="SOC Lead Analyst",
        description="Display name for the active analyst session",
    )
    analyst_tier: Literal[
        "Tier 1 Triage",
        "Tier 2 Incident Response",
        "Tier 3 Threat Hunting",
        "SOC Lead",
    ] = Field(
        default="Tier 2 Incident Response",
        description="Analyst operational tier",
    )
    refresh_interval: Literal["10s", "30s", "60s", "off"] = Field(
        default="30s",
        description="Dashboard background telemetry polling interval",
    )
    sound_alerts: bool = Field(
        default=True,
        description="Play audio notification on new critical threat ingress",
    )
