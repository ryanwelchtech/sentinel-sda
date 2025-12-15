#!/usr/bin/env python3
"""
Create a valid HS256 JWT for SENTINEL-SDA services.

Usage:
  python3 scripts/make_token.py --secret changeme
  python3 scripts/make_token.py --secret changeme --svc track-api
  python3 scripts/make_token.py --secret changeme --issuer sentinel-sda --svc "demo-client"

Output:
  Prints a JWT to stdout (no extra text).
"""

import argparse
import time

import jwt  # PyJWT


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--secret", required=True, help="HS256 shared secret (must match JWT_SECRET env)")
    p.add_argument("--issuer", default="sentinel-sda", help="JWT issuer (default: sentinel-sda)")
    p.add_argument("--svc", default="demo-client", help="Service identity claim (default: demo-client)")
    p.add_argument("--ttl", type=int, default=3600, help="Token TTL in seconds (default: 3600)")
    args = p.parse_args()

    now = int(time.time())
    payload = {
        "svc": args.svc,
        "iss": args.issuer,
        "iat": now,
        "exp": now + args.ttl,
    }

    token = jwt.encode(payload, args.secret, algorithm="HS256")
    print(token)


if __name__ == "__main__":
    main()
