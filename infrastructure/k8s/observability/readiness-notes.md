# Readiness and Health

All services expose:
- `/health` endpoint
- Kubernetes readiness via HTTP 200

Health semantics:
- `ingestion-gateway`: ready when JWT + downstream reachable
- `fusion-engine`: ready when Redis connectivity is established
- `track-api`: ready when track store is accessible

This enables:
- Rolling updates
- Zero-downtime restarts
- Predictable failure behavior
