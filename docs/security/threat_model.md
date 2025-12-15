# Threat Model

## Assets
- Observation data
- Track data
- Mission tasking decisions
- System availability

## Threat Actors
- Untrusted sensor sources
- Malicious data injection
- Insider misconfiguration

## Threats
- Data tampering
- Replay attacks
- Denial of service
- Unauthorized service access

## Mitigations
- Schema validation and sanity checks
- Authentication between services
- Rate limiting and resource quotas
- Audit logging of decisions

## Trust Boundaries
- Sensor simulators are untrusted
- All internal services require authentication
