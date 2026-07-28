from __future__ import annotations

import hashlib
import hmac


def sign_github_body(secret: str, body: bytes) -> str:
    digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def verify_github_signature(
    secret: str,
    body: bytes,
    signature_header: str | None,
) -> bool:
    if not secret or not signature_header:
        return False
    expected = sign_github_body(secret, body)
    return hmac.compare_digest(expected, signature_header)
