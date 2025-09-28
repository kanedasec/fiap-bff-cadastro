from pydantic import BaseModel, Field
import os

class Settings(BaseModel):
    APP_NAME: str = "fiap-bff-signup"
    APP_PORT: int = int(os.getenv("APP_PORT", "8010"))

    # Keycloak (Admin)
    KEYCLOAK_BASE_URL: str = os.getenv("KEYCLOAK_BASE_URL", "http://localhost:8080")
    KEYCLOAK_REALM: str = os.getenv("KEYCLOAK_REALM", "fiap")
    KEYCLOAK_CLIENT_ID: str = os.getenv("KEYCLOAK_CLIENT_ID", "admin-cli")
    KEYCLOAK_CLIENT_SECRET: str = os.getenv("KEYCLOAK_CLIENT_SECRET", "change-me")

    # Roles para atribuir ao novo usuário
    DEFAULT_REALM_ROLES: list[str] = Field(
        default_factory=lambda: os.getenv("DEFAULT_REALM_ROLES", "buyers_read,buyers_write").split(",")
    )

    # Buyers API
    BUYERS_BASE_URL: str = os.getenv("BUYERS_BASE_URL", "http://localhost:8002")

    # HTTP
    HTTP_TIMEOUT_SECS: float = float(os.getenv("HTTP_TIMEOUT_SECS", "10"))
    RETRIES: int = int(os.getenv("RETRIES", "3"))
    RETRY_BACKOFF_FACTOR: float = float(os.getenv("RETRY_BACKOFF_FACTOR", "0.5"))

settings = Settings()
