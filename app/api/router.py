from fastapi import APIRouter

from app.api.v1.shoe_lasts import router as shoe_lasts_router


api_router = APIRouter()

api_router.include_router(shoe_lasts_router)
