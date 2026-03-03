# Vercel Deployment Notes

Quick checklist and exact settings to deploy this monorepo (React frontend + Flask backend) on Vercel.

## Option A — Use Vercel UI (recommended)
- **Root Directory:** repository root (leave empty)
- **Framework Preset:** `Other` / `Static` for frontend build step
- **Build Command:**
  - `npm --prefix frontend run build`
- **Output Directory:**
  - `frontend/dist`
- **Functions Directory:** ensure `api/` exists (contains `index.py`)

## Option B — Use `vercel.json` (already in repo)
- We provide `vercel.json` and `api/index.py` so Vercel can auto-detect builds and functions.

## Required Vercel Environment Variables
Set these in Project Settings → Environment Variables (Production & Preview):
- `OPENAI_API_KEY` — your OpenAI secret (rotate if accidentally committed).
- `SECRET_KEY` — Flask secret (generate with `python -c "import secrets; print(secrets.token_urlsafe(64))"`).
- `CORS_ORIGINS` — comma-separated allowed origins (e.g. `https://task-a-master.vercel.app,http://localhost:3000`).
- `LLM_MODEL` — default `gpt-5.2`.
- `EMBEDDING_MODEL` — default `text-embedding-3-small`.

## Verification (once deployed)
- Health endpoint: `GET https://<your-deploy>/api/health` — returns non-sensitive config and DB presence.
- Check frontend: open `https://<your-deploy>/` in browser. If blank, open DevTools → Network to find failing asset paths.
- Check API: `curl -i https://<your-deploy>/api/health`

## Logs & Debug
- Vercel Dashboard → Deployments → select the deployment → Logs shows build and function logs.
- Use the `Visit` button to open the site and browser console for runtime errors.

## Important Notes
- Serverless functions on Vercel are ephemeral: local SQLite and `documents/` will not persist between invocations. For production, use a managed DB (Postgres) and object storage (S3/GCS).
- Remove any API keys from committed `.env` and rotate secrets immediately if exposed.

If you want, I can also add a small `vercel-setup.md` with screenshots of the exact dashboard fields.
