# ThreatIQ Local Demo Helper

`scripts/start_demo.py` is a local demo-deployment helper that launches the FastAPI backend and an ngrok HTTP tunnel concurrently. It queries ngrok's local management API (`http://127.0.0.1:4040/api/tunnels`) to obtain your active public HTTPS URL and automatically writes or updates `NEXT_PUBLIC_API_URL` in `frontend/.env.local`. When you are finished, pressing `Ctrl+C` cleanly terminates both the backend and ngrok processes.

## Running the Demo

From the project root, run:

```bash
python scripts/start_demo.py
```

## Important Notes

- **Frontend Restart Required**: The first time the public URL is written (or whenever the ngrok URL changes), restart your Next.js frontend dev server (`npm run dev` in `frontend/`). Next.js loads environment variables at process startup and does not hot-reload `.env.local` changes while running.
- **Demo Purposes Only**: This setup is strictly intended for local demonstrations, testing webhooks, or sharing preview builds. It is not suitable for production deployments.
