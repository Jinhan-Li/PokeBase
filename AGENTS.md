# Repository Guidelines

## Project Structure & Module Organization

This repository is a Pokemon knowledge graph Q&A system. The FastAPI backend lives in `backend/`, with API routers in `backend/routers/`, Pydantic models in `backend/models/`, service logic in `backend/services/`, and Cypher import scripts in `backend/data/cypher/`. The Vue 3 frontend lives in `frontend/`, with the main UI in `frontend/src/App.vue` and Axios helpers in `frontend/src/api/`. Data ingestion code is in `data_pipeline/`, ontology assets are in `ontology/`, exported Neo4j data is in `neo4j_export/`, and manual test scenarios are in `tests/test_cases.md`.

## Build, Test, and Development Commands

- `cd backend && pip install -r requirements.txt`: install backend dependencies.
- `cd backend && python check_env.py`: verify required environment variables and connectivity settings.
- `cd backend && python -m uvicorn main:app --reload --port 8000`: run the API locally.
- `cd frontend && npm install`: install frontend dependencies.
- `cd frontend && npm run dev`: start the Vite dev server at `http://localhost:5173`.
- `cd frontend && npm run build`: create a production frontend build.
- `cd data_pipeline && python run_pipeline.py 10`: fetch, transform, and load a small test data set.

## Coding Style & Naming Conventions

Use Python 3.12-compatible code for backend and pipeline modules. Follow PEP 8 naming: `snake_case` for functions, modules, and variables; `PascalCase` for Pydantic classes. Keep FastAPI route handlers thin and put reusable behavior in `backend/services/`. Frontend code uses Vue 3 single-file components and ES modules; name components with `PascalCase` and keep API calls in `frontend/src/api/`.

## Testing Guidelines

The current test suite is documented manually in `tests/test_cases.md`. Validate backend changes through the relevant API endpoints, especially `GET /api/health`, `POST /api/query`, `POST /api/chat`, and `GET /api/schema`. For data changes, rerun a small pipeline import first, then verify representative questions from the test cases before scaling the data set.

## Commit & Pull Request Guidelines

Git history was unavailable during this guide update because the repository is blocked by Git safe-directory ownership checks. Use concise, imperative commit subjects such as `Add chat schema endpoint` or `Fix Neo4j import mapping`. Pull requests should include a short description, affected areas (`backend`, `frontend`, `data_pipeline`, `ontology`), setup or migration notes, and screenshots for visible UI changes.

## Security & Configuration Tips

Copy `.env.example` to `.env` and keep credentials out of version control. Required secrets include Neo4j credentials and the DashScope API key. Do not hard-code connection strings, passwords, or model keys in source files; use `backend/config.py` and environment variables instead.
