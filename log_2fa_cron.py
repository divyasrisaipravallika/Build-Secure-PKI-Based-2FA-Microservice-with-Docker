#!/usr/bin/env python3

import os
import datetime
from totp_utils import generate_totp_code

SEED_PATH = "/data/seed.txt"
OUT_PATH = "/cron/last_code.txt"

def log_line(text: str):
    with open(OUT_PATH, "a") as f:
        f.write(text + "\n")

def main():
    try:
        # 1. Read seed
        if not os.path.exists(SEED_PATH):
            ts = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            log_line(f"{ts} - stderr: seed missing")
            return

        with open(SEED_PATH, "r") as f:
            hex_seed = f.read().strip()

        # 2. Generate TOTP
        code = generate_totp_code(hex_seed)

        # 3. Timestamp (UTC)
        ts = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

        # 4. Log
        log_line(f"{ts} - 2FA Code: {code}")

    except Exception as e:
        ts = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        log_line(f"{ts} - stderr: {str(e)}")

if __name__ == "__main__":
    main()
