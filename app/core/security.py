import secrets
import base64
import hashlib
import hmac
import struct
from datetime import datetime, timedelta
from typing import Any, Optional, Union
from urllib.parse import quote

from jose import jwt, JWTError
from passlib.context import CryptContext

from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(
    subject: Union[str, Any], expires_delta: timedelta = None
) -> str:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(subject: Union[str, Any]) -> tuple[str, str]:
    """Create a refresh token. Returns (jwt_token, jti) where jti is the unique token ID."""
    jti = secrets.token_urlsafe(32)
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "purpose": "refresh",
        "jti": jti,
    }
    token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token, jti


def verify_refresh_token(token: str) -> Optional[dict]:
    """Verify a refresh token. Returns payload dict (sub, jti) if valid."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("purpose") != "refresh":
            return None
        return payload
    except JWTError:
        return None


def create_password_reset_token(email: str) -> str:
    """Create a short-lived JWT for password reset (30 min)."""
    expire = datetime.utcnow() + timedelta(minutes=30)
    to_encode = {"exp": expire, "sub": email, "purpose": "password_reset"}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def verify_password_reset_token(token: str) -> Optional[str]:
    """Verify a password reset token. Returns email if valid, None otherwise."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("purpose") != "password_reset":
            return None
        return payload.get("sub")
    except JWTError:
        return None


def create_invite_token(email: str, tenant_id: str, role: str = "employee") -> str:
    """Create a JWT for tenant invitation (7 days)."""
    expire = datetime.utcnow() + timedelta(days=7)
    to_encode = {
        "exp": expire,
        "sub": email,
        "tenant_id": tenant_id,
        "role": role,
        "purpose": "invitation",
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def verify_invite_token(token: str) -> Optional[dict]:
    """Verify an invitation token. Returns payload dict if valid."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("purpose") != "invitation":
            return None
        return payload
    except JWTError:
        return None


def create_email_verification_token(email: str) -> str:
    """Create a JWT for email verification (24 hours)."""
    expire = datetime.utcnow() + timedelta(hours=24)
    to_encode = {"exp": expire, "sub": email, "purpose": "email_verification"}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def verify_email_verification_token(token: str) -> Optional[str]:
    """Verify an email verification token. Returns email if valid, None otherwise."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("purpose") != "email_verification":
            return None
        return payload.get("sub")
    except JWTError:
        return None


def generate_totp_secret() -> str:
    return base64.b32encode(secrets.token_bytes(20)).decode("utf-8").rstrip("=")


def build_totp_uri(email: str, secret: str, issuer: Optional[str] = None) -> str:
    issuer_name = issuer or settings.MFA_ISSUER_NAME
    label = quote(f"{issuer_name}:{email}")
    return (
        f"otpauth://totp/{label}?secret={secret}"
        f"&issuer={quote(issuer_name)}&digits={settings.MFA_TOTP_DIGITS}"
        f"&period={settings.MFA_TOTP_INTERVAL_SECONDS}"
    )


def _decode_base32_secret(secret: str) -> bytes:
    padding = "=" * ((8 - len(secret) % 8) % 8)
    return base64.b32decode((secret + padding).upper(), casefold=True)


def _generate_totp(secret: str, for_time: Optional[int] = None) -> str:
    timestamp = int(for_time or datetime.utcnow().timestamp())
    counter = timestamp // settings.MFA_TOTP_INTERVAL_SECONDS
    key = _decode_base32_secret(secret)
    message = struct.pack(">Q", counter)
    digest = hmac.new(key, message, hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    code = struct.unpack(">I", digest[offset:offset + 4])[0] & 0x7FFFFFFF
    otp = code % (10 ** settings.MFA_TOTP_DIGITS)
    return str(otp).zfill(settings.MFA_TOTP_DIGITS)


def verify_totp(secret: str, code: str, window: int = 1) -> bool:
    normalized = (code or "").strip().replace(" ", "")
    if not normalized.isdigit() or len(normalized) != settings.MFA_TOTP_DIGITS:
        return False

    now = int(datetime.utcnow().timestamp())
    interval = settings.MFA_TOTP_INTERVAL_SECONDS
    for offset in range(-window, window + 1):
        if hmac.compare_digest(_generate_totp(secret, now + (offset * interval)), normalized):
            return True
    return False


def create_mfa_setup_token(email: str, secret: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.MFA_SETUP_TOKEN_EXPIRE_MINUTES)
    payload = {
        "exp": expire,
        "sub": email,
        "secret": secret,
        "purpose": "mfa_setup",
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def verify_mfa_setup_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("purpose") != "mfa_setup":
            return None
        return payload
    except JWTError:
        return None


def create_mfa_login_token(email: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.MFA_LOGIN_TOKEN_EXPIRE_MINUTES)
    payload = {
        "exp": expire,
        "sub": email,
        "purpose": "mfa_login",
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def verify_mfa_login_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("purpose") != "mfa_login":
            return None
        return payload.get("sub")
    except JWTError:
        return None
