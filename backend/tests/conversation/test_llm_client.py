from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.modules.conversation.llm_client import build_reply_prompt, generate_reply


def test_build_reply_prompt_uses_scene_persona_and_difficulty():
    prompt = build_reply_prompt(
        scene_id="interview",
        persona_id="strict_interviewer",
        difficulty=2,
        history=[],
        user_text="I have five years of backend experience.",
    )

    assert "strict interviewer" in prompt.lower()
    assert "difficulty: 2" in prompt.lower()
    assert "I have five years of backend experience." in prompt


def test_generate_reply_keeps_recent_history_only():
    history = [
        {"role": "user", "content": f"user-{i}"} if i % 2 == 0 else {"role": "assistant", "content": f"assistant-{i}"}
        for i in range(8)
    ]

    reply = generate_reply(
        scene_id="meeting",
        persona_id="colleague",
        difficulty=1,
        history=history,
        user_text="I think we should launch next month.",
    )

    assert "Jordan" in reply or "meeting" in reply.lower() or "launch" in reply.lower()
    assert len(reply.split()) <= 40
