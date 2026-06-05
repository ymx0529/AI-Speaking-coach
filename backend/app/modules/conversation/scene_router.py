from fastapi import APIRouter

from app.core.scenes import SCENES

router = APIRouter()


@router.get("/scenes")
async def list_scenes() -> dict[str, dict]:
    return SCENES

