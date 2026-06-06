from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.modules.conversation.llm_client import build_reply_prompt, generate_reply


class _FakeMessage:
    def __init__(self, content: str | None = None):
        self.content = content


class _FakeChoice:
    def __init__(self, content: str | None = None):
        self.message = _FakeMessage(content)


class _FakeResponse:
    def __init__(self, content: str | None = None):
        self.choices = [_FakeChoice(content)]


class _FakeChatCompletions:
    def __init__(self):
        self.last_kwargs: dict | None = None

    def create(self, **kwargs):
        self.last_kwargs = kwargs
        return _FakeResponse("Alex: Could you tell me more about your recent project?")


class _FakeClient:
    def __init__(self):
        self.chat = type("ChatNamespace", (), {"completions": _FakeChatCompletions()})()


def test_build_reply_prompt_uses_scene_persona_and_difficulty():
    prompt = build_reply_prompt(
        scene_id="interview",
        persona_id="strict_interviewer",
        difficulty=2,
        history=[],
        user_text="I have five years of backend experience.",
    )

    assert prompt["scene_name"] == "Job Interview"
    assert prompt["persona_name"] == "Alex"
    assert "strict but professional interviewer" in prompt["messages"][0]["content"].lower()
    assert prompt["messages"][-1]["content"] == "I have five years of backend experience."


def test_generate_reply_calls_qwen_chat_model(monkeypatch):
    fake_client = _FakeClient()
    monkeypatch.setattr("app.modules.conversation.llm_client._get_client", lambda: fake_client)

    reply = generate_reply(
        scene_id="meeting",
        persona_id="colleague",
        difficulty=1,
        history=[],
        user_text="I think we should launch next month.",
    )

    assert "project" in reply.lower() or "could you tell me more" in reply.lower()
    kwargs = fake_client.chat.completions.last_kwargs
    assert kwargs is not None
    assert kwargs["model"] == "qwen3.5-flash"
    assert kwargs["stream"] is False
    assert kwargs["max_tokens"] == 80
    assert "enable_thinking" in kwargs["extra_body"]


def test_generate_reply_falls_back_when_qwen_fails(monkeypatch):
    def _raise():
        raise RuntimeError("network failed")

    monkeypatch.setattr("app.modules.conversation.llm_client._get_client", _raise)

    reply = generate_reply(
        scene_id="restaurant",
        persona_id="friendly_waiter",
        difficulty=1,
        history=[],
        user_text="I would like some water.",
    )

    assert "Would you like anything else" in reply
