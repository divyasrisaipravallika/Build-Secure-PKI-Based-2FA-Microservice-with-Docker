# main.py
"""
PKI 2FA Auth Service - Full API (Step 7)
Endpoints:
  POST  /decrypt-seed   -> decrypts RSA/OAEP(base64) encrypted seed and stores it to /data/seed.txt
  GET   /generate-2fa   -> reads seed and returns current TOTP code + seconds remaining
  POST  /verify-2fa     -> verifies TOTP code with ±1 period tolerance

Behavior strictly follows the assignment's response shapes and status codes.
"""
import os
import time
import logging
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

# local helpers - must exist in repo root
from crypto_utils import decrypt_seed, save_seed_to_disk
from totp_utils import generate_totp_code, verify_totp_code

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pki-2fa")

# Configurable paths (use env vars in Docker)
STUDENT_PRIVATE_PATH = os.environ.get("STUDENT_PRIVATE", "./student_private.pem")
DATA_DIR = os.environ.get("DATA_DIR", "./data")
SEED_FILE_PATH = os.path.join(DATA_DIR, "seed.txt")

app = FastAPI(title="PKI 2FA Auth Service (Full)")

# ---------------------------
# Request models
# ---------------------------
class DecryptRequest(BaseModel):
    encrypted_seed: str


class VerifyRequest(BaseModel):
    code: Optional[str] = None


# ---------------------------
# Helpers
# ---------------------------
def load_private_key(path: str):
    """
    Load a PEM private key from disk using cryptography.
    Raises FileNotFoundError if missing.
    """
    with open(path, "rb") as f:
        return serialization.load_pem_private_key(f.read(), password=None, backend=default_backend())


def read_seed_file(path: str) -> str:
    """
    Read hex seed from disk and return stripped string.
    Raises FileNotFoundError if missing.
    """
    with open(path, "r") as f:
        return f.read().strip()


# ---------------------------
# Endpoint 1: POST /decrypt-seed
# ---------------------------
@app.post("/decrypt-seed")
def post_decrypt_seed(payload: DecryptRequest):
    """
    Request:
      { "encrypted_seed": "<base64 ciphertext>" }
    Response 200:
      { "status": "ok" }
    Response 500:
      { "error": "Decryption failed" }
    """
    # Load private key
    try:
        private_key = load_private_key(STUDENT_PRIVATE_PATH)
    except FileNotFoundError:
        logger.error("Private key not found at %s", STUDENT_PRIVATE_PATH)
        raise HTTPException(status_code=500, detail={"error": "Decryption failed"})
    except Exception:
        logger.exception("Failed to load private key")
        raise HTTPException(status_code=500, detail={"error": "Decryption failed"})

    # Decrypt + validate seed
    try:
        hex_seed = decrypt_seed(payload.encrypted_seed, private_key)
    except Exception:
        logger.exception("Seed decryption/validation failed")
        raise HTTPException(status_code=500, detail={"error": "Decryption failed"})

    # Persist to /data/seed.txt (atomic)
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        saved_path = save_seed_to_disk(hex_seed, data_dir=DATA_DIR)
        logger.info("Seed saved to %s", saved_path)
    except Exception:
        logger.exception("Failed to persist seed")
        raise HTTPException(status_code=500, detail={"error": "Decryption failed"})

    return {"status": "ok"}


# ---------------------------
# Endpoint 2: GET /generate-2fa
# ---------------------------
@app.get("/generate-2fa")
def get_generate_2fa():
    """
    Response 200:
      { "code": "123456", "valid_for": 30 }
    Response 500:
      { "error": "Seed not decrypted yet" }
    """
    # Check existence
    if not os.path.exists(SEED_FILE_PATH):
        raise HTTPException(status_code=500, detail={"error": "Seed not decrypted yet"})

    # Read seed
    try:
        hex_seed = read_seed_file(SEED_FILE_PATH)
    except Exception:
        logger.exception("Failed to read seed file")
        raise HTTPException(status_code=500, detail={"error": "Seed not decrypted yet"})

    # Generate code
    try:
        code = generate_totp_code(hex_seed)
    except Exception:
        logger.exception("TOTP generation failed")
        raise HTTPException(status_code=500, detail={"error": "Seed not decrypted yet"})

    # Calculate remaining seconds in current 30s window
    now = int(time.time())
    valid_for = 30 - (now % 30)
    return {"code": code, "valid_for": valid_for}


# ---------------------------
# Endpoint 3: POST /verify-2fa
# ---------------------------
@app.post("/verify-2fa")
def post_verify_2fa(payload: VerifyRequest):
    """
    Request: { "code": "123456" }
    Response 200: { "valid": true } or { "valid": false }
    Response 400: { "error": "Missing code" }
    Response 500: { "error": "Seed not decrypted yet" }
    """
    # Validate code provided
    if not payload.code:
        raise HTTPException(status_code=400, detail={"error": "Missing code"})

    # Check seed exists
    if not os.path.exists(SEED_FILE_PATH):
        raise HTTPException(status_code=500, detail={"error": "Seed not decrypted yet"})

    # Read seed
    try:
        hex_seed = read_seed_file(SEED_FILE_PATH)
    except Exception:
        logger.exception("Failed to read seed file")
        raise HTTPException(status_code=500, detail={"error": "Seed not decrypted yet"})

    # Verify with ±1 period
    try:
        is_valid = verify_totp_code(hex_seed, payload.code, valid_window=1)
    except Exception:
        logger.exception("Verification error")
        raise HTTPException(status_code=500, detail={"error": "Seed not decrypted yet"})

    return {"valid": bool(is_valid)}
