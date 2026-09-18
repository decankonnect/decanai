# Decan AI

Decan AI is a retrieval-grounded assistant for chat, coding, documents, images, and user-provided knowledge. Anonymous sessions work immediately; authentication can be added later by migrating `session_id` ownership to a user record.

## Architecture

- `frontend/`: Next.js App Router UI, deployable to Vercel.
- `backend/`: FastAPI orchestration, provider abstraction, validation, PDF extraction, and session APIs.
- `supabase/migrations/`: PostgreSQL, pgvector, RLS, and vector search function.

The backend calls an OpenAI-compatible provider through `AI_BASE_URL`. Secrets stay server-side. Supabase persistence is enabled when `SUPABASE_URL` and a server key are configured; endpoints return clear configuration errors otherwise.

## Local setup

1. Copy `.env.example` to `.env` and configure Supabase and an AI provider.
2. Create a Supabase project, enable the `vector` extension, create private buckets named `decan-documents` and `decan-images`, then run `supabase/migrations/001_initial.sql`.
3. Backend (PowerShell): `cd backend; py -3.11 -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -r requirements.txt; uvicorn app.main:app --reload --port 8000`
4. Frontend: `cd frontend; npm install; npm run dev`
5. Open http://localhost:3000. API docs are at http://localhost:8000/docs.

For Linux/macOS, use `python3.11 -m venv .venv`, `source .venv/bin/activate`, and the same pip/uvicorn commands.

## Deployment

Deploy `frontend` to Vercel with `NEXT_PUBLIC_API_URL` pointing at a separately deployed Python service. Deploy `backend` to a Python-compatible service and set every server-side variable from `.env.example`. Never expose `SUPABASE_SERVICE_ROLE_KEY` or `AI_API_KEY` as `NEXT_PUBLIC_*` variables.

## Scope and safeguards

Text knowledge, PDF extraction, vector retrieval, image validation, anonymous sessions, chat persistence, and coding mode are implemented as real boundaries. OCR and image generation are intentionally not claimed. Uploads are treated as untrusted content and never executed. Rate limits and storage policies should be backed by a distributed counter before high-volume production launch.

## Checks

- Backend: `cd backend; pytest`
- Frontend: `cd frontend; npm run build`
