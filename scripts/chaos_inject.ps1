param(
  [Parameter(Mandatory=$true)]
  [ValidateSet("kill-optical","kill-validation","restore-all","status")]
  [string]$Action,
  [string]$Namespace = "sentinel-sda"
)

$ErrorActionPreference = "Stop"

switch ($Action) {
  "kill-optical" {
    Write-Host "Scaling sensor-sim-optical to 0..."
    kubectl -n $Namespace scale deploy/sensor-sim-optical --replicas=0
  }
  "kill-validation" {
    Write-Host "Scaling validation-service to 0..."
    kubectl -n $Namespace scale deploy/validation-service --replicas=0
  }
  "restore-all" {
    Write-Host "Restoring deployments to 1 replica..."
    kubectl -n $Namespace scale deploy/sensor-sim-optical --replicas=1
    kubectl -n $Namespace scale deploy/validation-service --replicas=1
  }
  "status" {
    kubectl -n $Namespace get deploy | Out-Host
    kubectl -n $Namespace get pods -o wide | Out-Host
  }
}

Write-Host ""
kubectl -n $Namespace get pods -o wide | Out-Host
