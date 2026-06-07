from fastapi import APIRouter, Depends, HTTPException

from app.core.types import SessionSummaryResponse
from app.modules.auth.dependencies import CurrentUser, require_auth_user
from app.modules.coach import summary_service

router = APIRouter()


@router.post("/sessions/{session_id}/summary", response_model=SessionSummaryResponse)
async def get_summary(
    session_id: str,
    user: CurrentUser = Depends(require_auth_user),
) -> SessionSummaryResponse:
    summary = summary_service.build_summary(session_id, user_id=user.id)
    if summary is None:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found.")
    return summary
