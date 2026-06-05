from fastapi import APIRouter, HTTPException

from app.core.types import SessionSummaryResponse
from app.modules.conversation.session_manager import get_session

router = APIRouter()


@router.post("/sessions/{session_id}/summary", response_model=SessionSummaryResponse)
async def get_summary(session_id: str) -> SessionSummaryResponse:
    session = get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found.")

    turns = session.turns
    if not turns:
        return SessionSummaryResponse(
            session_id=session_id,
            scene_id=session.scene_id,
            total_turns=0,
            pron_avg=0,
            accuracy_avg=0,
            fluency_avg=0,
            completeness_avg=0,
            corrections_count=0,
            ai_feedback="本次还没有练习记录，先完成至少一轮对话。",
            turns=[],
        )

    total_turns = len(turns)
    pron_avg = sum(turn.pron_score.overall for turn in turns) / total_turns
    accuracy_avg = sum(turn.pron_score.accuracy for turn in turns) / total_turns
    fluency_avg = sum(turn.pron_score.fluency for turn in turns) / total_turns
    completeness_avg = sum(turn.pron_score.completeness for turn in turns) / total_turns
    corrections_count = sum(len(turn.corrections) for turn in turns)

    return SessionSummaryResponse(
        session_id=session_id,
        scene_id=session.scene_id,
        total_turns=total_turns,
        pron_avg=round(pron_avg, 1),
        accuracy_avg=round(accuracy_avg, 1),
        fluency_avg=round(fluency_avg, 1),
        completeness_avg=round(completeness_avg, 1),
        corrections_count=corrections_count,
        ai_feedback="最小验证版已跑通：你可以看到识别、评分、纠错和总结链路已经串起来。",
        turns=turns,
    )
