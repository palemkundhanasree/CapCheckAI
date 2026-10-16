import re
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import User
from app.security.authentication import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_user_optional,
    TokenData
)
from app.config import settings
from app.services.email_service import generate_otp, hash_otp, otp_matches, send_otp_email, smtp_configured

router = APIRouter(prefix="/auth", tags=["Authentication"])

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    username: Optional[str] = None


class LoginRequest(BaseModel):
    # The frontend sends "identifier"; "email" is accepted for API clients.
    identifier: Optional[str] = None
    email: Optional[str] = None
    password: str


class ForgotPasswordRequest(BaseModel):
    email: str


class VerifyOtpResetRequest(BaseModel):
    email: str
    otp: str
    new_password: str


class OtpLoginVerifyRequest(BaseModel):
    email: str
    otp: str


class UserResponse(BaseModel):
    id: str
    email: str
    name: Optional[str] = None
    username: Optional[str] = None
    role: str
    created_at: datetime

    class Config:
        from_attributes = True


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


MAX_OTP_ATTEMPTS = 5
OTP_RESEND_SECONDS = 45


def _validate_password(password: str) -> None:
    if len(password) < 8 or not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters and include a letter and a number."
        )


def _auth_response(user: User) -> AuthResponse:
    token = create_access_token(data={"sub": user.email, "role": user.role, "uid": user.id})
    return AuthResponse(
        access_token=token,
        user=UserResponse(
            id=user.id,
            email=user.email,
            name=user.name or user.username or "User",
            username=user.username,
            role=user.role,
            created_at=user.created_at,
        ),
    )


def _issue_otp(db: Session, email: str, purpose: str) -> dict:
    """Creates and emails a one-time code. The response is identical whether or not the account exists."""
    clean_email = email.strip().lower()
    user = db.query(User).filter(User.email == clean_email).first()
    configured = smtp_configured()
    result = {
        "message": f"If an account exists for {clean_email}, a 6-digit code has been sent to that address. It expires in {settings.OTP_TTL_MINUTES} minutes.",
        "email": clean_email,
        "email_delivery_configured": configured,
    }
    if not user:
        return result

    # Throttle repeated requests for the same account
    if user.otp_expires_at:
        issued_at = user.otp_expires_at - timedelta(minutes=settings.OTP_TTL_MINUTES)
        if (datetime.utcnow() - issued_at).total_seconds() < OTP_RESEND_SECONDS:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Please wait {OTP_RESEND_SECONDS} seconds before requesting another code."
            )

    otp = generate_otp()
    user.otp_code = hash_otp(user.email, otp)
    user.otp_expires_at = datetime.utcnow() + timedelta(minutes=settings.OTP_TTL_MINUTES)
    user.otp_attempts = 0
    db.commit()

    delivery = send_otp_email(user.email, otp, user.name or "User", purpose=purpose)
    if delivery == "failed":
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="We could not send the email right now. Please try again in a few minutes."
        )
    if delivery == "not_configured" and settings.EXPOSE_DEV_OTP:
        result["dev_otp"] = otp  # local development only (EXPOSE_DEV_OTP=true)
    return result


def _check_otp(db: Session, email: str, otp: str) -> User:
    clean_email = email.strip().lower()
    user = db.query(User).filter(User.email == clean_email).first()
    generic = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="That code is invalid or has expired. Request a new code and try again."
    )
    if not user or not user.otp_code or not user.otp_expires_at:
        raise generic
    if datetime.utcnow() > user.otp_expires_at or (user.otp_attempts or 0) >= MAX_OTP_ATTEMPTS:
        user.otp_code = None
        user.otp_expires_at = None
        db.commit()
        raise generic
    if not otp_matches(user.email, otp, user.otp_code):
        user.otp_attempts = (user.otp_attempts or 0) + 1
        db.commit()
        raise generic
    return user


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    """Registers a new user account."""
    _validate_password(req.password)
    if not req.name.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Please enter your name.")

    clean_email = req.email.strip().lower()
    if not EMAIL_REGEX.match(clean_email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please provide a valid email address (e.g. name@example.com)."
        )

    if db.query(User).filter(User.email == clean_email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists. Please sign in."
        )

    username_candidate = clean_email.split("@")[0]
    new_user = User(
        email=clean_email,
        name=req.name.strip(),
        username=username_candidate,
        hashed_password=get_password_hash(req.password),
        role="user"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return _auth_response(new_user)


@router.post("/login", response_model=AuthResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """Authenticates a user via email/username and password."""
    clean_identifier = (req.identifier or req.email or "").strip().lower()
    user = db.query(User).filter(
        (User.email == clean_identifier) | (User.username == clean_identifier)
    ).first() if clean_identifier else None

    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password. Please check your credentials."
        )
    return _auth_response(user)


@router.post("/forgot-password")
def forgot_password(req: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """Emails a 6-digit reset code to the account's address."""
    return _issue_otp(db, req.email, purpose="reset")


@router.post("/verify-otp-reset")
def verify_otp_reset(req: VerifyOtpResetRequest, db: Session = Depends(get_db)):
    """Validates the emailed code and sets a new password."""
    _validate_password(req.new_password)
    user = _check_otp(db, req.email, req.otp)
    user.hashed_password = get_password_hash(req.new_password)
    user.otp_code = None
    user.otp_expires_at = None
    user.otp_attempts = 0
    db.commit()
    return {"message": "Password updated. You can now sign in with your new password."}


@router.post("/login-otp/request")
def request_login_otp(req: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """Emails a one-time sign-in code (passwordless login)."""
    return _issue_otp(db, req.email, purpose="login")


@router.post("/login-otp/verify", response_model=AuthResponse)
def verify_login_otp(req: OtpLoginVerifyRequest, db: Session = Depends(get_db)):
    """Signs the user in with the emailed code."""
    user = _check_otp(db, req.email, req.otp)
    user.otp_code = None
    user.otp_expires_at = None
    user.otp_attempts = 0
    db.commit()
    return _auth_response(user)


@router.get("/me", response_model=UserResponse)
def get_current_user_profile(
    token_data: Optional[TokenData] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Returns the authenticated user's profile."""
    if not token_data or not token_data.username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated. Please sign in."
        )

    user = db.query(User).filter(
        (User.email == token_data.username) | (User.username == token_data.username)
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )

    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name or user.username,
        username=user.username,
        role=user.role,
        created_at=user.created_at
    )
