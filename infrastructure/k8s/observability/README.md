# Observability

This folder defines observability hooks and intent for the Sentinel SDA system.

The current implementation is intentionally lightweight to support:
- Local Kubernetes (Docker Desktop)
- OpenShift compatibility
- Future integration with Prometheus, Grafana, or vendor APM tools

## Design Goals
- Zero impact on application logic
- Standards-based metrics exposure
- Declarative observability configuration

## Current Scope
- Metrics annotations on services
- Logging via stdout/stderr
- Kubernetes-native health signals

## Future Enhancements
- Prometheus Operator
- ServiceMonitors
- Grafana dashboards
- Distributed tracing (OpenTelemetry)
