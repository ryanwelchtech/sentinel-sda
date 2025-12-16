# SENTINEL-SDA
Sensor Fusion & Resilience Simulator for Space Domain Awareness

## Overview
SENTINEL-SDA is a Kubernetes-deployed systems engineering project that simulates a Space Domain Awareness (SDA) mission. The system ingests observations from multiple simulated sensors, validates and fuses those observations into tracks, dynamically optimizes sensor tasking, and maintains mission capability under degraded conditions.

This project is designed to demonstrate systems engineering principles, mission-driven architecture, security-by-design, and resilience engineering using modern cloud-native tooling.

## Mission Objectives
- Maintain continuous awareness of simulated space objects
- Fuse multi-source sensor data into reliable tracks
- Optimize sensor tasking based on mission priorities
- Continue operating under sensor failure, latency, or data integrity issues

## Key Capabilities
- Multi-sensor observation ingestion (radar, optical, space-based)
- Schema validation and data integrity checks
- Track fusion with confidence scoring
- Mission-aware sensor tasking optimization
- Fault injection and graceful degradation
- Full observability with metrics and dashboards

## Technology Stack
- Kubernetes (OpenShift-compatible)
- Python microservices
- Docker containers
- GitOps-compatible manifests
- Prometheus and Grafana
- Zero Trust service-to-service communication (JWT-based initially)

## Repository Structure
```text
sentinel-sda/
├── docs/
├── services/
├── infrastructure/
├── ci/
└── scripts/
```


## How This Maps to Systems Engineering
This project intentionally includes:
- Formal requirements
- System architecture documentation
- Trade-off analysis
- Verification and validation planning
- Risk management artifacts

These mirror artifacts used on defense and aerospace programs.

## Disclaimer
This is a simulation and educational project. No real satellite or classified systems are involved.
