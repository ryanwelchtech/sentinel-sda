
## `docs/interfaces/events.md`

```md
# Event and Data Flow

## High-level flow
1) `sensor-sim-*` produces observations
2) `ingestion-gateway` receives `POST /observations`
3) `validation-service` validates schema/integrity
4) `fusion-engine` fuses observations into tracks
5) `track-api` serves tracks via `GET /tracks`

## Contracts
- Observation payload: `observation.schema.json`
- Track payload: `track.schema.json`

## Notes
- JWT is validated at the edge (ingestion + track API) and may also be used internally depending on implementation.
- Redis is used for shared state / buffering (implementation-dependent).
