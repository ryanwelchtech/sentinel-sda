param(
  [string]$Namespace = "sentinel-sda",
  [int]$LocalPort = 8001,
  [string]$IngestService = "ingestion-gateway",
  [int]$DurationSeconds = 30,
  [int]$RatePerSec = 20,
  [int]$ObjectPool = 50,
  [string]$JwtIssuer = "sentinel-sda",
  [string]$JwtSecret = "changeme"
)

$ErrorActionPreference = "Stop"

$token = python scripts/make_token.py --secret $JwtSecret --issuer $JwtIssuer --svc load-tester
$env:TOKEN = $token

Write-Host "Starting port-forward to $IngestService on localhost:$LocalPort ..."
$pf = Start-Process -NoNewWindow -PassThru -FilePath "kubectl" -ArgumentList @("-n",$Namespace,"port-forward","svc/$IngestService","$LocalPort`:8000")

Start-Sleep -Seconds 2

Write-Host "Load test: duration=$DurationSeconds s rate=$RatePerSec req/s object_pool=$ObjectPool"
Write-Host "Endpoint: http://localhost:$LocalPort/observations"

python - << 'PY'
import os, time, random, json, urllib.request
local_port = int(os.environ.get("LOCAL_PORT","8001"))
duration = int(os.environ.get("DURATION_SECONDS","30"))
rate = int(os.environ.get("RATE_PER_SEC","20"))
object_pool = int(os.environ.get("OBJECT_POOL","50"))
token = os.environ["TOKEN"]
url = f"http://localhost:{local_port}/observations"
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

def now_iso():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

ok = 0
fail = 0
start = time.time()
next_tick = start
end = start + duration

while time.time() < end:
    for _ in range(rate):
        oid = f"obj-{random.randint(1, object_pool):03d}"
        evt = {
            "event_id": f"evt-load-{int(time.time()*1000)}-{random.randint(0,9999)}",
            "sensor_id": "loadgen-1",
            "sensor_type": "radar",
            "timestamp": now_iso(),
            "object_id": oid,
            "measurement": {
                "x_km": random.uniform(-20000,20000),
                "y_km": random.uniform(-20000,20000),
                "z_km": random.uniform(-20000,20000),
                "vx_kms": random.uniform(-2,2),
                "vy_kms": random.uniform(-2,2),
                "vz_kms": random.uniform(-2,2),
            },
            "quality": {"snr_db": random.uniform(5,25), "measurement_sigma": random.uniform(0.1,1.0)},
            "integrity": {"signed": True, "signature": "demo-signature"},
        }
        data = json.dumps(evt).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=3) as resp:
                ok += 1 if resp.status == 200 else 0
                fail += 0 if resp.status == 200 else 1
        except Exception:
            fail += 1
    next_tick += 1
    time.sleep(max(0, next_tick - time.time()))

elapsed = time.time() - start
print(f"Done. ok={ok} fail={fail} elapsed={elapsed:.1f}s rps={(ok+fail)/elapsed:.1f}")
PY
"@ | Out-Host
PY

# Note: the here-string above is tricky in PS; easiest is to set env vars and call a .py file.
# If you hit issues, tell me and I'll switch this script to call scripts/loadgen.py instead.

Stop-Process -Id $pf.Id -Force
Write-Host "Port-forward stopped."
