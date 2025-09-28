import logging
import httpx
from typing import Optional
from tenacity import retry, stop_after_attempt, wait_exponential_jitter

from src.schemas import BuyerCreateIn, BuyerOut
from src.core.config import settings

log = logging.getLogger(__name__)


class BuyersClient:
    def __init__(self, correlation_id: str):
        self.base = settings.BUYERS_BASE_URL.rstrip("/")
        self.timeout = settings.HTTP_TIMEOUT_SECS
        self.corr = correlation_id

    def _headers(self) -> dict[str, str]:
        return {"Accept": "application/json", "X-Request-ID": self.corr}

    @retry(stop=stop_after_attempt(settings.RETRIES),
           wait=wait_exponential_jitter(initial=settings.RETRY_BACKOFF_FACTOR))
    def create_buyer(self, data: BuyerCreateIn) -> BuyerOut:
        url = f"{self.base}/buyers"
        with httpx.Client(timeout=self.timeout) as c:
            r = c.post(url, json=data.model_dump(), headers=self._headers())
            if r.status_code == 409:
                log.warning("Buyer already exists by email; attempting to fetch existing buyer.")
                existing = self.get_buyer_by_email(data.email)
                if existing:
                    return existing
                raise RuntimeError("Buyer already exists but could not fetch details")
            r.raise_for_status()
            return BuyerOut(**r.json())

    @retry(stop=stop_after_attempt(settings.RETRIES),
           wait=wait_exponential_jitter(initial=settings.RETRY_BACKOFF_FACTOR))
    def get_buyer_by_email(self, email: str) -> Optional[BuyerOut]:
        url = f"{self.base}/buyers"
        params = {"email": email}
        with httpx.Client(timeout=self.timeout) as c:
            r = c.get(url, params=params, headers=self._headers())
            r.raise_for_status()
            arr = r.json()
            if arr:
                return BuyerOut(**arr[0])
            return None

    @retry(stop=stop_after_attempt(settings.RETRIES),
           wait=wait_exponential_jitter(initial=settings.RETRY_BACKOFF_FACTOR))
    def get_buyer_by_external_id(self, external_id: str) -> Optional[BuyerOut]:
        url = f"{self.base}/buyers"
        params = {"external_id": external_id}
        with httpx.Client(timeout=self.timeout) as c:
            r = c.get(url, params=params, headers=self._headers())
            r.raise_for_status()
            arr = r.json()
            if arr:
                return BuyerOut(**arr[0])
            return None
