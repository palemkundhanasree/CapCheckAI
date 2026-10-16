import hashlib
import hmac
import os
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel
from app.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/admin/login", auto_error=False)

ALGORITHM = "HS256"


class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None
    uid: Optional[str] = None


def get_password_hash(password: str) -> str:
    salt = os.urandom(16)
    kdf = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
    return f"{salt.hex()}${kdf.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        parts = hashed_password.split("$")
        if len(parts) != 2:
            return False
        salt = bytes.fromhex(parts[0])
        expected_kdf = bytes.fromhex(parts[1])
        actual_kdf = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt, 100000)
        return hmac.compare_digest(actual_kdf, expected_kdf)
    except Exception:
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user_optional(token: Optional[str] = Depends(oauth2_scheme)) -> Optional[TokenData]:
    if not token:
        return None
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        role: str = payload.get("role", "user")
        uid: Optional[str] = payload.get("uid")
        if username is None:
            return None
        return TokenData(username=username, role=role, uid=uid)
    except JWTError:
        return None


async def require_admin_user(token_data: Optional[TokenData] = Depends(get_current_user_optional)) -> TokenData:
    if not token_data or token_data.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required."
        )
    return token_data


async def require_user(token_data: Optional[TokenData] = Depends(get_current_user_optional)) -> TokenData:
    """Every verification, history, job and report endpoint requires a signed-in user."""
    if not token_data or not token_data.uid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Please sign in to use CapCheck AI.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token_data


def can_access(owner_id: Optional[str], user: TokenData) -> bool:
    """A record is accessible to its owner and to administrators."""
    return user.role == "admin" or (owner_id is not None and owner_id == user.uid)
