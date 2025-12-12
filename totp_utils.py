# totp_utils.py
import binascii
import base64
import pyotp

def _hex_to_base32(hex_seed: str) -> str:
    """
    Convert a 64-char hex string to a base32 string without padding.
    Raises ValueError on invalid hex or wrong length.
    """
    if not isinstance(hex_seed, str):
        raise ValueError("hex_seed must be a string")
    hex_seed = hex_seed.strip()
    if len(hex_seed) != 64:
        raise ValueError("hex_seed must be 64 hex characters")

    try:
        seed_bytes = binascii.unhexlify(hex_seed)
    except (binascii.Error, TypeError) as e:
        raise ValueError("hex_seed is not valid hex") from e

    # base32 encode and remove padding
    b32 = base64.b32encode(seed_bytes).decode("utf-8").strip("=")
    return b32

def generate_totp_code(hex_seed: str) -> str:
    """
    Generate current 6-digit TOTP code from a 64-character hex seed.
    Uses SHA-1, 30-second period, 6 digits (pyotp defaults).
    Returns the code as a zero-padded string.
    """
    b32 = _hex_to_base32(hex_seed)
    totp = pyotp.TOTP(b32, digits=6, interval=30)  # default digest=SHA1
    return totp.now()

def verify_totp_code(hex_seed: str, code: str, valid_window: int = 1) -> bool:
    """
    Verify the provided 6-digit TOTP code with ±valid_window tolerance.
    Returns True if valid, False otherwise.
    """
    if not isinstance(code, str):
        code = str(code)
    b32 = _hex_to_base32(hex_seed)
    totp = pyotp.TOTP(b32, digits=6, interval=30)
    try:
        return bool(totp.verify(code, valid_window=valid_window))
    except Exception:
        return False
