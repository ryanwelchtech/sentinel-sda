# Sentinel SDA API (Local)

Base URLs (via port-forward):
- Ingestion Gateway: `http://localhost:8001`
- Track API: `http://localhost:8000`

All endpoints require:
- Header: `Authorization: Bearer <JWT>`
- Content-Type: `application/json` for POST

## Ingestion Gateway

### POST /observations
Ingest a sensor observation event.

- Request body: `observation.schema.json`
- Response: 200 OK on accept, otherwise 4xx/5xx with JSON error body.

Example:
- `scripts/sample_observation.json`

## Track API

### GET /tracks?limit=<n>
Returns recent tracks.

- Query params:
  - `limit` (optional): integer
- Response:
  - JSON list of track objects (see `track.schema.json`)

Example:
```powershell
curl.exe -s -H "Authorization: Bearer $token" "http://localhost:8000/tracks?limit=10"
```