from fastapi import APIRouter
from api.routes import webhooks, health

api_router = APIRouter()
api_router.include_router(webhooks.router, prefix="/webhook", tags=["webhook"])
api_router.include_router(health.router, tags=["health"])
