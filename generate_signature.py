#!/usr/bin/env python3
"""
Generate a signed-and-encrypted proof of work for submission.

Outputs:
 - Commit Hash (printed)
 - encrypted_signature.b64 (file, single-line base64)
 - Also prints the base64 on stdout

Requirements:
 - cryptography
"""

import subprocess
import re
import base64
import sys
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.backends import default_backend
from pathlib import Path

# --- Configurable filenames (relative to repo root) ---
STUDENT_PRIVATE_PEM = "student_private.pem"
INSTRUCTOR_PUBLIC_PEM = "instructor_public.pem"
OUTPUT_FILE = "encrypted_signature.b64"

HEX40_RE = re.compile(r'^[0-9a-fA-F]{40}$')

def get_latest_commit_hash() -> str:
    out = subprocess.check_output(["git", "log", "-1", "--format=%H"], stderr=subprocess.DEVNULL)
    s = out.decode("utf-8").strip()
    if not HEX40_RE.fullmatch(s):
        raise ValueError("Commit hash is not a 40-character hex string: {!r}".format(s))
    return s

def load_private_key(path: str):
    data = Path(path).read_bytes()
    return serialization.load_pem_private_key(data, password=None, backend=default_backend())

def load_public_key(path: str):
    data = Path(path).read_bytes()
    return serialization.load_pem_public_key(data, backend=default_backend())

def sign_message(message: str, private_key: rsa.RSAPrivateKey) -> bytes:
    """
    Sign ASCII message using RSA-PSS with SHA-256, MGF1(SHA-256), salt_length=MAX.
    Returns raw signature bytes.
    """
    msg_bytes = message.encode("utf-8")  # sign ASCII/UTF-8 bytes of commit hash
    signature = private_key.sign(
        msg_bytes,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    return signature

def encrypt_with_public_key(data: bytes, public_key: rsa.RSAPublicKey) -> bytes:
    """
    Encrypt data using RSA-OAEP with SHA-256 and MGF1(SHA-256).
    Returns ciphertext bytes.
    """
    ciphertext = public_key.encrypt(
        data,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return ciphertext

def main():
    # 1. commit hash
    commit_hash = get_latest_commit_hash()
    print("Commit Hash:", commit_hash)

    # 2. load student private key
    if not Path(STUDENT_PRIVATE_PEM).exists():
        print(f"Error: {STUDENT_PRIVATE_PEM} not found", file=sys.stderr)
        sys.exit(2)
    priv = load_private_key(STUDENT_PRIVATE_PEM)

    # 3. sign commit hash
    sig = sign_message(commit_hash, priv)

    # 4. load instructor public key
    if not Path(INSTRUCTOR_PUBLIC_PEM).exists():
        print(f"Error: {INSTRUCTOR_PUBLIC_PEM} not found", file=sys.stderr)
        sys.exit(2)
    instr_pub = load_public_key(INSTRUCTOR_PUBLIC_PEM)

    # 5. encrypt signature with instructor public key
    ciphertext = encrypt_with_public_key(sig, instr_pub)

    # 6. base64 encode (single-line)
    b64 = base64.b64encode(ciphertext).decode("ascii")

    # Write file (single-line)
    Path(OUTPUT_FILE).write_text(b64, encoding="utf-8")

    # Print result
    print("Encrypted Signature (base64) written to:", OUTPUT_FILE)
    print("Encrypted Signature (base64):")
    print(b64)  # single-line

if __name__ == "__main__":
    main()
