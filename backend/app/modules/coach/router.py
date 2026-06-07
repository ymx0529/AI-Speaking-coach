import asyncio

from fastapi import APIRouter, Depends, HTTPException

from app.core.types import (
    SessionSummaryResponse,
    ShadowingAssessmentResponse,
    ShadowingAssessRequest,
    ShadowingItemsResponse,
    ShadowingTtsRequest,
    ShadowingTtsResponse,
)
from app.modules.auth.dependencies import CurrentUser, require_auth_user
from app.modules.coach import pronunciation_service, shadowing_service, store as coach_store, summary_service
from app.modules.conversation.azure_speech import synthesize_reply_audio

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


@router.get("/sessions/{session_id}/shadowing/items", response_model=ShadowingItemsResponse)
async def get_shadowing_items(
    session_id: str,
    user: CurrentUser = Depends(require_auth_user),
) -> ShadowingItemsResponse:
    turns = _get_user_turns(session_id, user.id)
    return ShadowingItemsResponse(
        session_id=session_id,
        items=shadowing_service.build_shadowing_items(turns),
    )


@router.post("/shadowing/tts", response_model=ShadowingTtsResponse)
async def synthesize_shadowing_tts(
    payload: ShadowingTtsRequest,
    _user: CurrentUser = Depends(require_auth_user),
) -> ShadowingTtsResponse:
    audio_data, audio_format = await asyncio.to_thread(synthesize_reply_audio, payload.text)
    return ShadowingTtsResponse(audio_format=audio_format, data=audio_data)


@router.post(
    "/sessions/{session_id}/shadowing/assess",
    response_model=ShadowingAssessmentResponse,
)
async def assess_shadowing(
    session_id: str,
    payload: ShadowingAssessRequest,
    user: CurrentUser = Depends(require_auth_user),
) -> ShadowingAssessmentResponse:
    _get_user_turns(session_id, user.id)
    pronunciation = await pronunciation_service.assess(payload.text, payload.audio_b64)
    return shadowing_service.build_assessment(
        item_id=payload.item_id,
        target_text=payload.text,
        pronunciation=pronunciation,
    )


def _get_user_turns(session_id: str, user_id: str):
    turns = coach_store.get_session_turns(session_id)
    if not turns or any(turn.user_id != user_id for turn in turns):
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found.")
    return turns
