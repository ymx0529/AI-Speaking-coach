from __future__ import annotations

from app.core.scenes import SCENES


def _get_scene(scene_id: str, persona_id: str) -> tuple[dict, dict]:
    scene = SCENES.get(scene_id, SCENES["interview"])
    persona = scene["personas"].get(persona_id) or next(iter(scene["personas"].values()))
    return scene, persona


def build_reply_prompt(
    *,
    scene_id: str,
    persona_id: str,
    difficulty: int,
    history: list[dict[str, str]],
    user_text: str,
) -> str:
    scene, persona = _get_scene(scene_id, persona_id)
    recent_history = history[-6:]
    history_text = " | ".join(f'{item["role"]}: {item["content"]}' for item in recent_history) or "No prior history."
    return (
        f'Scene: {scene["name"]}. '
        f'Persona: {persona["system_prompt"]}. '
        f'Difficulty: {difficulty}. '
        f'History: {history_text}. '
        f'Learner said: {user_text}'
    )


def generate_reply(
    *,
    scene_id: str,
    persona_id: str,
    difficulty: int,
    history: list[dict[str, str]],
    user_text: str,
) -> str:
    scene, persona = _get_scene(scene_id, persona_id)
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

    words = reply.split()
    if len(words) > 40:
        reply = " ".join(words[:40])
    return reply
