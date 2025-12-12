# crypto_utils.py
import base64
import binascii
import re
import os
import pathlib
from typing import Any
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend

# Regex to validate exactly 64 hex chars (0-9, a-f, A-F)
HEX64_RE = re.compile(r'^[0-9a-fA-F]{64}$')

def decrypt_seed(encrypted_seed_b64: str, private_key: Any) -> str:
    """
    Decrypt base64-encoded encrypted seed using RSA/OAEP (SHA-256 + MGF1(SHA-256)).

    Args:
        encrypted_seed_b64: Base64-encoded ciphertext (string)
        private_key: RSA private key object from cryptography

    Returns:
        Decrypted hex seed as a lowercase 64-character hex string.

    Raises:
        ValueError on invalid input, decryption failure, or invalid seed format.
    """
    # 1) validate input type
    if not isinstance(encrypted_seed_b64, str) or not encrypted_seed_b64.strip():
        raise ValueError("encrypted_seed_b64 must be a non-empty string")

    # 2) base64 decode
    try:
        ciphertext = base64.b64decode(encrypted_seed_b64, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError("Invalid base64 for encrypted_seed") from exc

    # 3) RSA/OAEP decrypt (OAEP with MGF1(SHA-256), SHA-256, label=None)
    try:
        plaintext_bytes = private_key.decrypt(
            ciphertext,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
    except Exception as exc:
        # Do not leak crypto internals to callers — raise generic error
        raise ValueError("Decryption failed") from exc

    # 4) decode to UTF-8 and strip whitespace
    try:
        seed_str = plaintext_bytes.decode("utf-8").strip()
    except Exception as exc:
        raise ValueError("Decrypted seed is not valid UTF-8") from exc

    # 5) validate: must be exactly 64 hex chars
    if not HEX64_RE.fullmatch(seed_str):
        raise ValueError("Decrypted seed is not a 64-character hex string")

    # Normalize to lowercase for consistency
    return seed_str.lower()


def save_seed_to_disk(hex_seed: str, data_dir: str = "/data", filename: str = "seed.txt") -> str:
    """
    Atomically save a validated 64-char hex seed to data_dir/seed.txt (LF newline).
    Attempts to set file permission 0o600. Returns the full path saved.
    Raises ValueError if input is invalid.
    """
    if not isinstance(hex_seed, str) or not HEX64_RE.fullmatch(hex_seed):
        raise ValueError("hex_seed must be a 64-character hex string")

    data_path = pathlib.Path(data_dir)
    data_path.mkdir(parents=True, exist_ok=True)

    file_path = data_path / filename
    tmp_path = data_path / (filename + ".tmp")

    # Write to a temp file then atomically replace
    with tmp_path.open("w", newline="\n") as f:
        f.write(hex_seed + "\n")
        f.flush()
        try:
            os.fsync(f.fileno())
        except Exception:
            # best-effort; some platforms may deny fsync
            pass

    tmp_path.replace(file_path)

    # Best-effort secure permissions (owner read/write)
    try:
        os.chmod(file_path, 0o600)
    except Exception:
        pass

    return str(file_path)
