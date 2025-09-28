from pydantic import BaseModel, EmailStr, Field
from uuid import UUID

# ===== Public payloads =====
class SignupIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str
    phone: str | None = None
    document: str | None = None

class SignupOut(BaseModel):
    keycloak_user_id: str
    buyer_id: UUID

class RetryIn(BaseModel):
    keycloak_user_id: str
    email: EmailStr
    full_name: str
    phone: str | None = None
    document: str | None = None

class HealthResponse(BaseModel):
    status: str

# ===== Internal DTOs =====
class BuyerCreateIn(BaseModel):
    email: EmailStr
    full_name: str
    phone: str | None = None
    document: str | None = None
    external_id: str | None = None  # keycloak user id

class BuyerOut(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str
    phone: str | None
    document: str | None
    external_id: str | None
