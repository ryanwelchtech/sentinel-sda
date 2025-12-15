# Local Overlay

This overlay configures Sentinel SDA to use locally-built container images.

## Use case
- Docker Desktop Kubernetes
- Rapid iteration
- No registry dependencies

## Build images locally
```powershell
docker build -t sentinel-sda-ingestion-gateway:local services/ingestion-gateway
```

(Repeat for other services.)

## Deploy using overlay
```powershell
kubectl apply -k k8s/overlays/local
```

## Production

Production clusters use the base manifests with GHCR images.