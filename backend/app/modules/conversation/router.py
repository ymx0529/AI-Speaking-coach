from __future__ import annotations

import json
from uuid import uuid4

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core import event_bus, ws_hub
from app.core.types import CorrectionIssue, PronScore, SpeakerTurnEvent, WordScore
from app.modules.conversation.session_manager import (
    append_audio_chunk,
    append_turn,
    end_session,
    get_session,
    start_session,
)

router = APIRouter()


def _mock_turn_payload(scene_id: str, turn_index: int) -> tuple[str, str, PronScore, list[CorrectionIssue]]:
    samples = {
        "interview": (
            "I am interested in this position because I enjoy solving problems.",
            "That is a solid start. Could you share a project you are proud of?",
        ),
        "restaurant": (
            "I would like a pasta and a glass of water, please.",
            "Sure. Would you like a salad or soup with that?",
        ),
        "meeting": (
            "I think we should increase the marketing budget this quarter.",
            "Interesting point. What result do you expect from that change?",
        ),
    }
    user_text, ai_reply = samples.get(scene_id, samples["interview"])
    overall = 70 + min(turn_index * 3, 12)
    pron_score = PronScore(
        overall=overall,
        accuracy=overall - 4,
        fluency=overall + 3,
        completeness=90,
        words=[
            WordScore(word="interested", accuracy_score=58, error_type="Mispronunciation"),
            WordScore(word="position", accuracy_score=82, error_type="None"),
        ],
    )
    corrections = [
        CorrectionIssue(
            original="I am interest in",
            corrected="I am interested in",
            explanation="Use the adjective form here.",
            category="grammar",
        )
    ]
    return user_text, ai_reply, pron_score, corrections


@router.websocket("/ws/session/{session_id}")
async def session_ws(websocket: WebSocket, session_id: str) -> None:
    await websocket.accept()
    ws_hub.register(session_id, websocket)

    try:
        while True:
            raw = await websocket.receive_text()
            payload = json.loads(raw)
            msg_type = payload.get("type")

            if msg_type == "session_start":
                start_session(
                    session_id=session_id,
                    scene_id=payload.get("scene_id", "interview"),
                    difficulty=payload.get("difficulty", 1),
                    persona_id=payload.get("persona_id", "strict_interviewer"),
                )
            elif msg_type == "audio_chunk":
                append_audio_chunk(session_id, payload.get("seq", 0), payload.get("data", ""))
            elif msg_type == "audio_end":
                session = get_session(session_id)
                if session is None:
                    await websocket.send_json(
                        {
                            "type": "error",
                            "code": "BAD_REQUEST",
                            "message": "Session not started.",
                        }
                    )
                    continue

                turn_id = str(uuid4())
                user_text, ai_reply, pron_score, corrections = _mock_turn_payload(
                    session.scene_id,
                    session.turn_count + 1,
                )
                append_turn(session_id, turn_id, user_text, ai_reply, pron_score, corrections)

                await websocket.send_json(
                    {
                        "type": "asr_final",
                        "turn_id": turn_id,
                        "text": user_text,
                        "duration_ms": 2200,
                    }
                )
                await websocket.send_json(
                    {
                        "type": "pron_score",
                        "turn_id": turn_id,
                        **pron_score.model_dump(),
                    }
                )
                await websocket.send_json(
                    {
                        "type": "reply_text",
                        "turn_id": turn_id,
                        "text": ai_reply,
                    }
                )
                await websocket.send_json(
                    {
                        "type": "correction",
                        "turn_id": turn_id,
                        "issues": [issue.model_dump() for issue in corrections],
                    }
                )
                await event_bus.publish(
                    SpeakerTurnEvent(
                        session_id=session_id,
                        turn_id=turn_id,
                        user_text=user_text,
                        pron_score=pron_score,
                        ai_reply=ai_reply,
                        scene_id=session.scene_id,
                    )
                )
                await websocket.send_json({"type": "turn_end", "turn_id": turn_id})
            elif msg_type == "session_end":
                break
            else:
                await websocket.send_json(
                    {
                        "type": "error",
                        "code": "BAD_REQUEST",
                        "message": f"Unknown message type: {msg_type}",
                    }
                )
    except WebSocketDisconnect:
        pass
    finally:
        end_session(session_id)
        ws_hub.unregister(session_id)
