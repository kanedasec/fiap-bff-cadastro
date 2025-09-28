import logging
import httpx
from typing import Any
from tenacity import retry, stop_after_attempt, wait_exponential_jitter
from src.core.config import settings

log = logging.getLogger(__name__)

class KeycloakAdminClient:
    def __init__(self, correlation_id: str):
        self.base = settings.KEYCLOAK_BASE_URL.rstrip("/")
        self.realm = settings.KEYCLOAK_REALM
        self.client_id = settings.KEYCLOAK_CLIENT_ID
        self.client_secret = settings.KEYCLOAK_CLIENT_SECRET
        self.timeout = settings.HTTP_TIMEOUT_SECS
        self.corr = correlation_id

    def _headers(self, token: str | None = None) -> dict[str, str]:
        h = {"Accept": "application/json", "X-Request-ID": self.corr}
        if token:
            h["Authorization"] = f"Bearer {token}"
        return h

    @retry(stop=stop_after_attempt(settings.RETRIES), wait=wait_exponential_jitter(initial=settings.RETRY_BACKOFF_FACTOR))
    def _token(self) -> str:
        url = f"{self.base}/realms/{self.realm}/protocol/openid-connect/token"
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        with httpx.Client(timeout=self.timeout) as c:
            resp = c.post(url, data=data, headers={"X-Request-ID": self.corr})
            resp.raise_for_status()
            return resp.json()["access_token"]

    @retry(stop=stop_after_attempt(settings.RETRIES), wait=wait_exponential_jitter(initial=settings.RETRY_BACKOFF_FACTOR))
    def create_user(self, email: str, full_name: str, enabled: bool = True) -> str:
        token = self._token()
        url = f"{self.base}/admin/realms/{self.realm}/users"
        payload = {
            "username": email,
            "email": email,
            "enabled": enabled,
            "emailVerified": False,
            "firstName": full_name,
        }
        with httpx.Client(timeout=self.timeout) as c:
            r = c.post(url, json=payload, headers=self._headers(token))

            if r.status_code == 201:
                log.info("User created in Keycloak: %s", email)
            elif r.status_code == 409:
                log.info("User already exists in Keycloak: %s", email)
            else:
                r.raise_for_status()

            # Resolve user_id sempre (novo ou já existente)
            user_id = self.find_user_id_by_username(email, token=token)
            if not user_id:
                raise RuntimeError("Could not resolve Keycloak user id")
            return user_id

    @retry(stop=stop_after_attempt(settings.RETRIES), wait=wait_exponential_jitter(initial=settings.RETRY_BACKOFF_FACTOR))
    def find_user_id_by_username(self, username: str, token: str | None = None) -> str | None:
        tok = token or self._token()
        url = f"{self.base}/admin/realms/{self.realm}/users"
        params = {"username": username, "exact": "true"}
        with httpx.Client(timeout=self.timeout) as c:
            r = c.get(url, params=params, headers=self._headers(tok))
            r.raise_for_status()
            arr = r.json()
            if arr:
                return arr[0]["id"]
            return None

    @retry(stop=stop_after_attempt(settings.RETRIES), wait=wait_exponential_jitter(initial=settings.RETRY_BACKOFF_FACTOR))
    def set_password(self, user_id: str, password: str, temporary: bool = False):
        token = self._token()
        url = f"{self.base}/admin/realms/{self.realm}/users/{user_id}/reset-password"
        payload = {"type": "password", "value": password, "temporary": temporary}
        with httpx.Client(timeout=self.timeout) as c:
            r = c.put(url, json=payload, headers=self._headers(token))
            r.raise_for_status()

    def _get_realm_role(self, role_name: str, token: str) -> dict[str, Any]:
        url = f"{self.base}/admin/realms/{self.realm}/roles/{role_name}"
        with httpx.Client(timeout=self.timeout) as c:
            r = c.get(url, headers=self._headers(token))
            if r.status_code == 403:
                log.error("No permission to fetch role '%s'", role_name)
                raise PermissionError(f"Forbidden to fetch role {role_name}")
            r.raise_for_status()
            return r.json()

    @retry(stop=stop_after_attempt(settings.RETRIES), wait=wait_exponential_jitter(initial=settings.RETRY_BACKOFF_FACTOR))
    def assign_realm_roles(self, user_id: str, role_names: list[str]):
        token = self._token()
        roles = [self._get_realm_role(rn, token) for rn in role_names]
        url = f"{self.base}/admin/realms/{self.realm}/users/{user_id}/role-mappings/realm"
        with httpx.Client(timeout=self.timeout) as c:
            r = c.post(url, json=roles, headers=self._headers(token))
            if r.status_code == 403:
                log.error("No permission to assign roles %s to user %s", role_names, user_id)
                raise PermissionError("Forbidden to assign roles")
            r.raise_for_status()
