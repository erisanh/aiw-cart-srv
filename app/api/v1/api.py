from fastapi import APIRouter

from app.api.v1.endpoints import cart, health

api_router = APIRouter()

api_router.include_router(health.router, tags=["health"])

api_router.include_router(cart.router, tags=["cart"])