# AI-Speaking-coach
vibe coding搭建的AI英语陪练
# SpeakCoach

Skeleton project for an AI English speaking practice demo.

## Structure

- `backend/`: FastAPI app and shared types
- `frontend/`: Vue 3 app and placeholder modules
- `ai-coding/`: planning and design documents

## Quick Start

### Backend

```powershell
cd backend
uv pip install -e .
Copy-Item ../.env.example .env
uvicorn app.main:app --reload --port 8000
```

### Frontend

```powershell
cd frontend
pnpm install
pnpm dev
```

