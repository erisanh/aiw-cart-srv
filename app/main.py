from app.api.v1.api import api_router
from app.core.config import settings
from app.util.logger import setup_logger
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

logger = setup_logger()
app = FastAPI()

app.add_middleware(SessionMiddleware, secret_key=settings.JWT_SECRET_KEY)

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)

if settings.ENV in ["local", "dev"]:
    logger.info(f"🦆🦆🦆 {settings.ENV} 🦆🦆🦆")