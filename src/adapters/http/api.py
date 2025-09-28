import logging
from fastapi import APIRouter, Header, HTTPException
from src.schemas import SignupIn, SignupOut, RetryIn, HealthResponse, BuyerCreateIn
from src.adapters.keycloak.admin import KeycloakAdminClient
from src.adapters.buyers.client import BuyersClient
from src.core.config import settings
from src.utils.correlation import ensure_correlation_id, HEADER as CORR_HEADER

router = APIRouter()
log = logging.getLogger(__name__)

@router.get("/healthz", response_model=HealthResponse, tags=["health"])
def healthz():
    return {"status": "ok"}

@router.get("/readyz", response_model=HealthResponse, tags=["health"])
def readyz():
    # MVP: pronto se configs básicas existem
    return {"status": "ok"}

@router.post("/signup", response_model=SignupOut, tags=["signup"])
def signup(body: SignupIn, x_request_id: str | None = Header(None)):
    corr_id = ensure_correlation_id(x_request_id)
    kc = KeycloakAdminClient(corr_id)
    buyers = BuyersClient(corr_id)

    try:
        # 1) Cria (ou recupera) usuário no Keycloak
        user_id = kc.create_user(email=body.email, full_name=body.full_name, enabled=True)

        # 2) Sempre garante senha
        kc.set_password(user_id, body.password, temporary=False)

        # 3) Se roles configuradas, atribui
        if settings.DEFAULT_REALM_ROLES:
            try:
                kc.assign_realm_roles(user_id, settings.DEFAULT_REALM_ROLES)
            except PermissionError as pe:
                log.warning("Role assignment skipped: %s", pe)

        # 4) Cria buyer com external_id=user_id
        buyer = buyers.create_buyer(
            BuyerCreateIn(
                email=body.email,
                full_name=body.full_name,
                phone=body.phone,
                document=body.document,
                external_id=user_id,
            )
        )
        return {"keycloak_user_id": user_id, "buyer_id": buyer.id}

    except HTTPException:
        raise
    except Exception as e:
        log.exception("signup failed: %s", e)
        raise HTTPException(status_code=500, detail="signup_failed")

@router.post("/signup/retry", response_model=SignupOut, tags=["signup"])
def signup_retry(body: RetryIn, x_request_id: str | None = Header(None)):
    corr_id = ensure_correlation_id(x_request_id)
    buyers = BuyersClient(corr_id)
    try:
        buyer = buyers.create_buyer(
            BuyerCreateIn(
                email=body.email,
                full_name=body.full_name,
                phone=body.phone,
                document=body.document,
                external_id=body.keycloak_user_id,
            )
        )
        return {"keycloak_user_id": body.keycloak_user_id, "buyer_id": buyer.id}
    except Exception as e:
        log.exception("signup_retry failed: %s", e)
        raise HTTPException(status_code=500, detail="signup_retry_failed")
