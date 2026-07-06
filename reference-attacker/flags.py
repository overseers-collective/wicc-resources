import base64
import re
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.hazmat.primitives.serialization import load_pem_public_key

PREFIX = "WICC{"
SUFFIX = "}"
PAYLOAD_SIZE = 4 + 64
BODY_LEN = (PAYLOAD_SIZE * 4 + 2) // 3
FLAG_LEN = len(PREFIX) + BODY_LEN + 1
FLAG_RE = re.compile(r"WICC\{[A-Za-z0-9_-]{%d}\}" % BODY_LEN)


def _decode_flag(flag: str) -> bytes:
    if len(flag) != FLAG_LEN:
        raise ValueError(f"wrong length {len(flag)}, expected {FLAG_LEN}")
    if not flag.startswith(PREFIX) or not flag.endswith(SUFFIX):
        raise ValueError("missing WICC{...} wrapper")

    body = flag[len(PREFIX) : -1]
    if len(body) != BODY_LEN:
        raise ValueError(f"body length {len(body)}, expected {BODY_LEN}")

    # re-pad for the stdlib decoder
    padded = body + "=" * (-len(body) % 4)
    try:
        payload = base64.urlsafe_b64decode(padded)
    except ValueError as e:
        raise ValueError(f"invalid base64 body: {e}")

    if len(payload) != PAYLOAD_SIZE:
        raise ValueError(f"payload size {len(payload)}, expected {PAYLOAD_SIZE}")

    return payload


def _parse_payload(payload: bytes):
    header, signature = payload[:4], payload[4:]
    round_ = int.from_bytes(header[0:2], "big")
    service_id = header[2]
    team_id = header[3]
    return round_, service_id, team_id, header, signature


def validate_flag(flag: str, pub: Ed25519PublicKey):
    payload = _decode_flag(flag)
    round_, service_id, team_id, header, signature = _parse_payload(payload)
    try:
        pub.verify(signature, header)
        ok = True
    except InvalidSignature:
        ok = False
    return ok, round_, service_id, team_id


def load_key(key: bytes) -> Ed25519PublicKey:
    return load_pem_public_key(key)
