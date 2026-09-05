"""Local demo-deployment helper using ngrok and FastAPI.

Starts the FastAPI backend and an ngrok tunnel, retrieves the public HTTPS URL
from the ngrok local API, updates frontend/.env.local, and keeps running until
interrupted with Ctrl+C.
"""

import atexit
import json
import os
import shutil
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = REPO_ROOT / "backend"
FRONTEND_ENV = REPO_ROOT / "frontend" / ".env.local"
NGROK_API_URL = "http://127.0.0.1:4040/api/tunnels"


def resolve_uvicorn_command() -> list[str]:
    """Find the best command to invoke uvicorn."""
    # 1. If the repository has a virtual environment, prefer its python interpreter
    scripts_dir = "Scripts" if os.name == "nt" else "bin"
    exe_name = "python.exe" if os.name == "nt" else "python"
    venv_py = REPO_ROOT / "venv" / scripts_dir / exe_name
    if venv_py.exists():
        return [str(venv_py), "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

    # 2. Check if uvicorn is available on the system PATH
    uvicorn_path = shutil.which("uvicorn")
    if uvicorn_path:
        return [uvicorn_path, "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

    # 3. Fall back to running as a python module using the current interpreter
    return [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]


def terminate_process(proc: subprocess.Popen | None, name: str) -> None:
    """Terminate a process and any child processes cleanly."""
    if proc is None or proc.poll() is not None:
        return

    try:
        if os.name == "nt":
            # On Windows, taskkill /F /T kills the entire process tree (e.g. uvicorn reloader workers)
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
        else:
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass


def query_ngrok_public_url(max_retries: int = 10, delay_sec: float = 1.0) -> str | None:
    """Query ngrok's local API (http://127.0.0.1:4040/api/tunnels) for the public HTTPS URL."""
    for _ in range(max_retries):
        try:
            req = urllib.request.Request(
                NGROK_API_URL,
                headers={"Accept": "application/json", "User-Agent": "ThreatIQ-DemoHelper"},
            )
            with urllib.request.urlopen(req, timeout=3) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    tunnels = data.get("tunnels", [])
                    # Prefer HTTPS tunnel
                    for tunnel in tunnels:
                        public_url = tunnel.get("public_url", "")
                        if public_url.startswith("https://"):
                            return public_url
                    # Fallback to any public URL
                    for tunnel in tunnels:
                        public_url = tunnel.get("public_url", "")
                        if public_url:
                            return public_url
        except (urllib.error.URLError, ConnectionError, OSError, json.JSONDecodeError):
            pass

        time.sleep(delay_sec)

    return None


def update_frontend_env(tunnel_url: str) -> None:
    """Write or update NEXT_PUBLIC_API_URL in frontend/.env.local without altering other entries."""
    target_key = "NEXT_PUBLIC_API_URL"
    new_entry = f"{target_key}={tunnel_url}"

    if not FRONTEND_ENV.exists():
        FRONTEND_ENV.parent.mkdir(parents=True, exist_ok=True)
        FRONTEND_ENV.write_text(f"{new_entry}\n", encoding="utf-8")
        return

    content = FRONTEND_ENV.read_text(encoding="utf-8")
    lines = content.splitlines(keepends=True)

    found = False
    updated_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(f"{target_key}=") or stripped == target_key:
            updated_lines.append(f"{new_entry}\n")
            found = True
        else:
            updated_lines.append(line)

    if not found:
        if updated_lines and not updated_lines[-1].endswith("\n"):
            updated_lines[-1] += "\n"
        updated_lines.append(f"{new_entry}\n")

    FRONTEND_ENV.write_text("".join(updated_lines), encoding="utf-8")


def main() -> int:
    backend_proc: subprocess.Popen | None = None
    ngrok_proc: subprocess.Popen | None = None
    cleaned_up = False

    def cleanup() -> None:
        nonlocal cleaned_up
        if cleaned_up:
            return
        cleaned_up = True
        print("\nShutting down demo services...")
        terminate_process(ngrok_proc, "ngrok")
        terminate_process(backend_proc, "FastAPI backend")
        print("Demo services stopped successfully.")

    atexit.register(cleanup)

    # Handle termination signals
    def handle_signal(sig, frame):
        cleanup()
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_signal)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, handle_signal)
    if hasattr(signal, "SIGBREAK"):
        signal.signal(signal.SIGBREAK, handle_signal)

    print("Starting FastAPI backend (uvicorn main:app --host 0.0.0.0 --port 8000 --reload)...")
    uvicorn_cmd = resolve_uvicorn_command()
    try:
        backend_proc = subprocess.Popen(
            uvicorn_cmd,
            cwd=str(BACKEND_DIR),
        )
    except Exception as err:
        print(f"[ERROR] Failed to start FastAPI backend: {err}")
        return 1

    print("Starting ngrok tunnel (ngrok http 8000)...")
    try:
        ngrok_proc = subprocess.Popen(
            ["ngrok", "http", "8000"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception as err:
        print(f"[ERROR] Failed to start ngrok: {err}")
        cleanup()
        return 1

    # Wait a couple seconds before querying ngrok's local API
    print("Waiting for ngrok tunnel initialization...")
    time.sleep(2.0)

    tunnel_url = query_ngrok_public_url(max_retries=10, delay_sec=1.0)
    if not tunnel_url:
        print("\n" + "=" * 72)
        print("[ERROR] Failed to query ngrok local API at http://127.0.0.1:4040/api/tunnels.")
        print("Please check that ngrok is running and authenticated on this machine.")
        print("  - To authenticate: ngrok config add-authtoken <your-authtoken>")
        print("  - To check ngrok status manually: ngrok http 8000")
        print("=" * 72 + "\n")
        cleanup()
        return 1

    update_frontend_env(tunnel_url)

    banner = [
        "=" * 72,
        "                      THREATIQ DEMO TUNNEL ACTIVE",
        "=" * 72,
        f"  Public Tunnel URL  : {tunnel_url}",
        f"  Frontend Config    : frontend/.env.local",
        f"  NEXT_PUBLIC_API_URL: {tunnel_url}",
        "=" * 72,
        "  NOTE: If the Next.js frontend is already running, restart it",
        "  (Ctrl+C then 'npm run dev') to load the new environment variable.",
        "",
        "  Running demo services. Press Ctrl+C to stop.",
        "=" * 72,
    ]
    print("\n" + "\n".join(banner) + "\n", flush=True)

    try:
        while True:
            # Monitor subprocess health
            if backend_proc.poll() is not None:
                print(f"\n[ERROR] FastAPI backend exited unexpectedly with code {backend_proc.returncode}.")
                break
            if ngrok_proc.poll() is not None:
                print(f"\n[ERROR] ngrok exited unexpectedly with code {ngrok_proc.returncode}.")
                break
            time.sleep(1.0)
    except KeyboardInterrupt:
        pass
    finally:
        cleanup()

    return 0


if __name__ == "__main__":
    sys.exit(main())
