from fastapi import APIRouter

from .cards import router as cards_router

router = APIRouter()
router.include_router(cards_router, prefix="/cards", tags=["Cards"])
