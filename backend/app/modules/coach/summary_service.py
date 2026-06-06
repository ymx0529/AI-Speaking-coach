from __future__ import annotations

from app.core.types import SessionSummaryResponse, TurnRecord
from app.modules.coach import store as coach_store
from app.modules.coach.store import TurnAnalysisRecord


def build_summary(session_id: str) -> SessionSummaryResponse | None:
    """Aggregate all analyzed turns into a SessionSummaryResponse.

    Returns None if the session has no turns at all (→ 404).
    Always returns a stable response even if some turns failed or are still pending.
    """
    turns = coach_store.get_session_turns(session_id)
    if not turns:
        return None

    scene_id = turns[0].scene_id
    finished = [t for t in turns if t.status in ("analyzed", "failed")]

    pron_avg, accuracy_avg, fluency_avg, completeness_avg = _pron_averages(finished)
    grammar_score = _avg_scores([t.grammar_score for t in finished])
    expression_score = _avg_scores([t.expression_score for t in finished])
    vocabulary_score = _avg_scores([t.vocabulary_score for t in finished])
    corrections_count = sum(len(t.corrections) for t in finished)

    focus = _build_recommendations(pron_avg, grammar_score, corrections_count)
    feedback = _build_feedback(len(finished), pron_avg, corrections_count)

    turn_records = [_to_turn_record(t) for t in finished]

    return SessionSummaryResponse(
        session_id=session_id,
        scene_id=scene_id,
        total_turns=len(finished),
        pron_avg=pron_avg or 0.0,
        accuracy_avg=accuracy_avg or 0.0,
        fluency_avg=fluency_avg or 0.0,
        completeness_avg=completeness_avg or 0.0,
        grammar_score=grammar_score,
        expression_score=expression_score,
        vocabulary_score=vocabulary_score,
        corrections_count=corrections_count,
        ai_feedback=feedback,
        focus_recommendations=focus,
        turns=turn_records,
    )


# ── Private helpers ────────────────────────────────────────────────────────────

def _pron_averages(
    turns: list[TurnAnalysisRecord],
) -> tuple[float | None, float | None, float | None, float | None]:
    scored = [t for t in turns if t.pronunciation is not None]
    if not scored:
        return None, None, None, None
    n = len(scored)
    return (
        round(sum(t.pronunciation.overall for t in scored) / n, 1),       # type: ignore[union-attr]
        round(sum(t.pronunciation.accuracy for t in scored) / n, 1),      # type: ignore[union-attr]
        round(sum(t.pronunciation.fluency for t in scored) / n, 1),       # type: ignore[union-attr]
        round(sum(t.pronunciation.completeness for t in scored) / n, 1),  # type: ignore[union-attr]
    )


def _avg_scores(values: list[float | None]) -> float | None:
    valid = [v for v in values if v is not None]
    if not valid:
        return None
    return round(sum(valid) / len(valid), 1)


def _build_recommendations(
    pron_avg: float | None,
    grammar_score: float | None,
    corrections_count: int,
) -> list[str]:
    recs: list[str] = []
    if pron_avg is not None and pron_avg < 70:
        recs.append("重点练习单词发音准确度，可通过跟读练习提升")
    if grammar_score is not None and grammar_score < 70:
        recs.append("注意语法结构，尤其是动词时态和介词搭配")
    if corrections_count >= 3:
        recs.append("减少重复性语言错误，建议每次练习后复习纠错记录")
    if not recs:
        recs.append("整体表现良好，继续保持流利表达")
    return recs


def _build_feedback(total_turns: int, pron_avg: float | None, corrections_count: int) -> str:
    if total_turns == 0:
        return "本次练习暂无完成的对话轮次。"
    if pron_avg is None:
        return (
            f"完成了 {total_turns} 轮对话练习，语言纠错已记录 {corrections_count} 处。"
            "配置发音评测后可获得更全面的反馈。"
        )
    if pron_avg >= 80:
        return f"本次练习表现优秀！完成 {total_turns} 轮对话，发音综合得分 {pron_avg:.0f} 分，继续保持。"
    if pron_avg >= 60:
        return (
            f"本次完成 {total_turns} 轮对话，发音综合得分 {pron_avg:.0f} 分，"
            "有提升空间，建议重点练习低分词汇。"
        )
    return (
        f"本次完成 {total_turns} 轮对话，发音需要加强（得分 {pron_avg:.0f} 分），"
        "建议从基础音标入手，配合跟读练习。"
    )


def _to_turn_record(t: TurnAnalysisRecord) -> TurnRecord:
    from app.core.types import PronScore  # noqa: PLC0415
    return TurnRecord(
        turn_id=t.turn_id,
        user_text=t.transcript,
        ai_reply=t.assistant_reply_text,
        pron_score=t.pronunciation or PronScore(
            overall=0, accuracy=0, fluency=0, completeness=0
        ),
        corrections=t.corrections,
    )
