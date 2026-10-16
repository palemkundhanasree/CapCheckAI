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
from app.services.email_service import generate_otp, send_otp_email

router = APIRouter(prefix="/auth", tags=["Authentication"])

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    username: Optional[str] = None


class LoginRequest(BaseModel):
    email: Optional[str] = None
    identifier: Optional[str] = None
    username: Optional[str] = None
    password: str


class ForgotPasswordRequest(BaseModel):
    email: str


class VerifyOtpResetRequest(BaseModel):
    email: str
    otp: str
    new_password: str


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


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    """Registers a new user account."""
    raw_password = req.password.strip()
    if len(raw_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters long."
        )

    clean_email = req.email.strip().lower()
    if not EMAIL_REGEX.match(clean_email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please provide a valid email address (e.g. name@example.com)."
        )

    existing_user = db.query(User).filter(User.email == clean_email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists. Please sign in."
        )

    # Clean username: user input if provided, otherwise derive from email prefix
    if req.username and req.username.strip():
        clean_username = req.username.strip().lower()
        existing_username = db.query(User).filter(User.username == clean_username).first()
        if existing_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Username '@{clean_username}' is already taken. Please choose another username."
            )
    else:
        base_username = clean_email.split("@")[0]
        clean_username = base_username
        count = 1
        while db.query(User).filter(User.username == clean_username).first():
            clean_username = f"{base_username}_{count}"
            count += 1

    new_user = User(
        email=clean_email,
        name=req.name.strip(),
        username=clean_username,
        hashed_password=get_password_hash(raw_password),
        role="user"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token = create_access_token(data={"sub": new_user.email, "role": new_user.role, "uid": new_user.id})
    return AuthResponse(
        access_token=token,
        user=UserResponse(
            id=new_user.id,
            email=new_user.email,
            name=new_user.name,
            username=new_user.username,
            role=new_user.role,
            created_at=new_user.created_at
        )
    )


@router.post("/login", response_model=AuthResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """Authenticates a user via email/username and password."""
    raw_identifier = (req.email or req.identifier or req.username or "").strip().lower()
    raw_password = req.password.strip()

    if not raw_identifier:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please provide your email address or username."
        )

    user = db.query(User).filter(
        (User.email == raw_identifier) | (User.username == raw_identifier)
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password. Please check your credentials."
        )

    # Verify password (try stripped and raw in case of whitespace)
    is_valid = verify_password(raw_password, user.hashed_password) or verify_password(req.password, user.hashed_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password. Please check your credentials."
        )

    token = create_access_token(data={"sub": user.email, "role": user.role, "uid": user.id})
    return AuthResponse(
        access_token=token,
        user=UserResponse(
            id=user.id,
            email=user.email,
            name=user.name or user.username or "User",
            username=user.username,
            role=user.role,
            created_at=user.created_at
        )
    )


@router.post("/forgot-password")
def forgot_password(req: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """Generates and dispatches a 6-digit OTP code to the user's email."""
    clean_email = req.email.strip().lower()
    user = db.query(User).filter(User.email == clean_email).first()

    # Generate OTP
    otp = generate_otp()
    expires_at = datetime.utcnow() + timedelta(minutes=15)

    if user:
        user.otp_code = otp
        user.otp_expires_at = expires_at
        db.commit()
        send_otp_email(user.email, otp, user.name or "User")

    return {
        "message": f"If an account exists for {clean_email}, a 6-digit verification code has been sent.",
        "email": clean_email,
        "dev_otp_hint": otp
    }


@router.post("/verify-otp-reset")
def verify_otp_reset(req: VerifyOtpResetRequest, db: Session = Depends(get_db)):
    """Validates the 6-digit OTP and resets the user's password."""
    clean_email = req.email.strip().lower()
    user = db.query(User).filter(User.email == clean_email).first()

    if not user or not user.otp_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active password reset request found for this email."
        )

    if user.otp_expires_at and datetime.utcnow() > user.otp_expires_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The verification code has expired. Please request a new one."
        )

    if req.otp.strip() != user.otp_code.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid 6-digit code. Please verify the code sent to your email."
        )

    if len(req.new_password.strip()) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 6 characters long."
        )

    user.hashed_password = get_password_hash(req.new_password)
    user.otp_code = None
    user.otp_expires_at = None
    db.commit()

    return {"message": "Password successfully updated! You can now log in with your new password."}


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
