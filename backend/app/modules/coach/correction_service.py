from __future__ import annotations

import json
import logging
from typing import Any

from app.core.config import settings
from app.core.types import CorrectionIssue

logger = logging.getLogger(__name__)

_MAX_ISSUES = 5
_VALID_CATEGORIES = {"grammar", "expression", "vocabulary"}
_VALID_SEVERITIES = {"high", "medium", "low"}
_PROVIDER_CUSTOM = "custom"
_PROVIDER_DASHSCOPE = "dashscope"

_SYSTEM_PROMPT = """\
You are an English speaking coach. Analyze the student's spoken English and return a JSON object.

Return ONLY valid JSON with these fields:
{
  "issues": [
    {
      "original": "<problematic phrase>",
      "corrected": "<corrected version>",
      "explanation": "<one-sentence explanation>",
      "category": "<grammar|expression|vocabulary>",
      "severity": "<high|medium|low>"
    }
  ],
  "grammar_score": <0-100>,
  "expression_score": <0-100>,
  "vocabulary_score": <0-100>,
  "sample_answer": "<the corrected version of the student's transcript only>"
}

Rules:
- Analyze only the speech recognition transcript provided by the student.
- Return at most 5 issues, focusing on the most important ones.
- Cover grammar, expression, and vocabulary issues when they are present.
- Do not invent problems. If a category has no issue, simply omit that category from issues.
- The sample_answer must be a corrected/standard version of the student's own words only.
- Do not answer the AI, continue the conversation, add examples, invent facts, or expand beyond what the student said.
- If the transcript is already natural, sample_answer must repeat the transcript with only light punctuation/capitalization cleanup.
- If speech is correct, return empty issues array with high scores (85-100).
- No explanation outside the JSON object.\
"""


async def analyse(
    transcript: str,
    assistant_reply: str,
) -> tuple[list[CorrectionIssue], float | None, float | None, float | None, str]:
    """Analyse transcript for grammar/expression/vocabulary issues via LLM."""
    if not transcript.strip():
        return [], None, None, None, ""

    llm_config = _resolve_llm_config()
    if llm_config is None:
        logger.warning("No correction LLM key set - skipping correction analysis")
        return [], None, None, None, transcript.strip()

    try:
        return await _call_llm(transcript, assistant_reply, llm_config=llm_config)
    except Exception as exc:
        logger.error("Correction analysis failed: %s", exc)
        return [], None, None, None, transcript.strip()


def _resolve_llm_config() -> dict[str, str] | None:
    if settings.llm_api_key:
        return {
            "provider": _PROVIDER_CUSTOM,
            "api_key": settings.llm_api_key,
            "base_url": settings.llm_base_url,
            "model": settings.llm_model,
        }
    if settings.dashscope_api_key:
        return {
            "provider": _PROVIDER_DASHSCOPE,
            "api_key": settings.dashscope_api_key,
            "base_url": settings.dashscope_base_url,
            "model": settings.qwen_chat_model,
        }
    return None


async def _call_llm(
    transcript: str,
    _assistant_reply: str,
    *,
    llm_config: dict[str, str] | None = None,
) -> tuple[list[CorrectionIssue], float | None, float | None, float | None, str]:
    try:
        from openai import AsyncOpenAI  # noqa: PLC0415
    except ImportError:
        logger.warning("openai package not installed - skipping correction")
        return [], None, None, None, transcript.strip()

    llm_config = llm_config or _resolve_llm_config()
    if llm_config is None:
        return [], None, None, None, transcript.strip()

    client = AsyncOpenAI(
        api_key=llm_config["api_key"],
        base_url=llm_config["base_url"],
    )

    user_prompt = (
        f'Speech recognition transcript: "{transcript}"\n\n'
        "Correct only this transcript. Do not use any surrounding conversation to add new content."
    )

    request_kwargs: dict[str, Any] = {
        "model": llm_config["model"],
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.2,
        "max_tokens": 500,
    }
    if llm_config["provider"] == _PROVIDER_DASHSCOPE:
        request_kwargs["extra_body"] = {"enable_thinking": False}

    response = await client.chat.completions.create(**request_kwargs)
    raw = response.choices[0].message.content or ""
    return _parse_response(raw, transcript=transcript)


def _parse_response(
    raw: str,
    transcript: str = "",
) -> tuple[list[CorrectionIssue], float | None, float | None, float | None, str]:
    try:
        data: dict[str, Any] = json.loads(raw.strip())
    except json.JSONDecodeError:
        logger.warning("LLM returned non-JSON: %s", raw[:200])
        return [], None, None, None, transcript.strip()

    issues = _parse_issues(data.get("issues", []))
    grammar_score = _safe_score(data.get("grammar_score"))
    expression_score = _safe_score(data.get("expression_score"))
    vocabulary_score = _safe_score(data.get("vocabulary_score"))
    sample_answer = _select_sample_answer(
        transcript=transcript,
        issues=issues,
        raw_sample=data.get("sample_answer"),
    )

    return issues, grammar_score, expression_score, vocabulary_score, sample_answer


def _parse_issues(raw_issues: Any) -> list[CorrectionIssue]:
    if not isinstance(raw_issues, list):
        return []
    result: list[CorrectionIssue] = []
    for item in raw_issues[:_MAX_ISSUES]:
        if not isinstance(item, dict):
            continue
        try:
            result.append(
                CorrectionIssue(
                    original=str(item.get("original", "")),
                    corrected=str(item.get("corrected", "")),
                    explanation=str(item.get("explanation", "")),
                    category=item.get("category", "grammar")
                    if item.get("category") in _VALID_CATEGORIES
                    else "grammar",
                    severity=item.get("severity", "medium")
                    if item.get("severity") in _VALID_SEVERITIES
                    else "medium",
                )
            )
        except Exception:
            continue
    return result


def _safe_score(value: Any) -> float | None:
    try:
        score = float(value)
        return round(max(0.0, min(100.0, score)), 1)
    except (TypeError, ValueError):
        return None


def _safe_sample_answer(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return " ".join(value.split())[:600]


def _select_sample_answer(
    *,
    transcript: str,
    issues: list[CorrectionIssue],
    raw_sample: Any,
) -> str:
    fallback = _build_sample_answer(transcript, issues)
    sample = _safe_sample_answer(raw_sample)
    if not sample:
        return fallback
    if _looks_expanded_beyond_transcript(transcript, sample):
        return fallback
    return sample


def _looks_expanded_beyond_transcript(transcript: str, sample: str) -> bool:
    source_words = transcript.split()
    sample_words = sample.split()
    if not source_words:
        return bool(sample_words)

    max_allowed_words = max(len(source_words) + 6, int(len(source_words) * 1.8))
    if len(sample_words) > max_allowed_words:
        return True

    max_allowed_chars = max(len(transcript) + 60, int(len(transcript) * 2.2))
    return len(sample) > max_allowed_chars


def _build_sample_answer(transcript: str, issues: list[CorrectionIssue]) -> str:
    sample = transcript.strip()
    for issue in issues:
        if issue.original and issue.corrected:
            sample = sample.replace(issue.original, issue.corrected)
    return " ".join(sample.split())


def build_ws_payload(
    session_id: str,
    turn_id: str,
    issues: list[CorrectionIssue],
    *,
    grammar_score: float | None = None,
    expression_score: float | None = None,
    vocabulary_score: float | None = None,
    sample_answer: str = "",
) -> dict:
    return {
        "type": "analysis.correction",
        "session_id": session_id,
        "turn_id": turn_id,
        "issues": [issue.model_dump() for issue in issues],
        "grammar_score": grammar_score,
        "expression_score": expression_score,
        "vocabulary_score": vocabulary_score,
        "sample_answer": sample_answer,
    }
