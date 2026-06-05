> 文件归属：`backend/app/modules/coach/**`、`backend/tests/coach/**`、`frontend/src/modules/coach/**`  
> 分支：`feat/coach`（从 tag `v0-skeleton` 拉出）  
不得修改 backend/app/core/、backend/app/main.py、frontend/src/core/、frontend/src/App.vue 等骨架文件。  
> **可用 `frontend/src/mock/events.ts` + `MOCK_SUMMARY_RESPONSE` 完全独立开发，无需等待 Dev A。**

---

任务清单（按顺序完成）

Phase B1 · 纠错引擎 + Mock 联调（Day 1 下午）

[] B1-1 创建 backend/app/modules/coach/correction_engine.py：LLM 语法/表达纠错
[] B1-2 创建 backend/app/modules/coach/session_accumulator.py：会话数据累积（内存）
[] B1-3 创建 backend/app/modules/coach/turn_handler.py：订阅 EventBus，处理每轮事件
[] B1-4 用 mock SpeakerTurnEvent 跑通完整 correction 流程（含写单测）
[] B1-5 写 backend/tests/coach/test_correction_engine.py
Phase B2 · 课后总结 + 前端（Day 2 全天）

[] B2-1 创建 backend/app/modules/coach/summary_engine.py：生成课后评分报告
[] B2-2 创建 backend/app/modules/coach/router.py：POST /api/sessions/{id}/summary
[] B2-3 实现 register.py（订阅 EventBus + 挂载路由）
[] B2-4 创建 frontend/src/modules/coach/useCoach.ts
[] B2-5 创建 frontend/src/modules/coach/CorrectionPanel.vue
[] B2-6 创建 frontend/src/modules/coach/SessionSummaryPanel.vue
[] B2-7 写 backend/tests/coach/test_summary_engine.py
---

后端文件详解

backend/app/modules/coach/correction_engine.py

"""LLM 语法/表达纠错：分析用户口语文本，返回最多 3 条最重要的问题"""
from __future__ import annotations
from openai import AsyncOpenAI
from app.core.config import settings
from app.core.types import CorrectionIssue

_client: AsyncOpenAI | None = None
_SYSTEM_PROMPT = """\
You are an English language coach analyzing a learner's spoken English.
Identify grammar, expression, and vocabulary issues.
Return a JSON array of issues (max 3, most important first).
Each issue: {"original": "...", "corrected": "...", "explanation": "...", "category": "grammar|expression|vocabulary"}
If no issues, return [].
Keep explanations under 15 words, in English.
Return ONLY the JSON array, no other text.\
"""


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url,
        )
    return _client


async def check_corrections(
    user_text: str,
    scene_id: str,
) -> list[CorrectionIssue]:
    """
    入参:
        user_text  str  用户本轮说话的完整识别文字（来自 SpeakerTurnEvent.user_text）
        scene_id   str  "interview" | "restaurant" | "meeting"（用于 prompt 上下文提示）
    出参:
        list[CorrectionIssue]  0–3 条纠错（无错误时返回空列表）
    异常:
        Exception  LLM 调用失败或 JSON 解析失败时向上抛出（调用方 catch 并静默处理）

    LLM Prompt 说明:
        - 系统提示见 _SYSTEM_PROMPT
        - 用户消息: "Scene: {scene_id}. Learner said: \"{user_text}\""
        - 解析模型返回的 JSON array
        - 过滤掉解析失败的条目

    性能说明:
        此函数在 EventBus handler 中以 asyncio.create_task 异步调用，
        不阻塞主对话流程，允许 0.5–1.5s 延迟。
    """
    import json

    if not user_text or len(user_text.strip()) < 5:
        return []

    user_prompt = f'Scene: {scene_id}. Learner said: "{user_text}"'

    client = _get_client()
    response = await client.chat.completions.create(
        model=settings.llm_model,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=300,
        temperature=0.1,        # 低温提高一致性
        response_format={"type": "json_object"} if "deepseek" not in settings.llm_base_url else None,
    )

    raw = response.choices[0].message.content or "[]"

    # 有些模型会把数组包在 json_object 里，兼容处理
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            # 取第一个 list 类型的值
            parsed = next((v for v in parsed.values() if isinstance(v, list)), [])
    except json.JSONDecodeError:
        return []

    issues: list[CorrectionIssue] = []
    for item in parsed[:3]:
        try:
            issues.append(CorrectionIssue(**item))
        except Exception:
            continue
    return issues

---

backend/app/modules/coach/session_accumulator.py

"""内存存储每个会话的逐轮数据，供课后总结使用"""
from __future__ import annotations
from dataclasses import dataclass, field
from app.core.types import PronScore, CorrectionIssue


@dataclass
class TurnData:
    turn_id: str
    user_text: str
    ai_reply: str
    pron_score: PronScore
    corrections: list[CorrectionIssue]


@dataclass
class SessionData:
    session_id: str
    scene_id: str
    turns: list[TurnData] = field(default_factory=list)


_sessions: dict[str, SessionData] = {}


def record_turn(
    session_id: str,
    scene_id: str,
    turn_id: str,
    user_text: str,
    ai_reply: str,
    pron_score: PronScore,
    corrections: list[CorrectionIssue],
) -> None:
    """
    入参:
        session_id   str
        scene_id     str                "interview" | "restaurant" | "meeting"
        turn_id      str                本轮 uuid（来自 SpeakerTurnEvent）
        user_text    str
        ai_reply     str
        pron_score   PronScore
        corrections  list[CorrectionIssue]  本轮的纠错结果（可能为空列表）
    出参: None
    副作用: 在内存中追加本轮数据；session 不存在则自动创建
    """
    if session_id not in _sessions:
        _sessions[session_id] = SessionData(session_id=session_id, scene_id=scene_id)
    _sessions[session_id].turns.append(TurnData(
        turn_id=turn_id,
        user_text=user_text,
        ai_reply=ai_reply,
        pron_score=pron_score,
        corrections=corrections,
    ))


def get_session_data(session_id: str) -> SessionData | None:
    """
    入参: session_id str
    出参: SessionData | None（不存在返回 None）
    """
    return _sessions.get(session_id)


def remove_session(session_id: str) -> None:
    _sessions.pop(session_id, None)

---

backend/app/modules/coach/turn_handler.py

"""EventBus 订阅handler：接收 Dev A 发布的每轮事件，异步处理纠错并推送 WS 消息"""
from __future__ import annotations
from app.core.types import SpeakerTurnEvent
from app.core import ws_hub
from app.modules.coach.correction_engine import check_corrections
from app.modules.coach.session_accumulator import record_turn


async def on_turn_event(event: SpeakerTurnEvent) -> None:
    """
    入参:
        event  SpeakerTurnEvent  来自 EventBus 的每轮事件
            .session_id   str
            .turn_id      str
            .user_text    str     用户识别文字
            .pron_score   PronScore
            .ai_reply     str     AI 回复文字
            .scene_id     str

    出参: None（async，fire-and-forget）

    执行逻辑：
        1. 调用 check_corrections(user_text, scene_id)
        2. 调用 record_turn(...)，存储本轮数据（含纠错结果）
        3. 若 corrections 非空，通过 ws_hub.send() 推送 correction 事件
           （此时 AI 回复已在播放，correction 事件叠加显示）

    性能说明:
        此 handler 在 asyncio.create_task 中运行，不阻塞主对话流程。
        预期延迟：LLM 纠错 0.5–1.5s，在 TTS 播放期间完成，用户无感。
    """
    try:
        corrections = await check_corrections(event.user_text, event.scene_id)
    except Exception:
        corrections = []

    record_turn(
        session_id=event.session_id,
        scene_id=event.scene_id,
        turn_id=event.turn_id,
        user_text=event.user_text,
        ai_reply=event.ai_reply,
        pron_score=event.pron_score,
        corrections=corrections,
    )

    if corrections:
        await ws_hub.send(event.session_id, {
            "type": "correction",
            "turn_id": event.turn_id,
            "issues": [c.model_dump() for c in corrections],
        })

---

backend/app/modules/coach/summary_engine.py

"""课后总结生成：聚合发音均分 + LLM 综合点评"""
from __future__ import annotations
from openai import AsyncOpenAI
from app.core.config import settings
from app.core.types import SessionSummaryResponse, TurnRecord
from app.modules.coach.session_accumulator import SessionData

_client: AsyncOpenAI | None = None
_SUMMARY_SYSTEM_PROMPT = """\
You are an English speaking coach. Given a student's practice session data, write a brief, encouraging summary in Chinese (100-150 characters).
Mention: the main pronunciation weakness, the main grammar pattern to improve, and one specific encouragement.
Return only the summary text, no other content.\
"""


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url,
        )
    return _client


async def generate_summary(session_data: SessionData) -> SessionSummaryResponse:
    """
    入参:
        session_data  SessionData  来自 session_accumulator.get_session_data()
            .session_id  str
            .scene_id    str
            .turns       list[TurnData]

    出参:
        SessionSummaryResponse
            .session_id        str
            .scene_id          str
            .total_turns       int
            .pron_avg          float  四维均分（所有轮次平均）
            .accuracy_avg      float
            .fluency_avg       float
            .completeness_avg  float
            .corrections_count int    全场累计纠错条数
            .ai_feedback       str    LLM 生成的中文综合点评
            .turns             list[TurnRecord]

    异常:
        LLM 调用失败时 ai_feedback 降级为固定文本，不影响评分数据返回

    实现步骤：
        1. 从 session_data.turns 聚合发音均分
        2. 统计全场 corrections_count
        3. 整理 turns 为 TurnRecord 列表
        4. 调用 LLM 生成 ai_feedback（见 _SUMMARY_SYSTEM_PROMPT）
        5. 组装并返回 SessionSummaryResponse
    """
    turns = session_data.turns
    if not turns:
        return SessionSummaryResponse(
            session_id=session_data.session_id,
            scene_id=session_data.scene_id,
            total_turns=0,
            pron_avg=0, accuracy_avg=0, fluency_avg=0, completeness_avg=0,
            corrections_count=0,
            ai_feedback="本次练习轮次为零，请尝试开始一次对话再结束。",
            turns=[],
        )

    n = len(turns)
    pron_avg = sum(t.pron_score.overall for t in turns) / n
    accuracy_avg = sum(t.pron_score.accuracy for t in turns) / n
    fluency_avg = sum(t.pron_score.fluency for t in turns) / n
    completeness_avg = sum(t.pron_score.completeness for t in turns) / n
    corrections_count = sum(len(t.corrections) for t in turns)

    turn_records = [
        TurnRecord(
            turn_id=t.turn_id,
            user_text=t.user_text,
            ai_reply=t.ai_reply,
            pron_score=t.pron_score,
            corrections=t.corrections,
        )
        for t in turns
    ]

    # 构建 LLM prompt 数据
    weakness_words = [
        w.word
        for t in turns
        for w in t.pron_score.words
        if w.error_type == "Mispronunciation"
    ][:5]
    all_errors = [
        c.original
        for t in turns
        for c in t.corrections
    ][:5]

    user_data_str = (
        f"场景: {session_data.scene_id}, 轮次: {n}, "
        f"发音均分: {pron_avg:.0f}, 流利度: {fluency_avg:.0f}, "
        f"主要发音错误词: {', '.join(weakness_words) or '无'}, "
        f"语法/表达错误样例: {', '.join(all_errors) or '无'}"
    )

    try:
        client = _get_client()
        resp = await client.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {"role": "system", "content": _SUMMARY_SYSTEM_PROMPT},
                {"role": "user", "content": user_data_str},
            ],
            max_tokens=200,
            temperature=0.6,
        )
        ai_feedback = resp.choices[0].message.content or ""
    except Exception:
        ai_feedback = f"本次练习完成 {n} 轮对话，发音综合评分 {pron_avg:.0f}/100，继续加油！"

    return SessionSummaryResponse(
        session_id=session_data.session_id,
        scene_id=session_data.scene_id,
        total_turns=n,
        pron_avg=round(pron_avg, 1),
        accuracy_avg=round(accuracy_avg, 1),
        fluency_avg=round(fluency_avg, 1),
        completeness_avg=round(completeness_avg, 1),
        corrections_count=corrections_count,
        ai_feedback=ai_feedback,
        turns=turn_records,
    )

---

backend/app/modules/coach/router.py

from fastapi import APIRouter, HTTPException
from app.core.types import SessionSummaryResponse
from app.modules.coach.session_accumulator import get_session_data
from app.modules.coach.summary_engine import generate_summary

router = APIRouter()


@router.post("/sessions/{session_id}/summary", response_model=SessionSummaryResponse)
async def get_summary(session_id: str):
    """
    入参（路径参数）:
        session_id  str  会话 uuid4
    出参:
        SessionSummaryResponse  （见 core/types.py）
    HTTP 状态:
        200  正常返回
        404  session_id 不存在（会话已结束或从未创建）

    调用时机：前端在用户点击"结束"后，store.phase 变为 summary 时触发。
    """
    session_data = get_session_data(session_id)
    if session_data is None:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    return await generate_summary(session_data)

---

backend/app/modules/coach/register.py（最终实现）

from fastapi import FastAPI


def register_coach(app: FastAPI) -> None:
    from app.core import event_bus
    from app.modules.coach.turn_handler import on_turn_event
    from app.modules.coach.router import router as coach_router

    event_bus.subscribe(on_turn_event)
    app.include_router(coach_router, prefix="/api")

---

前端文件详解

frontend/src/modules/coach/useCoach.ts

import { ref, onUnmounted } from 'vue'
import axios from 'axios'
import { useAppStore } from '@/core/store'
import { ws } from '@/core/ws'
import type { ServerMsg, CorrectionIssue, SessionSummaryResponse } from '@/core/types'

export function useCoach() {
  /**
   * 出参（响应式 state + actions）：
   *
   * state:
   *   summary   Ref<SessionSummaryResponse | null>  课后总结数据（fetchSummary 后填充）
   *
   * actions:
   *   fetchSummary(sessionId)  调用 POST /api/sessions/{id}/summary，填充 store.summary
   *
   * 副作用（mounted 时自动）：
   *   - 订阅 WS correction 事件，写入 store.currentCorrections
   */
  const store = useAppStore()
  const summary = ref<SessionSummaryResponse | null>(null)

  const unsubscribe = ws.onMessage((msg: ServerMsg) => {
    if (msg.type === 'correction') {
      store.currentCorrections = msg.issues
    }
  })

  async function fetchSummary(sessionId: string): Promise<void> {
    /**
     * 入参: sessionId  str
     * 出参: Promise<void>
     * 副作用:
     *   - 调用 POST /api/sessions/{sessionId}/summary
     *   - 成功后设置 summary.value + store.summary
     * 异常:
     *   - HTTP 404：session 不存在，summary.value 保持 null
     *   - 其他网络错误：向上抛出
     */
    const resp = await axios.post<SessionSummaryResponse>(
      `http://localhost:8000/api/sessions/${sessionId}/summary`
    )
    summary.value = resp.data
    store.summary = resp.data
  }

  onUnmounted(() => {
    unsubscribe()
  })

  return { summary, fetchSummary }
}

---

frontend/src/modules/coach/CorrectionPanel.vue

<template>
  <!--
    展示当前轮次的语法/表达纠错列表。
    由 ConversationRoom.vue 通过 <slot name="correction"> 挂载。
    
    Props:
      无（直接读 store.currentCorrections）
    
    展示逻辑：
      - 有纠错才显示，无纠错不渲染
      - 每条纠错：划线原文 → 正确写法 + 解释
      - 分类图标：grammar=📖, expression=💬, vocabulary=📝
  -->
  <div v-if="store.currentCorrections.length > 0" class="bg-amber-50 border border-amber-200 rounded-xl p-3">
    <h4 class="text-xs font-semibold text-amber-700 mb-2">💡 本轮纠错建议</h4>
    <div
      v-for="(issue, i) in store.currentCorrections"
      :key="i"
      class="flex gap-2 text-sm mb-1 last:mb-0"
    >
      <span class="text-lg leading-none">{{ categoryIcon[issue.category] }}</span>
      <div>
        <span class="line-through text-red-400 mr-1">{{ issue.original }}</span>
        <span class="text-green-700 font-medium mr-1">→ {{ issue.corrected }}</span>
        <span class="text-gray-500 text-xs">{{ issue.explanation }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useAppStore } from '@/core/store'

const store = useAppStore()
const categoryIcon: Record<string, string> = {
  grammar: '📖',
  expression: '💬',
  vocabulary: '📝',
}
</script>

---

frontend/src/modules/coach/SessionSummaryPanel.vue

<template>
  <div class="max-w-2xl mx-auto p-6">
    <h2 class="text-xl font-bold mb-4 text-center">练习结束 🎉</h2>

    <!-- 加载中 -->
    <div v-if="loading" class="text-center text-gray-400 py-8">生成总结中...</div>

    <template v-else-if="data">
      <!-- 四维评分卡片 -->
      <div class="grid grid-cols-2 gap-3 mb-4">
        <div
          v-for="(val, label) in scoreCards"
          :key="label"
          class="bg-white rounded-xl p-4 shadow-sm text-center"
        >
          <div class="text-2xl font-bold" :class="scoreColor(val)">{{ Math.round(val) }}</div>
          <div class="text-xs text-gray-500 mt-1">{{ label }}</div>
        </div>
      </div>

      <!-- AI 综合点评 -->
      <div class="bg-indigo-50 rounded-xl p-4 mb-4">
        <h4 class="text-sm font-semibold text-indigo-700 mb-1">教练点评</h4>
        <p class="text-sm text-gray-700 leading-relaxed">{{ data.ai_feedback }}</p>
      </div>

      <!-- 纠错统计 -->
      <div class="text-sm text-gray-500 text-center mb-4">
        本次共 {{ data.total_turns }} 轮对话，累计纠错 {{ data.corrections_count }} 条
      </div>

      <!-- 逐轮回顾 -->
      <div class="space-y-2">
        <h4 class="text-sm font-semibold text-gray-600">逐轮回顾</h4>
        <div
          v-for="(turn, i) in data.turns"
          :key="turn.turn_id"
          class="bg-white rounded-lg p-3 shadow-sm text-sm"
        >
          <div class="flex justify-between items-center mb-1">
            <span class="font-medium text-gray-700">第 {{ i + 1 }} 轮</span>
            <span class="text-xs font-mono" :class="scoreColor(turn.pron_score.overall)">
              {{ Math.round(turn.pron_score.overall) }}分
            </span>
          </div>
          <div class="text-gray-600 mb-1">你说：{{ turn.user_text }}</div>
          <div
            v-if="turn.corrections.length"
            class="text-xs text-amber-600"
          >
            纠错: {{ turn.corrections.map(c => c.original + ' → ' + c.corrected).join(' / ') }}
          </div>
        </div>
      </div>

      <!-- 重新练习 -->
      <button
        class="w-full mt-4 py-3 bg-indigo-600 text-white rounded-xl font-bold"
        @click="store.phase = 'scene_select'"
      >
        再练一次
      </button>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useAppStore } from '@/core/store'
import { useCoach } from './useCoach'
import type { SessionSummaryResponse } from '@/core/types'

const props = defineProps<{ sessionId: string }>()
const store = useAppStore()
const { summary, fetchSummary } = useCoach()
const loading = ref(true)
const data = computed(() => summary.value)

const scoreCards = computed(() =>
  data.value
    ? {
        '发音准确度': data.value.accuracy_avg,
        '流利度': data.value.fluency_avg,
        '完整度': data.value.completeness_avg,
        '综合评分': data.value.pron_avg,
      }
    : {}
)

function scoreColor(val: number) {
  if (val >= 80) return 'text-green-600'
  if (val >= 60) return 'text-yellow-600'
  return 'text-red-500'
}

onMounted(async () => {
  await fetchSummary(props.sessionId)
  loading.value = false
})
</script>

---

CorrectionPanel 集成约定

> `App.vue` 属于 Skeleton，Dev B 不能直接改。

最终约定是：

- `App.vue` 在 Phase 0 已经预埋 `<ConversationRoom><template #correction><CorrectionPanel /></template></ConversationRoom>`
- Dev A 在 `ConversationRoom.vue` 中保证存在 `<slot name="correction" />`
- Dev B 只负责实现 `CorrectionPanel.vue` 本身，不改 Skeleton 文件

这样联调阶段不需要再补 `App.vue`，也不破坏“中心文件冻结”的规则。

---

Dev B Mock 独立开发指南

Dev B 在 Dev A 完成之前可以：

1. Mock SpeakerTurnEvent 测试 turn_handler：
# backend/tests/coach/test_turn_handler.py
import pytest
import asyncio
from app.core.types import SpeakerTurnEvent, PronScore
from app.modules.coach.turn_handler import on_turn_event

MOCK_EVENT = SpeakerTurnEvent(
    session_id="test-session",
    turn_id="test-turn-1",
    user_text="I am interest in the position and I have three year experience.",
    pron_score=PronScore(overall=71, accuracy=66, fluency=78, completeness=90),
    ai_reply="Tell me more about your experience.",
    scene_id="interview",
)

@pytest.mark.asyncio
async def test_turn_handler_runs():
    """turn_handler 不抛异常，且存储了本轮数据"""
    from app.modules.coach.session_accumulator import get_session_data
    await on_turn_event(MOCK_EVENT)
    await asyncio.sleep(0.1)  # 等待 create_task 完成
    data = get_session_data("test-session")
    assert data is not None
    assert len(data.turns) == 1

2. Mock summary 测试前端 SessionSummaryPanel：

在 frontend/src/mock/events.ts 中已有 MOCK_SUMMARY_RESPONSE。  
在 useCoach.ts 中，若检测到 sessionId === "mock-session"，直接返回 mock 数据：

// 开发阶段 mock 分支（联调后删除）
if (sessionId === 'mock-session') {
  const { MOCK_SUMMARY_RESPONSE } = await import('@/mock/events')
  summary.value = MOCK_SUMMARY_RESPONSE as SessionSummaryResponse
  store.summary = MOCK_SUMMARY_RESPONSE as SessionSummaryResponse
  return
}

---

Dev B 测试用例

backend/tests/coach/test_correction_engine.py

import pytest
from unittest.mock import patch, AsyncMock
from app.modules.coach.correction_engine import check_corrections


@pytest.mark.asyncio
@patch("app.modules.coach.correction_engine._get_client")
async def test_grammar_error_detected(mock_get_client):
    """有语法错误时，返回至少一条纠错"""
    mock_client = AsyncMock()
    mock_get_client.return_value = mock_client
    mock_client.chat.completions.create.return_value = AsyncMock(
        choices=[AsyncMock(message=AsyncMock(content='[{"original":"interest","corrected":"interested","explanation":"adjective form required","category":"grammar"}]'))]
    )
    result = await check_corrections("I am interest in the position.", "interview")
    assert len(result) == 1
    assert result[0].category == "grammar"


@pytest.mark.asyncio
async def test_empty_text_returns_empty():
    """空文本或极短文本不调用 LLM，直接返回空"""
    result = await check_corrections("", "interview")
    assert result == []

backend/tests/coach/test_summary_engine.py

import pytest
from unittest.mock import patch, AsyncMock
from app.modules.coach.session_accumulator import SessionData, TurnData
from app.modules.coach.summary_engine import generate_summary
from app.core.types import PronScore


def _make_session_data(n_turns: int = 3) -> SessionData:
    turns = [
        TurnData(
            turn_id=f"turn-{i}",
            user_text=f"Hello turn {i}",
            ai_reply=f"AI reply {i}",
            pron_score=PronScore(overall=70 + i, accuracy=65, fluency=75, completeness=90),
            corrections=[],
        )
        for i in range(n_turns)
    ]
    return SessionData(session_id="test", scene_id="interview", turns=turns)


@pytest.mark.asyncio
@patch("app.modules.coach.summary_engine._get_client")
async def test_summary_scores(mock_client):
    """聚合均分正确"""
    mock_client.return_value.chat.completions.create = AsyncMock(
        return_value=AsyncMock(choices=[AsyncMock(message=AsyncMock(content="很好的练习！"))])
    )
    data = _make_session_data(3)
    summary = await generate_summary(data)
    assert summary.total_turns == 3
    assert abs(summary.pron_avg - 71.0) < 0.1   # (70+71+72)/3
    assert summary.ai_feedback == "很好的练习！"
