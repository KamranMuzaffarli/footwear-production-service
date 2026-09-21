from fastapi import APIRouter

from app.api.v1.materials import router as materials_router
from app.api.v1.model_classes import router as model_classes_router
from app.api.v1.reference import router as reference_router
from app.api.v1.shoe_lasts import router as shoe_lasts_router
from app.api.v1.shoe_models import router as shoe_models_router

from app.api.v1.production_composition import (
    router as production_composition_router,
)


api_router = APIRouter()

api_router.include_router(shoe_lasts_router)
api_router.include_router(shoe_models_router)
api_router.include_router(model_classes_router)
api_router.include_router(materials_router)
api_router.include_router(reference_router)
api_router.include_router(production_composition_router)
