import uuid

HEADER = "X-Request-ID"

def ensure_correlation_id(existing: str | None = None) -> str:
    return existing or str(uuid.uuid4())
