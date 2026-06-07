import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

pytestmark = pytest.mark.anyio

from app.modules.coach import correction_service


async def test_empty_transcript_returns_empty():
    issues, g, e, v, sample = await correction_service.analyse("", "reply")
    assert issues == []
    assert g is None
    assert sample == ""


async def test_missing_llm_key_returns_empty(monkeypatch):
    monkeypatch.setattr("app.modules.coach.correction_service.settings.llm_api_key", "")
    monkeypatch.setattr("app.modules.coach.correction_service.settings.dashscope_api_key", "")
    issues, g, e, v, sample = await correction_service.analyse("I want order pasta", "Sure!")
    assert issues == []
    assert sample == "I want order pasta"


async def test_uses_dashscope_when_custom_llm_key_missing(monkeypatch):
    expected = ([], 90.0, 91.0, 92.0, "I would like to order pasta.")
    call_mock = AsyncMock(return_value=expected)
    monkeypatch.setattr("app.modules.coach.correction_service.settings.llm_api_key", "")
    monkeypatch.setattr("app.modules.coach.correction_service.settings.dashscope_api_key", "dashscope-key")
    monkeypatch.setattr("app.modules.coach.correction_service.settings.dashscope_base_url", "https://dashscope")
    monkeypatch.setattr("app.modules.coach.correction_service.settings.qwen_chat_model", "qwen-test")
    monkeypatch.setattr("app.modules.coach.correction_service._call_llm", call_mock)

    result = await correction_service.analyse("I want order pasta", "Sure!")

    assert result == expected
    llm_config = call_mock.await_args.kwargs["llm_config"]
    assert llm_config["provider"] == correction_service._PROVIDER_DASHSCOPE
    assert llm_config["api_key"] == "dashscope-key"
    assert llm_config["base_url"] == "https://dashscope"
    assert llm_config["model"] == "qwen-test"


async def test_llm_exception_returns_empty(monkeypatch):
    monkeypatch.setattr("app.modules.coach.correction_service.settings.llm_api_key", "fake")
    with patch(
        "app.modules.coach.correction_service._call_llm",
        new=AsyncMock(side_effect=RuntimeError("LLM down")),
    ):
        issues, g, e, v, sample = await correction_service.analyse("Hello", "Hi")
    assert issues == []
    assert g is None
    assert sample == "Hello"


def test_parse_valid_response():
    raw = json.dumps({
        "issues": [
            {
                "original": "I want order",
                "corrected": "I want to order",
                "explanation": "Use infinitive after want.",
                "category": "grammar",
                "severity": "high",
            }
        ],
        "grammar_score": 72,
        "expression_score": 80,
        "vocabulary_score": 85,
        "sample_answer": "I would like to order pasta.",
    })
    issues, g, e, v, sample = correction_service._parse_response(raw, transcript="I want order pasta.")
    assert len(issues) == 1
    assert issues[0].severity == "high"
    assert issues[0].category == "grammar"
    assert g == 72.0
    assert e == 80.0
    assert v == 85.0
    assert sample == "I would like to order pasta."


def test_parse_rejects_expanded_sample_answer():
    raw = json.dumps({
        "issues": [],
        "grammar_score": 92,
        "expression_score": 90,
        "vocabulary_score": 91,
        "sample_answer": (
            "Hello, my name is Strong. I recently led a project to streamline "
            "our team's workflow, which reduced processing time by 20%."
        ),
    })

    issues, g, e, v, sample = correction_service._parse_response(
        raw,
        transcript="Hello, my name is Strong.",
    )

    assert issues == []
    assert g == 92.0
    assert e == 90.0
    assert v == 91.0
    assert sample == "Hello, my name is Strong."


def test_parse_non_json_returns_empty():
    issues, g, e, v, sample = correction_service._parse_response("not json at all", transcript="Hello")
    assert issues == []
    assert g is None
    assert sample == "Hello"


def test_parse_invalid_structure_safe_defaults():
    raw = json.dumps({
        "issues": [
            {
                "original": "bad",
                "corrected": "good",
                "explanation": "fix it",
                "category": "UNKNOWN_CATEGORY",
                "severity": "UNKNOWN",
            }
        ],
        "grammar_score": "not-a-number",
    })
    issues, g, e, v, sample = correction_service._parse_response(raw, transcript="bad")
    assert issues[0].category == "grammar"   # fallback
    assert issues[0].severity == "medium"    # fallback
    assert g is None                         # unparseable score
    assert sample == "good"


def test_parse_caps_at_max_issues():
    many = [
        {"original": f"x{i}", "corrected": f"y{i}", "explanation": "e",
         "category": "grammar", "severity": "low"}
        for i in range(10)
    ]
    raw = json.dumps({"issues": many, "grammar_score": 90})
    issues, *_ = correction_service._parse_response(raw)
    assert len(issues) == correction_service._MAX_ISSUES


def test_build_ws_payload():
    from app.core.types import CorrectionIssue
    issues = [
        CorrectionIssue(
            original="I want order",
            corrected="I want to order",
            explanation="Use infinitive.",
            category="grammar",
            severity="high",
        )
    ]
    payload = correction_service.build_ws_payload(
        "sess-1",
        "turn-1",
        issues,
        grammar_score=70,
        expression_score=80,
        vocabulary_score=90,
        sample_answer="I want to order pasta.",
    )
    assert payload["type"] == "analysis.correction"
    assert payload["session_id"] == "sess-1"
    assert payload["turn_id"] == "turn-1"
    assert payload["issues"][0]["severity"] == "high"
    assert payload["grammar_score"] == 70
    assert payload["sample_answer"] == "I want to order pasta."


def test_severity_score_clamped():
    assert correction_service._safe_score(150) == 100.0
    assert correction_service._safe_score(-10) == 0.0
    assert correction_service._safe_score(None) is None
