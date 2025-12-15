# System Architecture

## Architectural Overview
SENTINEL-SDA is implemented as a set of loosely coupled microservices deployed on Kubernetes. Each service has a clearly defined responsibility and communicates over authenticated APIs.

## Major Components
- Sensor Simulators
- Ingestion Gateway
- Validation Service
- Fusion Engine
- Track Store
- Track Query API
- Mission Optimizer
- Tasking Service
- Observability Stack

## Data Flow
1. Sensor simulators emit observation events
2. Ingestion Gateway receives and forwards events
3. Validation Service enforces schema and sanity checks
4. Fusion Engine updates object tracks
5. Tracks are persisted and exposed via API
6. Mission Optimizer evaluates priorities
7. Tasking Service issues sensor directives

## Design Principles
- Separation of concerns
- Fail-fast validation
- Graceful degradation
- Automation-first operations
- Security as an architectural constraint
