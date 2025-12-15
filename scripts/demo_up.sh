#!/usr/bin/env bash
set -euo pipefail

NAMESPACE="${NAMESPACE:-sentinel-sda}"
KUSTOMIZE_DIR="${KUSTOMIZE_DIR:-infrastructure/k8s}"
LOCAL_PORT="${LOCAL_PORT:-8000}"
SERVICE_PORT="${SERVICE_PORT:-8000}"
TRACK_SVC="${TRACK_SVC:-track-api}"

# Set JWT secret here or export JWT_SECRET before running.
JWT_SECRET="${JWT_SECRET:-changeme}"
JWT_ISSUER="${JWT_ISSUER:-sentinel-sda}"

echo "[1/6] Applying manifests from: ${KUSTOMIZE_DIR}"
kubectl apply -k "${KUSTOMIZE_DIR}"

echo "[2/6] Waiting for deployments to become available..."
kubectl -n "${NAMESPACE}" rollout status deploy/redis --timeout=120s || true
kubectl -n "${NAMESPACE}" rollout status deploy/ingestion-gateway --timeout=180s || true
kubectl -n "${NAMESPACE}" rollout status deploy/validation-service --timeout=180s || true
kubectl -n "${NAMESPACE}" rollout status deploy/fusion-engine --timeout=180s || true
kubectl -n "${NAMESPACE}" rollout status deploy/tasking-service --timeout=180s || true
kubectl -n "${NAMESPACE}" rollout status deploy/mission-optimizer --timeout=180s || true
kubectl -n "${NAMESPACE}" rollout status deploy/track-api --timeout=180s || true
kubectl -n "${NAMESPACE}" rollout status deploy/sensor-sim-radar --timeout=180s || true
kubectl -n "${NAMESPACE}" rollout status deploy/sensor-sim-optical --timeout=180s || true
kubectl -n "${NAMESPACE}" rollout status deploy/sensor-sim-space --timeout=180s || true

echo "[3/6] Current pods:"
kubectl -n "${NAMESPACE}" get pods -o wide

echo "[4/6] Starting port-forward to ${TRACK_SVC} on localhost:${LOCAL_PORT} ..."
echo "      Press Ctrl+C to stop port-forward."
echo

TOKEN="$(python3 scripts/make_token.py --secret "${JWT_SECRET}" --issuer "${JWT_ISSUER}" --svc demo-client)"
export TOKEN

echo "[5/6] Token created and exported as \$TOKEN."
echo
echo "Try these in another terminal:"
echo "  curl -s http://localhost:${LOCAL_PORT}/health | jq ."
echo "  curl -s -H \"Authorization: Bearer \$TOKEN\" \"http://localhost:${LOCAL_PORT}/tracks?min_conf=0.0&limit=10\" | jq ."
echo
echo "[6/6] Port-forward running now..."
kubectl -n "${NAMESPACE}" port-forward "svc/${TRACK_SVC}" "${LOCAL_PORT}:${SERVICE_PORT}"
