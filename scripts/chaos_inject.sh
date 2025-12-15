#!/usr/bin/env bash
set -euo pipefail

NAMESPACE="${NAMESPACE:-sentinel-sda}"
ACTION="${1:-}"

usage() {
  echo "Usage: scripts/chaos_inject.sh <action>"
  echo
  echo "Actions:"
  echo "  kill-optical     Scale optical sensor simulator to 0 (sensor outage)"
  echo "  kill-validation  Scale validation-service to 0 (pipeline outage)"
  echo "  restore-all      Restore scaled components back to 1 replica"
  echo "  status           Show pod/deploy status"
  exit 1
}

if [[ -z "${ACTION}" ]]; then
  usage
fi

case "${ACTION}" in
  kill-optical)
    echo "Scaling sensor-sim-optical to 0 in namespace ${NAMESPACE}"
    kubectl -n "${NAMESPACE}" scale deploy/sensor-sim-optical --replicas=0
    ;;
  kill-validation)
    echo "Scaling validation-service to 0 in namespace ${NAMESPACE}"
    kubectl -n "${NAMESPACE}" scale deploy/validation-service --replicas=0
    ;;
  restore-all)
    echo "Restoring deployments to 1 replica in namespace ${NAMESPACE}"
    kubectl -n "${NAMESPACE}" scale deploy/sensor-sim-optical --replicas=1
    kubectl -n "${NAMESPACE}" scale deploy/validation-service --replicas=1
    ;;
  status)
    echo "Deployments:"
    kubectl -n "${NAMESPACE}" get deploy
    echo
    echo "Pods:"
    kubectl -n "${NAMESPACE}" get pods -o wide
    ;;
  *)
    usage
    ;;
esac

echo
echo "Current status:"
kubectl -n "${NAMESPACE}" get pods -o wide
