from fastapi import APIRouter, HTTPException

from app.core.types import SessionSummaryResponse
from app.modules.coach import summary_service

router = APIRouter()


@router.post("/sessions/{session_id}/summary", response_model=SessionSummaryResponse)
async def get_summary(session_id: str) -> SessionSummaryResponse:
    summary = summary_service.build_summary(session_id)
    if summary is None:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found.")
    return summary
