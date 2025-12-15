# Sentinel SDA – Demo Runbook (Local Kubernetes)

This runbook demonstrates end-to-end functionality, performance under load, and resiliency under failure for the Sentinel SDA microservices system.

**Environment**
- Platform: Docker Desktop Kubernetes (kubeadm)
- OS: Windows (PowerShell)
- Namespace: `sentinel-sda`

---

## 0. Prerequisites

### Required tools
- kubectl
- Python 3.10+
- curl.exe (Windows built-in)

### Python dependency
```powershell
python -m pip install pyjwt
```

### JWT secret

The Kubernetes secret secret-jwt.yaml uses:

```
replace-with-a-strong-demo-secret
```

You must set this in every PowerShell terminal where you generate a token:

```powershell
$env:JWT_SECRET = "replace-with-a-strong-demo-secret"
```

1. Scenario S0 – Baseline Health Check
#### Goal

Verify the cluster and all services are healthy.

#### Commands
```powershell
kubectl -n sentinel-sda get pods
kubectl -n sentinel-sda get svc
kubectl -n sentinel-sda get deploy
```

#### Expected Result

- All pods show `Running` and `READY 1/1`
- Services exist for ingestion and track API

2. Scenario S1 – Normal Operations (Track Query)
#### Goal

Verify the system can return tracks during normal operation.

#### Terminal A – Port-forward Track API
```powershell
kubectl -n sentinel-sda port-forward svc/track-api 8000:8000
```

#### Terminal B – Generate JWT
```powershell
$env:JWT_SECRET="replace-with-a-strong-demo-secret"
$token = (python scripts/make_token.py --secret $env:JWT_SECRET).Trim()
$token.Split(".").Count
```


Expected output:
```
3
```

#### Query tracks
```powershell
curl.exe -s -H "Authorization: Bearer $token" "http://localhost:8000/tracks?limit=10"
```

3. Scenario S2 – Manual Observation Injection (End-to-End Proof)
#### Goal

Inject a known observation and confirm it becomes a track.

#### Terminal A – Port-forward Ingestion Gateway
```powershell
kubectl -n sentinel-sda port-forward svc/ingestion-gateway 8001:8000
```

#### Create sample observation payload
```powershell
@'
{
  "event_id": "evt-manual-1",
  "sensor_id": "manual-1",
  "sensor_type": "radar",
  "timestamp": "2025-12-15T00:00:00Z",
  "object_id": "obj-999",
  "measurement": {
    "x_km": 1000,
    "y_km": 2000,
    "z_km": 3000,
    "vx_kms": 0.1,
    "vy_kms": 0.2,
    "vz_kms": 0.3
  },
  "quality": {
    "snr_db": 12,
    "measurement_sigma": 0.3
  },
  "integrity": {
    "signed": true,
    "signature": "demo"
  }
}
'@ | Out-File -Encoding ascii .\scripts\sample_observation.json
```

#### POST the observation
```powershell
curl.exe -s -X POST "http://localhost:8001/observations" `
  -H "Authorization: Bearer $token" `
  -H "Content-Type: application/json" `
  --data-binary "@scripts/sample_observation.json"
```

#### Confirm the track exists
```
curl.exe -s -H "Authorization: Bearer $token" "http://localhost:8000/tracks?limit=25"
```

Expected: object `obj-999` appears.

4. Scenario S3 – Load Test (Burst Traffic)
#### Goal

Demonstrate system stability under burst ingestion.

#### Generate load
```powershell
1..200 | ForEach-Object {
  $body = @{
    event_id="evt-burst-$_"
    sensor_id="burst-1"
    sensor_type="radar"
    timestamp=(Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    object_id=("obj-burst-" + (($_ % 25) + 1))
    measurement=@{x_km=1000; y_km=2000; z_km=3000; vx_kms=0.1; vy_kms=0.2; vz_kms=0.3}
    quality=@{snr_db=12; measurement_sigma=0.3}
    integrity=@{signed=$true; signature="demo"}
  } | ConvertTo-Json -Depth 10 -Compress

  curl.exe -s -X POST "http://localhost:8001/observations" `
    -H "Authorization: Bearer $token" `
    -H "Content-Type: application/json" `
    -d "$body" | Out-Null
}
```

#### Verify responsiveness
```powershell
curl.exe -s -H "Authorization: Bearer $token" "http://localhost:8000/tracks?limit=10"
```

5. Scenario S4 – Sensor Outage (Graceful Degradation)
#### Disable optical sensor
```powershell
kubectl -n sentinel-sda scale deploy/sensor-sim-optical --replicas=0
```

#### Restore
```powershell
kubectl -n sentinel-sda scale deploy/sensor-sim-optical --replicas=1
kubectl -n sentinel-sda rollout status deploy/sensor-sim-optical --timeout=180s
```

6. Scenario S5 – Validation Service Failure
#### Disable validation
```powershell
kubectl -n sentinel-sda scale deploy/validation-service --replicas=0
```

#### Restore
```powershell
kubectl -n sentinel-sda scale deploy/validation-service --replicas=1
kubectl -n sentinel-sda rollout status deploy/validation-service --timeout=180s
```

7. Scenario S6 – Fusion Engine Restart
```powershell
kubectl -n sentinel-sda delete pod -l app=fusion-engine
kubectl -n sentinel-sda rollout status deploy/fusion-engine --timeout=180s
```

8. Troubleshooting
```powershell
kubectl -n sentinel-sda get events --sort-by=.lastTimestamp | Select-Object -Last 40
```

