import logging
from fastapi import FastAPI
from src.core.logging import setup_logging
from src.adapters.http.api import router
from src.core.config import settings

setup_logging("INFO")
log = logging.getLogger(__name__)

app = FastAPI(title=settings.APP_NAME)

app.include_router(router)

@app.on_event("startup")
def on_startup():
    log.info("Starting %s", settings.APP_NAME)

@app.get("/")
def root():
    return {"service": settings.APP_NAME}
