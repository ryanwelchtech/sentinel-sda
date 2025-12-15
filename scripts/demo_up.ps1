param(
  [string]$Namespace = "sentinel-sda",
  [string]$KustomizeDir = "infrastructure/k8s",
  [int]$LocalPort = 8000,
  [string]$TrackService = "track-api",
  [string]$JwtIssuer = "sentinel-sda",
  [string]$JwtSecret = "changeme"
)

$ErrorActionPreference = "Stop"

Write-Host "[1/5] Applying manifests from $KustomizeDir"
kubectl apply -k $KustomizeDir

Write-Host "[2/5] Waiting for deployments to become available..."
$deploys = @(
  "redis","ingestion-gateway","validation-service","fusion-engine",
  "tasking-service","mission-optimizer","track-api",
  "sensor-sim-radar","sensor-sim-optical","sensor-sim-space"
)

foreach ($d in $deploys) {
  try {
    kubectl -n $Namespace rollout status "deploy/$d" --timeout=180s | Out-Host
  } catch {
    Write-Host "Warning: rollout status failed for $d (may still be starting)"
  }
}

Write-Host "[3/5] Current pods:"
kubectl -n $Namespace get pods -o wide | Out-Host

Write-Host "[4/5] Creating JWT token and setting `$env:TOKEN"
$env:JWT_SECRET = $JwtSecret
$env:JWT_ISSUER = $JwtIssuer

$token = python scripts/make_token.py --secret $JwtSecret --issuer $JwtIssuer --svc demo-client
$env:TOKEN = $token

Write-Host ""
Write-Host "Token set in `$env:TOKEN"
Write-Host ""
Write-Host "Try in another PowerShell window:"
Write-Host "  curl http://localhost:$LocalPort/health"
Write-Host "  curl -H `"Authorization: Bearer $env:TOKEN`" `"http://localhost:$LocalPort/tracks?min_conf=0.0&limit=10`""
Write-Host ""
Write-Host "[5/5] Starting port-forward (Ctrl+C to stop)..."

kubectl -n $Namespace port-forward "svc/$TrackService" "$LocalPort`:8000"
