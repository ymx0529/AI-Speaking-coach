from __future__ import annotations

from base64 import b64encode
import json
from uuid import uuid4

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect

from app.modules.conversation.audio_utils import merge_sorted_chunks
from app.modules.conversation.azure_speech import synthesize_reply_audio
from app.modules.conversation.llm_client import generate_reply
from app.modules.conversation.qwen_stt import build_partial_transcript, transcribe_chunks
from app.core import event_bus, ws_hub
from app.core.types import (
    CorrectionIssue,
    PronScore,
    SessionStatusResponse,
    SpeakerTurnEvent,
    TurnTranscriptReadyEvent,
    WordScore,
)
from app.modules.conversation.session_manager import (
    append_audio_chunk,
    append_turn,
    finalize_turn,
    end_session,
    get_session,
    start_session,
)

router = APIRouter()


def _encoding_to_source_format(encoding: str | None) -> str:
    if encoding == "wav_pcm16":
        return "wav"
    return "webm"


@router.get("/api/sessions/{session_id}/status", response_model=SessionStatusResponse)
async def get_session_status(session_id: str) -> SessionStatusResponse:
    session = get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found.")

    last_turn_id = session.current_turn_id
    return SessionStatusResponse(
        session_id=session_id,
        state=session.session_status,
        summary_ready=False,
        last_turn_id=last_turn_id,
        last_error=None,
    )


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


def _handle_asr_partial(websocket: WebSocket, session_id: str, turn_id: str, text: str):
    return websocket.send_json(
        {
            "type": "asr.partial",
            "session_id": session_id,
            "turn_id": turn_id,
            "text": text,
            "server_ts": 0,
        }
    )


@router.websocket("/ws/session/{session_id}")
async def session_ws(websocket: WebSocket, session_id: str) -> None:
    await websocket.accept()
    ws_hub.register(session_id, websocket)

    try:
        while True:
            raw = await websocket.receive_text()
            payload = json.loads(raw)
            msg_type = payload.get("type")

            if msg_type in {"session_start", "session.start"}:
                start_session(
                    session_id=session_id,
                    scene_id=payload.get("scene_id", "interview"),
                    difficulty=payload.get("difficulty", 1),
                    persona_id=payload.get("persona_id", "strict_interviewer"),
                )
                if msg_type == "session.start":
                    await websocket.send_json(
                        {
                            "type": "session.ready",
                            "session_id": session_id,
                            "server_ts": payload.get("client_ts", 0),
                        }
                    )
            elif msg_type in {"audio_chunk", "audio.append"}:
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

                if msg_type == "audio.append":
                    previous_turn_id = session.current_turn_id
                    turn_id = append_audio_chunk(
                        session_id,
                        payload.get("seq", 0),
                        payload.get("chunk", ""),
                        now_ms=payload.get("client_ts", 0),
                    )
                    session = get_session(session_id)
                    if turn_id is None or session is None:
                        await websocket.send_json(
                            {
                                "type": "error",
                                "code": "BAD_REQUEST",
                                "message": "Turn could not be started.",
                            }
                        )
                        continue

                    if previous_turn_id is None:
                        await websocket.send_json(
                            {
                                "type": "turn.started",
                                "session_id": session_id,
                                "turn_id": turn_id,
                                "server_ts": payload.get("client_ts", 0),
                            }
                        )
                    if not payload.get("is_last", False):
                        partial_text = build_partial_transcript(session.current_turn_audio_chunks)
                        await _handle_asr_partial(websocket, session_id, turn_id, partial_text)
                        continue

                    finalized_turn = finalize_turn(session_id, now_ms=payload.get("client_ts", 0))
                    if finalized_turn is None:
                        await websocket.send_json(
                            {
                                "type": "error",
                                "code": "BAD_REQUEST",
                                "message": "No active turn to finalize.",
                            }
                        )
                        continue

                    try:
                        final_text, duration_ms = transcribe_chunks(
                            list(enumerate(finalized_turn.audio_chunks)),
                            source_format=_encoding_to_source_format(payload.get("encoding")),
                        )
                    except Exception as exc:
                        await websocket.send_json(
                            {
                                "type": "error",
                                "session_id": session_id,
                                "turn_id": finalized_turn.turn_id,
                                "code": "ASR_FAILED",
                                "message": str(exc),
                                "retryable": True,
                            }
                        )
                        continue
                    await websocket.send_json(
                        {
                            "type": "user_turn.final",
                            "session_id": session_id,
                            "turn_id": finalized_turn.turn_id,
                            "text": final_text,
                            "duration_ms": duration_ms,
                            "server_ts": payload.get("client_ts", 0),
                        }
                    )
                    ai_reply = generate_reply(
                        scene_id=session.scene_id,
                        persona_id=session.persona_id,
                        difficulty=session.difficulty,
                        history=session.history,
                        user_text=final_text,
                    )
                    await websocket.send_json(
                        {
                            "type": "assistant.reply_text",
                            "session_id": session_id,
                            "turn_id": finalized_turn.turn_id,
                            "text": ai_reply,
                        }
                    )
                    audio_data, audio_format = synthesize_reply_audio(ai_reply)
                    await websocket.send_json(
                        {
                            "type": "assistant.reply_audio",
                            "session_id": session_id,
                            "turn_id": finalized_turn.turn_id,
                            "audio_format": audio_format,
                            "data": audio_data,
                        }
                    )
                    merged_audio_bytes = merge_sorted_chunks(list(enumerate(finalized_turn.audio_chunks)))
                    await event_bus.publish(
                        TurnTranscriptReadyEvent(
                            session_id=session_id,
                            turn_id=finalized_turn.turn_id,
                            scene_id=session.scene_id,
                            difficulty=session.difficulty,
                            persona_id=session.persona_id,
                            transcript=final_text,
                            audio_format="wav_pcm16",
                            audio_b64=b64encode(merged_audio_bytes).decode("utf-8"),
                            assistant_reply_text=ai_reply,
                            turn_duration_ms=duration_ms,
                        )
                    )
                    continue

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
                user_text, _legacy_ai_reply, pron_score, corrections = _mock_turn_payload(
                    session.scene_id,
                    session.turn_count + 1,
                )
                ai_reply = generate_reply(
                    scene_id=session.scene_id,
                    persona_id=session.persona_id,
                    difficulty=session.difficulty,
                    history=session.history,
                    user_text=user_text,
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
            elif msg_type in {"session_end", "session.finish"}:
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
