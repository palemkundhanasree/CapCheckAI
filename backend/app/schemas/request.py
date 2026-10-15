from typing import Optional
from pydantic import BaseModel, Field, HttpUrl


class ClaimVerifyRequest(BaseModel):
    claim_text: str = Field(..., min_length=5, max_length=2000, description="The factual claim to verify")
    context: Optional[str] = Field(None, max_length=1000, description="Optional background or surrounding context")
    demo_mode: Optional[bool] = Field(None, description="Force demo verification simulation mode")


class UrlVerifyRequest(BaseModel):
    url: str = Field(..., description="Target news article or public web page URL")
    demo_mode: Optional[bool] = Field(None, description="Force demo verification simulation mode")


class AdminLoginRequest(BaseModel):
    username: str
    password: str
