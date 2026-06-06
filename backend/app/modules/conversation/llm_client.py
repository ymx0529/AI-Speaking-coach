from __future__ import annotations

from openai import OpenAI

from app.core.config import settings
from app.core.scenes import SCENES


def _get_scene(scene_id: str, persona_id: str) -> tuple[dict, dict]:
    scene = SCENES.get(scene_id, SCENES["interview"])
    persona = scene["personas"].get(persona_id) or next(iter(scene["personas"].values()))
    return scene, persona


def _get_client() -> OpenAI:
    if not settings.dashscope_api_key:
        raise RuntimeError("DashScope API key is missing.")

    return OpenAI(
        api_key=settings.dashscope_api_key,
        base_url=settings.dashscope_base_url,
        timeout=settings.qwen_request_timeout_sec,
    )


def build_reply_prompt(
    *,
    scene_id: str,
    persona_id: str,
    difficulty: int,
    history: list[dict[str, str]],
    user_text: str,
) -> dict[str, object]:
    scene, persona = _get_scene(scene_id, persona_id)
    system_prompt = persona["system_prompt"].format(difficulty=difficulty)
    recent_history = history[-6:]

    messages: list[dict[str, str]] = [
        {
            "role": "system",
            "content": (
                f"{system_prompt}\n"
                f"Current scene: {scene['name']}.\n"
                f"If the learner is too brief, ask a short follow-up question.\n"
                f"Do not explain that you are an AI.\n"
                f"Keep the conversation natural and scenario-consistent."
            ),
        }
    ]
    messages.extend(recent_history)
    messages.append({"role": "user", "content": user_text})
    return {
        "scene_name": scene["name"],
        "persona_name": persona["name"],
        "messages": messages,
    }


def generate_reply(
    *,
    scene_id: str,
    persona_id: str,
    difficulty: int,
    history: list[dict[str, str]],
    user_text: str,
) -> str:
    prompt = build_reply_prompt(
        scene_id=scene_id,
        persona_id=persona_id,
        difficulty=difficulty,
        history=history,
        user_text=user_text,
    )
    try:
        client = _get_client()
        response = client.chat.completions.create(
            model=settings.qwen_chat_model,
            messages=prompt["messages"],
            extra_body={"enable_thinking": settings.qwen_enable_thinking},
            max_tokens=80,
            stream=False,
        )

        reply = response.choices[0].message.content or ""
        reply = reply.strip()
        if reply:
            return _normalize_reply(reply)
    except Exception:
        pass

    return _fallback_reply(scene_id=scene_id, persona_id=persona_id, user_text=user_text)


def _normalize_reply(reply: str) -> str:
    normalized = " ".join(reply.split())
    words = normalized.split()
    if len(words) > 40:
        normalized = " ".join(words[:40])
    return normalized


def _fallback_reply(*, scene_id: str, persona_id: str, user_text: str) -> str:
    _scene, persona = _get_scene(scene_id, persona_id)
    persona_name = persona["name"]
    lowered = user_text.lower()

    if scene_id == "interview":
        if "experience" in lowered:
            reply = f"{persona_name}: What result best shows your impact on that project?"
        else:
            reply = f"{persona_name}: Please share one project that best matches this role."
    elif scene_id == "restaurant":
        if "water" in lowered or "drink" in lowered:
            reply = f"{persona_name}: Great. Would you like anything else with your order?"
        else:
            reply = f"{persona_name}: Certainly. Would you like something to drink as well?"
    else:
        if "budget" in lowered or "launch" in lowered:
            reply = f"{persona_name}: What evidence supports that timeline and budget decision?"
        else:
            reply = f"{persona_name}: That is useful. What outcome do you expect from this idea?"

    return _normalize_reply(reply)
