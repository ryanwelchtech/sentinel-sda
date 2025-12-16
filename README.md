# SENTINEL-SDA
Sensor Fusion & Resilience Simulator for Space Domain Awareness

## Overview
SENTINEL-SDA is a Kubernetes-deployed systems engineering project that simulates a Space Domain Awareness (SDA) mission environment. The system ingests observations from multiple simulated sensors, validates and fuses those observations into object tracks, and provides mission-level planning and sensor tasking recommendations while maintaining capability under degraded conditions.

The project is designed to demonstrate applied systems engineering principles, mission-driven architecture, security-by-design, and resilience engineering using modern cloud-native tooling.

## Mission Objectives
- Maintain continuous awareness of simulated space objects
- Fuse multi-source sensor data into reliable tracks
- Optimize sensor tasking based on mission priorities
- Continue operating under sensor failure, latency, or data integrity issues

## Key Capabilities
- Multi-sensor observation ingestion (radar, optical, space-based)
- Schema validation and data integrity enforcement
- Track fusion with confidence scoring and state propagation
- Mission-aware sensor tasking and planning recommendations
- Fault injection with graceful degradation and recovery
- Full observability with metrics, health checks, and dashboards
- Hybrid agentic mission planning with policy-based constraints and explainable rationale

## Technology Stack
- Kubernetes (OpenShift-compatible)
- Python-based microservices
- Docker containerization
- GitOps-compatible Kubernetes manifests
- Prometheus and Grafana for observability
- Zero Trust service-to-service communication (JWT-based, policy-enforced)

## Repository Structure
```text
sentinel-sda/
├── docs/                  # System architecture, requirements, V&V, risks, runbooks
├── services/              # Microservices (ingestion, fusion, planning, agents)
├── k8s/                   # Kubernetes manifests (base + overlays)
├── config/                # Mission and planning policies
├── infrastructure/        # Terraform and infrastructure scaffolding
├── .github/workflows/     # CI/CD pipelines
└── scripts/               # Demo, load, chaos, and utility scripts
```

## Agentic Mission Planning (Hybrid Decision Support)

SENTINEL-SDA includes a Mission Planning Agent that provides human-in-the-loop decision support for space domain awareness operations. The agent analyzes object tracks, sensor availability, and operator intent to generate ranked tasking recommendations.

The planning capability uses a hybrid approach:
- Deterministic, policy-driven rules enforce mission constraints and scoring
- An optional explainable AI layer provides rationale and trade-off explanations
- The agent does not execute actions autonomously and operates within defined trust boundaries

This design supports auditable, repeatable, and mission-safe decision making aligned with defense and aerospace systems engineering practices.

## Systems Engineering Alignment
This project intentionally includes:
- Formal requirements
- System and subsystem architecture documentation
- Trade-off and design analysis
- Verification and validation planning
- Risk identification and mitigation

These mirror artifacts used on defense and aerospace programs.

## Disclaimer
This is a simulation and educational project. No real satellite systems, operational data, or classified information are involved.
