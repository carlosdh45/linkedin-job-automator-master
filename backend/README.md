# DobryBot — Backend API

FastAPI backend for DobryBot. Wraps the existing Python core and exposes it over HTTP. Human-in-the-loop rules are fully enforced — no send or apply path exists.

## Install

```bash
pip install -r requirements.txt
```

## Run

```bash
uvicorn backend.main:app --reload --port 8000
```

## Demo mode (no config.yaml needed)

```bash
# Seed safe demo data
python main.py --seed-demo-data

# Start the API
uvicorn backend.main:app --reload --port 8000

# Try it
curl http://localhost:8000/health
curl http://localhost:8000/api/stats
curl http://localhost:8000/api/daily-brief
curl http://localhost:8000/api/review-queue
```

Interactive Swagger docs: http://localhost:8000/docs

## Configuration

By default the API uses the same SQLite DB as the CLI: `data/copilot.db`.

Override via environment variable:

```bash
DOBRYBOT_DB_PATH=/path/to/my.db uvicorn backend.main:app --reload
```

Or add to `config.yaml`:

```yaml
paths:
  database: data/copilot.db
```

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | /health | Health check |
| GET | /api/stats | Database statistics |
| GET | /api/daily-brief | Daily opportunity summary (JSON) |
| GET | /api/jobs | All jobs — optional `?status=scored` |
| GET | /api/leads | All leads — optional `?status=scored` |
| GET | /api/review-queue | Drafts pending review |
| POST | /api/drafts/{id}/approve | Approve a draft (Quality Guard enforced) |
| POST | /api/drafts/{id}/skip | Skip a draft — optional body `{"reason": "..."}` |
| POST | /api/drafts/{id}/needs-research | Flag for research — optional body `{"note": "..."}` |
| POST | /api/demo/seed | Seed safe demo data (no external calls) |
| POST | /api/demo/clear | Remove all demo records (.test domains) |

## Safety rules

- No `/send` endpoint. No `/send-approved` endpoint. Emails are never sent by this API.
- No `/apply` endpoint. LinkedIn submission is permanently removed and will never be re-added.
- `POST /api/drafts/{id}/approve` enforces the Quality Guard — drafts with `quality_status` of `failed` or `pending` return HTTP 422. There is no force-approve parameter.
- `POST /api/demo/seed` and `POST /api/demo/clear` make zero external network calls.

## Tests

```bash
python -m pytest tests/test_api.py -v
```
