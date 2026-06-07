from __future__ import annotations

import re

from app.core.types import (
    PronScore,
    ShadowingAssessmentResponse,
    ShadowingItem,
    WordScore,
)
from app.modules.coach.store import TurnAnalysisRecord

_MAX_SHADOWING_ITEMS = 3
_MAX_TEXT_CHARS = 180
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")
_WORD_RE = re.compile(r"[A-Za-z][A-Za-z'-]*")
_SILENCE_TOKENS = {"sil", "sp", "silence"}


def build_shadowing_items(turns: list[TurnAnalysisRecord]) -> list[ShadowingItem]:
    """Pick short, useful expressions for after-class shadowing practice."""
    candidates: list[ShadowingItem] = []
    finished_turns = [turn for turn in turns if turn.status in {"analyzed", "failed"}]

    for index, turn in enumerate(finished_turns, start=1):
        sample = _best_sample_sentence(turn)
        if sample:
            candidates.append(
                ShadowingItem(
                    id=f"{turn.turn_id}-sample",
                    text=sample,
                    source_turn_id=turn.turn_id,
                    source="sample_answer",
                    focus_words=_focus_words(turn),
                    note=f"第 {index} 轮你的表达升级",
                )
            )

        user_sentence = _first_useful_sentence(turn.transcript)
        if user_sentence:
            candidates.append(
                ShadowingItem(
                    id=f"{turn.turn_id}-user",
                    text=user_sentence,
                    source_turn_id=turn.turn_id,
                    source="user_sentence",
                    focus_words=_focus_words(turn),
                    note=f"第 {index} 轮你的原句复练",
                )
            )

    return _dedupe_and_rank(candidates)[:_MAX_SHADOWING_ITEMS]


def build_assessment(
    *,
    item_id: str,
    target_text: str,
    pronunciation: PronScore | None,
) -> ShadowingAssessmentResponse:
    if pronunciation is None:
        return ShadowingAssessmentResponse(
            item_id=item_id,
            target_text=target_text,
            pronunciation=None,
            similarity_score=0.0,
            stress_score=0.0,
            intonation_score=0.0,
            liaison_score=0.0,
            pause_score=0.0,
            tips=["没有拿到发音评测结果，请检查评测 API 配置后重试。"],
        )

    weak_words = _weak_words(pronunciation.words)
    similarity = _clamp_score(pronunciation.overall)
    stress = _clamp_score(pronunciation.accuracy * 0.72 + pronunciation.overall * 0.28)
    intonation = _clamp_score(pronunciation.fluency * 0.72 + pronunciation.overall * 0.28)
    liaison = _clamp_score(
        pronunciation.fluency * 0.56
        + pronunciation.accuracy * 0.24
        + pronunciation.completeness * 0.20
    )
    pauses = _clamp_score(pronunciation.fluency * 0.62 + pronunciation.completeness * 0.38)

    return ShadowingAssessmentResponse(
        item_id=item_id,
        target_text=target_text,
        pronunciation=pronunciation,
        similarity_score=similarity,
        stress_score=stress,
        intonation_score=intonation,
        liaison_score=liaison,
        pause_score=pauses,
        weak_words=weak_words,
        tips=_tips(pronunciation, weak_words),
    )


def _best_sample_sentence(turn: TurnAnalysisRecord) -> str:
    sample = turn.sample_answer.strip() or _apply_corrections(turn.transcript, turn)
    if sample.strip().lower() == turn.transcript.strip().lower():
        return ""
    return _first_useful_sentence(sample)


def _apply_corrections(text: str, turn: TurnAnalysisRecord) -> str:
    sample = text
    for issue in turn.corrections:
        if issue.original and issue.corrected:
            sample = sample.replace(issue.original, issue.corrected)
    return sample


def _first_useful_sentence(text: str) -> str:
    normalized = " ".join(text.split())
    if not normalized:
        return ""
    for sentence in _SENTENCE_SPLIT_RE.split(normalized):
        trimmed = sentence.strip()
        if not trimmed:
            continue
        if len(trimmed) > _MAX_TEXT_CHARS:
            trimmed = _trim_to_words(trimmed, _MAX_TEXT_CHARS)
        if _is_useful_sentence(trimmed):
            return trimmed
    return ""


def _trim_to_words(text: str, max_chars: int) -> str:
    current = ""
    for word in text.split():
        candidate = f"{current} {word}".strip()
        if len(candidate) > max_chars:
            return current.rstrip(" ,;:")
        current = candidate
    return current


def _is_useful_sentence(text: str) -> bool:
    words = _WORD_RE.findall(text)
    return 4 <= len(words) <= 28


def _focus_words(turn: TurnAnalysisRecord) -> list[str]:
    if turn.pronunciation is None:
        return []
    return [
        word.word
        for word in _weak_words(turn.pronunciation.words)
    ][:3]


def _weak_words(words: list[WordScore]) -> list[WordScore]:
    return sorted(
        [
            word
            for word in words
            if word.word.strip().lower() not in _SILENCE_TOKENS
            and (word.accuracy_score < 80 or word.error_type != "None")
        ],
        key=lambda item: (item.accuracy_score, item.word.lower()),
    )[:5]


def _dedupe_and_rank(candidates: list[ShadowingItem]) -> list[ShadowingItem]:
    seen: set[str] = set()
    ranked: list[ShadowingItem] = []
    source_rank = {
        "sample_answer": 0,
        "user_sentence": 1,
    }
    for item in sorted(
        candidates,
        key=lambda candidate: (
            source_rank[candidate.source],
            -len(candidate.focus_words),
            len(candidate.text),
        ),
    ):
        normalized = item.text.lower().strip(" .!?")
        if normalized in seen:
            continue
        seen.add(normalized)
        ranked.append(item)
    return ranked


def _clamp_score(value: float) -> float:
    return round(max(0.0, min(100.0, value)), 1)


def _tips(pronunciation: PronScore, weak_words: list[WordScore]) -> list[str]:
    tips: list[str] = []
    if weak_words:
        words = "、".join(word.word for word in weak_words[:3])
        tips.append(f"先慢速复练 {words}，确保每个重读音节更清楚。")
    if pronunciation.fluency < 75:
        tips.append("整句先分成 2 段跟读，再连起来说，减少中间停顿。")
    if pronunciation.completeness < 80:
        tips.append("跟读时看着完整句子说完，避免漏词或提前收尾。")
    if not tips:
        tips.append("整体跟读稳定，可以尝试提高语速并保持语调起伏。")
    return tips
