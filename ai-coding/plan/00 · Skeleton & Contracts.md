全员一起做，完成后打 tag v0-skeleton，任何人不再改本范围内的文件。

> 重要：`App.vue` 中的 `CorrectionPanel` 插槽必须在 Phase 0 一次性预埋完成，联调阶段不再补骨架。

---

Phase 0 任务清单

[] 创建 GitHub 仓库 speak-coach，初始化 main 分支
[] 创建目录结构（见下方 Tree）
[] 写入 .gitignore + .env.example
[] 写入 PROTOCOL.md（WS 事件契约，完整内容见本文件下方）
[] 写入 backend/pyproject.toml
[] 写入 backend/app/core/config.py
[] 写入 backend/app/core/types.py
[] 写入 backend/app/core/event_bus.py
[] 写入 backend/app/core/ws_hub.py
[] 写入 backend/app/core/scenes.py
[] 写入 backend/app/main.py
[] 创建模块 stub 与可编译占位组件（见本文末尾）
[] 写入 frontend/package.json + vite.config.ts
[] 写入 frontend/src/core/types.ts
[] 写入 frontend/src/core/ws.ts
[] 写入 frontend/src/core/store.ts
[] 写入 frontend/src/core/scenes.ts
[] 写入 frontend/src/mock/events.ts
[] 写入 frontend/src/App.vue + main.ts + index.css
[] 验证：uvicorn 启动 + vite dev 启动 + 浏览器 WS 可连接
[] PR 合入 main → tag v0-skeleton
[] 两人分别拉 feat/conversation + feat/coach 分支
---

目录结构（完整 Tree）

speak-coach/
├── .env.example
├── .gitignore
├── PROTOCOL.md                    ← WS 事件契约文档
├── README.md
├── backend/
│   ├── pyproject.toml
│   └── app/
│       ├── main.py                ← FastAPI 入口（Skeleton 冻结）
│       └── core/
│           ├── config.py          ← 环境变量（Skeleton 冻结）
│           ├── types.py           ← 共享 Pydantic 类型（Skeleton 冻结）
│           ├── event_bus.py       ← 进程内事件总线（Skeleton 冻结）
│           ├── ws_hub.py          ← WS 连接注册表（Skeleton 冻结）
│           └── scenes.py          ← 场景/人设配置（Skeleton 冻结）
│       └── modules/
│           ├── conversation/      ← Dev A 独占（Phase 0 只建空目录+stub）
│           │   ├── __init__.py
│           │   └── register.py    ← stub（A 实现）
│           └── coach/             ← Dev B 独占（Phase 0 只建空目录+stub）
│               ├── __init__.py
│               └── register.py    ← stub（B 实现）
├── tests/
│   ├── conversation/              ← Dev A 测试目录
│   └── coach/                     ← Dev B 测试目录
└── frontend/
    ├── package.json
    ├── vite.config.ts
    ├── tailwind.config.js
    ├── postcss.config.js
    ├── index.html
    └── src/
        ├── main.ts                ← Vue 入口（Skeleton 冻结）
        ├── App.vue                ← 根组件路由（Skeleton 冻结）
        ├── index.css              ← Tailwind 指令（Skeleton 冻结）
        ├── core/
        │   ├── types.ts           ← 共享 TS 类型（Skeleton 冻结）
        │   ├── ws.ts              ← WS 客户端（Skeleton 冻结）
        │   ├── store.ts           ← Pinia 全局状态（Skeleton 冻结）
        │   └── scenes.ts          ← 场景配置（Skeleton 冻结）
        ├── mock/
        │   └── events.ts          ← Mock WS 事件（Skeleton 冻结，只读）
        └── modules/
            ├── conversation/      ← Dev A 独占（Phase 0 建可编译占位组件）
            └── coach/             ← Dev B 独占（Phase 0 建可编译占位组件）

---

PROTOCOL.md（完整内容——直接复制到根目录）


SpeakCoach WebSocket 协议契约 v1

本文件一旦 tag v0-skeleton 后冻结。修改需单开微 PR，两人均 approve。

连接

URL: ws://{host}/ws/session/{session_id}

session_id 由前端生成（uuid v4）。连接建立后立即发送 session_start。

客户端 → 服务端消息

session_start
{
  "type": "session_start",
  "scene_id": "interview",
  "difficulty": 1,
  "persona_id": "strict_interviewer"
}
- scene_id: "interview" | "restaurant" | "meeting"
- difficulty: 1 | 2 | 3
- persona_id: 见 scenes.py 配置
audio_chunk
{
  "type": "audio_chunk",
  "data": "<base64 encoded webm/opus bytes>",
  "seq": 0
}
- seq 从 0 递增
- 前端按住录音期间持续发送
audio_end
{
  "type": "audio_end",
  "seq_count": 12
}
- 前端松开录音后发送
- seq_count = 总共发出的 audio_chunk 数量
session_end
{ "type": "session_end" }

服务端 → 客户端消息

asr_partial（STT 流式中间结果，可选）
{ "type": "asr_partial", "text": "I am inter..." }

asr_final
{
  "type": "asr_final",
  "turn_id": "uuid",
  "text": "I am interested in the position.",
  "duration_ms": 2400
}

pron_score
{
  "type": "pron_score",
  "turn_id": "uuid",
  "overall": 72.5,
  "accuracy": 68.0,
  "fluency": 78.3,
  "completeness": 92.0,
  "words": [
    { "word": "interested", "accuracy_score": 58.2, "error_type": "Mispronunciation" }
  ]
}
- error_type: "None" | "Omission" | "Insertion" | "Mispronunciation"
reply_text
{
  "type": "reply_text",
  "turn_id": "uuid",
  "text": "That's great. Can you tell me more about your relevant experience?"
}

reply_audio
{
  "type": "reply_audio",
  "turn_id": "uuid",
  "data": "<base64 mp3 bytes>"
}

correction（异步，在 reply_audio 之后推送）
{
  "type": "correction",
  "turn_id": "uuid",
  "issues": [
    {
      "original": "I am interest in",
      "corrected": "I am interested in",
      "explanation": "\"interested\" is the adjective form needed here",
      "category": "grammar"
    }
  ]
}
- issues 可为空数组 []
- category: "grammar" | "expression" | "vocabulary"
turn_end
{ "type": "turn_end", "turn_id": "uuid" }

error
{ "type": "error", "code": "ASR_FAILED", "message": "Azure STT returned no result" }

---

## File: .env.example

```dotenv
AZURE_SPEECH_KEY=
AZURE_SPEECH_REGION=eastasia
LLM_API_KEY=
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_MODEL=deepseek-chat
CORS_ORIGIN=http://localhost:5173

---

File: backend/pyproject.toml

[project]
name = "speak-coach-backend"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.111",
    "uvicorn[standard]>=0.29",
    "pydantic>=2.0",
    "pydantic-settings>=2.0",
    "azure-cognitiveservices-speech>=1.37",
    "openai>=1.30",
    "pydub>=0.25",
    "python-multipart>=0.0.9",
    "websockets>=12",
    "python-dotenv>=1.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.pytest.ini_options]
asyncio_mode = "auto"

安装命令：uv pip install -e ".[dev]" 或 pip install -e .

---

File: backend/app/core/config.py

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    azure_speech_key: str = ""
    azure_speech_region: str = "eastasia"

    llm_api_key: str = ""
    llm_base_url: str = "https://api.deepseek.com/v1"
    llm_model: str = "deepseek-chat"

    cors_origin: str = "http://localhost:5173"


settings = Settings()

---

File: backend/app/core/types.py

from __future__ import annotations
from pydantic import BaseModel
from typing import Literal


class WordScore(BaseModel):
    word: str
    accuracy_score: float          # 0–100
    error_type: Literal["None", "Omission", "Insertion", "Mispronunciation"] = "None"


class PronScore(BaseModel):
    overall: float                 # 0–100 加权综合分
    accuracy: float                # 发音准确度
    fluency: float                 # 流利度（停顿/重复惩罚）
    completeness: float            # 完整度（词语覆盖率）
    words: list[WordScore] = []


class CorrectionIssue(BaseModel):
    original: str                  # 用户原文片段
    corrected: str                 # 建议更正
    explanation: str               # 简短解释（英文，≤20词）
    category: Literal["grammar", "expression", "vocabulary"]


class TurnRecord(BaseModel):
    turn_id: str
    user_text: str
    ai_reply: str
    pron_score: PronScore
    corrections: list[CorrectionIssue] = []


class SpeakerTurnEvent(BaseModel):
    """EventBus 上传播的事件——Dev A 发布，Dev B 订阅"""
    session_id: str
    turn_id: str
    user_text: str
    pron_score: PronScore
    ai_reply: str
    scene_id: str


class SessionSummaryResponse(BaseModel):
    session_id: str
    scene_id: str
    total_turns: int
    pron_avg: float                # 发音综合均分
    accuracy_avg: float
    fluency_avg: float
    completeness_avg: float
    corrections_count: int
    ai_feedback: str               # LLM 生成的综合点评（中文，100–200字）
    turns: list[TurnRecord]

---

File: backend/app/core/event_bus.py

"""进程内异步事件总线。Dev A 调用 publish()，Dev B 调用 subscribe()。"""
from __future__ import annotations
import asyncio
from typing import Callable, Awaitable

from app.core.types import SpeakerTurnEvent

_handlers: list[Callable[[SpeakerTurnEvent], Awaitable[None]]] = []


def subscribe(handler: Callable[[SpeakerTurnEvent], Awaitable[None]]) -> None:
    """Dev B 在 register_coach() 中调用一次。"""
    _handlers.append(handler)


async def publish(event: SpeakerTurnEvent) -> None:
    """Dev A 每轮对话结束后调用。fire-and-forget，不阻塞主流程。"""
    for h in _handlers:
        asyncio.create_task(h(event))

---

File: backend/app/core/ws_hub.py

"""WS 连接注册表。按 session_id 路由消息。"""
from __future__ import annotations
from fastapi import WebSocket

_connections: dict[str, WebSocket] = {}


def register(session_id: str, ws: WebSocket) -> None:
    _connections[session_id] = ws


def unregister(session_id: str) -> None:
    _connections.pop(session_id, None)


async def send(session_id: str, message: dict) -> None:
    """发送 JSON 消息到指定 session 的 WebSocket。session 不存在则静默忽略。"""
    ws = _connections.get(session_id)
    if ws is not None:
        try:
            await ws.send_json(message)
        except Exception:
            unregister(session_id)

---

File: backend/app/core/scenes.py

"""场景与人设配置。全局只读，Phase 0 冻结后不修改。"""
from __future__ import annotations

SCENES: dict[str, dict] = {
    "interview": {
        "name": "Job Interview",
        "name_zh": "求职面试",
        "opening": "Hello! I'm Alex, and I'll be conducting your interview today. Let's start — can you briefly introduce yourself?",
        "personas": {
            "strict_interviewer": {
                "name": "Alex",
                "system_prompt": (
                    "You are Alex, a strict technical interviewer at a top tech company. "
                    "You ask focused, challenging questions and probe for depth on every answer. "
                    "Keep each reply under 40 words. Difficulty level: {difficulty}."
                ),
            }
        },
    },
    "restaurant": {
        "name": "Restaurant Order",
        "name_zh": "餐厅点餐",
        "opening": "Welcome! I'm Sam, your server today. What can I get for you?",
        "personas": {
            "friendly_waiter": {
                "name": "Sam",
                "system_prompt": (
                    "You are Sam, a friendly and attentive server at an upscale restaurant. "
                    "Be warm, make recommendations, and handle special requests gracefully. "
                    "Keep each reply under 40 words. Difficulty level: {difficulty}."
                ),
            }
        },
    },
    "meeting": {
        "name": "Business Meeting",
        "name_zh": "商务会议",
        "opening": "Good morning, everyone. I'm Jordan. Let's get started — could you walk us through your proposal?",
        "personas": {
            "colleague": {
                "name": "Jordan",
                "system_prompt": (
                    "You are Jordan, a professional colleague in a business strategy meeting. "
                    "Be collaborative, ask clarifying questions, and challenge assumptions constructively. "
                    "Keep each reply under 40 words. Difficulty level: {difficulty}."
                ),
            }
        },
    },
}

DIFFICULTY_LABELS = {1: "Beginner", 2: "Intermediate", 3: "Advanced"}

---

File: backend/app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

app = FastAPI(title="SpeakCoach API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.cors_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _register_modules() -> None:
    from app.modules.conversation.register import register_conversation
    from app.modules.coach.register import register_coach
    register_conversation(app)
    register_coach(app)


_register_modules()

启动命令：uvicorn app.main:app --reload --port 8000（在 backend/ 目录下执行）

---

File: backend/app/modules/conversation/register.py（STUB，Dev A 实现）

from fastapi import FastAPI


def register_conversation(app: FastAPI) -> None:
    """Dev A 在此挂载路由。签名不可改变。"""
    # TODO(Dev A): 实现
    # from app.modules.conversation.router import router as ws_router
    # from app.modules.conversation.scene_router import router as scene_router
    # app.include_router(ws_router)
    # app.include_router(scene_router, prefix="/api")
    pass

---

File: backend/app/modules/coach/register.py（STUB，Dev B 实现）

from fastapi import FastAPI


def register_coach(app: FastAPI) -> None:
    """Dev B 在此挂载路由并订阅 EventBus。签名不可改变。"""
    # TODO(Dev B): 实现
    # from app.core import event_bus
    # from app.modules.coach.turn_handler import on_turn_event
    # from app.modules.coach.router import router as coach_router
    # event_bus.subscribe(on_turn_event)
    # app.include_router(coach_router, prefix="/api")
    pass

---

File: frontend/package.json

{
  "name": "speak-coach-frontend",
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vue-tsc && vite build",
    "preview": "vite preview",
    "type-check": "vue-tsc --noEmit"
  },
  "dependencies": {
    "vue": "^3.4.0",
    "pinia": "^2.1.0",
    "axios": "^1.7.0"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^5.0.0",
    "vite": "^5.2.0",
    "vue-tsc": "^2.0.0",
    "typescript": "^5.4.0",
    "tailwindcss": "^3.4.0",
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0"
  }
}

安装命令：pnpm install（在 frontend/ 目录下）

---

File: frontend/vite.config.ts

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },
  server: {
    port: 5173,
  },
})

---

File: frontend/tailwind.config.js

/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js,ts}'],
  theme: { extend: {} },
  plugins: [],
}

---

File: frontend/src/core/types.ts

export type Difficulty = 1 | 2 | 3

export interface WordScore {
  word: string
  accuracy_score: number
  error_type: 'None' | 'Omission' | 'Insertion' | 'Mispronunciation'
}

export interface PronScore {
  overall: number
  accuracy: number
  fluency: number
  completeness: number
  words: WordScore[]
}

export interface CorrectionIssue {
  original: string
  corrected: string
  explanation: string
  category: 'grammar' | 'expression' | 'vocabulary'
}

export interface TurnRecord {
  turn_id: string
  user_text: string
  ai_reply: string
  pron_score: PronScore
  corrections: CorrectionIssue[]
}

export interface SessionSummaryResponse {
  session_id: string
  scene_id: string
  total_turns: number
  pron_avg: number
  accuracy_avg: number
  fluency_avg: number
  completeness_avg: number
  corrections_count: number
  ai_feedback: string
  turns: TurnRecord[]
}

// ─── WS Messages ────────────────────────────────────────────────────────────

export type ClientMsg =
  | { type: 'session_start'; scene_id: string; difficulty: Difficulty; persona_id: string }
  | { type: 'audio_chunk'; data: string; seq: number }
  | { type: 'audio_end'; seq_count: number }
  | { type: 'session_end' }

export type ServerMsg =
  | { type: 'asr_partial'; text: string }
  | { type: 'asr_final'; turn_id: string; text: string; duration_ms: number }
  | { type: 'pron_score'; turn_id: string; overall: number; accuracy: number; fluency: number; completeness: number; words: WordScore[] }
  | { type: 'reply_text'; turn_id: string; text: string }
  | { type: 'reply_audio'; turn_id: string; data: string }
  | { type: 'correction'; turn_id: string; issues: CorrectionIssue[] }
  | { type: 'turn_end'; turn_id: string }
  | { type: 'error'; code: string; message: string }

---

File: frontend/src/core/ws.ts

import type { ClientMsg, ServerMsg } from './types'

type Handler = (msg: ServerMsg) => void

let _socket: WebSocket | null = null
const _handlers: Handler[] = []

export const ws = {
  connect(sessionId: string): Promise<void> {
    return new Promise((resolve, reject) => {
      const url = `ws://localhost:8000/ws/session/${sessionId}`
      _socket = new WebSocket(url)
      _socket.onopen = () => resolve()
      _socket.onerror = (e) => reject(e)
      _socket.onmessage = (e) => {
        try {
          const msg: ServerMsg = JSON.parse(e.data as string)
          _handlers.forEach((h) => h(msg))
        } catch {
          // ignore malformed messages
        }
      }
    })
  },

  disconnect(): void {
    _socket?.close()
    _socket = null
  },

  send(msg: ClientMsg): void {
    if (_socket?.readyState === WebSocket.OPEN) {
      _socket.send(JSON.stringify(msg))
    }
  },

  onMessage(handler: Handler): () => void {
    _handlers.push(handler)
    return () => {
      const idx = _handlers.indexOf(handler)
      if (idx !== -1) _handlers.splice(idx, 1)
    }
  },

  isConnected(): boolean {
    return _socket?.readyState === WebSocket.OPEN
  },
}

---

File: frontend/src/core/store.ts

import { defineStore } from 'pinia'
import type { PronScore, CorrectionIssue, SessionSummaryResponse } from './types'

export const useAppStore = defineStore('app', {
  state: () => ({
    // 会话元数据
    sessionId: null as string | null,
    sceneId: null as string | null,
    difficulty: 1 as 1 | 2 | 3,
    personaId: null as string | null,

    // 页面阶段
    phase: 'scene_select' as 'scene_select' | 'in_session' | 'summary',

    // 当前轮次（每轮重置）
    currentTurnId: null as string | null,
    isRecording: false,
    isSpeaking: false,          // AI TTS 播放中
    asrText: '',                // STT 实时文字
    aiReplyText: '',
    currentPronScore: null as PronScore | null,
    currentCorrections: [] as CorrectionIssue[],

    // 课后总结
    summary: null as SessionSummaryResponse | null,
  }),

  actions: {
    startSession(params: {
      sessionId: string
      sceneId: string
      difficulty: 1 | 2 | 3
      personaId: string
    }) {
      this.sessionId = params.sessionId
      this.sceneId = params.sceneId
      this.difficulty = params.difficulty
      this.personaId = params.personaId
      this.phase = 'in_session'
    },

    resetTurn() {
      this.currentTurnId = null
      this.asrText = ''
      this.aiReplyText = ''
      this.currentPronScore = null
      this.currentCorrections = []
    },

    endSession() {
      this.phase = 'summary'
    },
  },
})

---

File: frontend/src/core/scenes.ts

export interface SceneConfig {
  name: string
  name_zh: string
  personas: Record<string, { name: string }>
}

export const SCENES: Record<string, SceneConfig> = {
  interview: {
    name: 'Job Interview',
    name_zh: '求职面试',
    personas: { strict_interviewer: { name: 'Alex' } },
  },
  restaurant: {
    name: 'Restaurant Order',
    name_zh: '餐厅点餐',
    personas: { friendly_waiter: { name: 'Sam' } },
  },
  meeting: {
    name: 'Business Meeting',
    name_zh: '商务会议',
    personas: { colleague: { name: 'Jordan' } },
  },
}

---

File: frontend/src/mock/events.ts

import type { ServerMsg } from '@/core/types'

export const MOCK_TURN_EVENTS: ServerMsg[] = [
  { type: 'asr_partial', text: 'I am inter...' },
  {
    type: 'asr_final',
    turn_id: 'mock-turn-1',
    text: 'I am interested in the senior engineer position.',
    duration_ms: 2800,
  },
  {
    type: 'pron_score',
    turn_id: 'mock-turn-1',
    overall: 71.5,
    accuracy: 66.0,
    fluency: 78.0,
    completeness: 91.0,
    words: [
      { word: 'I', accuracy_score: 95, error_type: 'None' },
      { word: 'am', accuracy_score: 92, error_type: 'None' },
      { word: 'interested', accuracy_score: 58, error_type: 'Mispronunciation' },
      { word: 'in', accuracy_score: 88, error_type: 'None' },
      { word: 'the', accuracy_score: 85, error_type: 'None' },
      { word: 'senior', accuracy_score: 74, error_type: 'None' },
      { word: 'engineer', accuracy_score: 62, error_type: 'Mispronunciation' },
      { word: 'position', accuracy_score: 80, error_type: 'None' },
    ],
  },
  {
    type: 'reply_text',
    turn_id: 'mock-turn-1',
    text: "Good. Can you describe a technically challenging project you've led recently?",
  },
  {
    type: 'correction',
    turn_id: 'mock-turn-1',
    issues: [
      {
        original: 'interested',
        corrected: 'ɪnˈtrestɪd',
        explanation: 'Stress falls on the first syllable: IN-ter-es-ted',
        category: 'expression',
      },
    ],
  },
  { type: 'turn_end', turn_id: 'mock-turn-1' },
]

export const MOCK_SUMMARY_RESPONSE = {
  session_id: 'mock-session',
  scene_id: 'interview',
  total_turns: 5,
  pron_avg: 71.5,
  accuracy_avg: 66.0,
  fluency_avg: 78.0,
  completeness_avg: 91.0,
  corrections_count: 3,
  ai_feedback:
    '整体表现不错，句式结构清晰。主要问题是部分多音节词（如 "interested"、"experience"）的重音位置不准确，建议重点练习词重音规律。流利度良好，完整度高，继续保持。',
  turns: [],
}

---

File: frontend/src/App.vue

<template>
  <div class="min-h-screen bg-slate-50 font-sans">
    <SceneSelector v-if="store.phase === 'scene_select'" />
    <ConversationRoom v-else-if="store.phase === 'in_session'">
      <template #correction>
        <CorrectionPanel />
      </template>
    </ConversationRoom>
    <SessionSummaryPanel
      v-else-if="store.phase === 'summary'"
      :session-id="store.sessionId!"
    />
  </div>
</template>

<script setup lang="ts">
import { useAppStore } from '@/core/store'
// Dev A 提供
import SceneSelector from '@/modules/conversation/SceneSelector.vue'
import ConversationRoom from '@/modules/conversation/ConversationRoom.vue'
// Dev B 提供
import CorrectionPanel from '@/modules/coach/CorrectionPanel.vue'
import SessionSummaryPanel from '@/modules/coach/SessionSummaryPanel.vue'

const store = useAppStore()
</script>

---

File: frontend/src/main.ts

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import './index.css'

const app = createApp(App)
app.use(createPinia())
app.mount('#app')

---

File: frontend/src/index.css

@tailwind base;
@tailwind components;
@tailwind utilities;

---

File: frontend/index.html

<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>SpeakCoach</title>
  </head>
  <body>
    <div id="app"></div>
    <script type="module" src="/src/main.ts"></script>
  </body>
</html>

---

Module Stubs（Phase 0 创建，Phase A/B 填写）

以下文件 Phase 0 创建为“可编译占位”，保证 `pnpm dev` 当场能跑起来；后续内容由各自 owner 覆盖实现。

Dev A 需创建：
backend/app/modules/conversation/__init__.py
backend/app/modules/conversation/register.py  ← 上方已给 stub
backend/tests/conversation/__init__.py
frontend/src/modules/conversation/SceneSelector.vue
frontend/src/modules/conversation/ConversationRoom.vue
frontend/src/modules/conversation/PronScoreBar.vue

Dev B 需创建：
backend/app/modules/coach/__init__.py
backend/app/modules/coach/register.py  ← 上方已给 stub
backend/tests/coach/__init__.py
frontend/src/modules/coach/CorrectionPanel.vue
frontend/src/modules/coach/SessionSummaryPanel.vue

占位组件要求：

- `SceneSelector.vue`：渲染一个简单占位块，例如 `SceneSelector Placeholder`
- `ConversationRoom.vue`：渲染一个简单容器，并包含 `<slot name="correction" />`
- `PronScoreBar.vue`：渲染占位文本
- `CorrectionPanel.vue`：默认渲染空状态或占位文本
- `SessionSummaryPanel.vue`：接受 `sessionId: string` props，渲染占位文本

这样做的目的：避免 Skeleton 阶段 `App.vue` 已 import 组件、但模块目录只有 `.gitkeep` 导致前端直接编译失败。

---

验证 Skeleton 正常工作

# 终端 1：后端
cd backend
uv pip install -e .
Copy-Item ../.env.example .env   # Windows PowerShell；填入 key
uvicorn app.main:app --reload --port 8000

# 预期输出：INFO: Application startup complete.

# 终端 2：前端
cd frontend
pnpm install
pnpm dev

# 预期输出：Local: http://localhost:5173

# 终端 3：验证 WS 可连接
# 浏览器控制台执行：
# const ws = new WebSocket('ws://localhost:8000/ws/session/test-123')
# ws.onopen = () => ws.send(JSON.stringify({type:'session_start', scene_id:'interview', difficulty:1, persona_id:'strict_interviewer'}))
# ws.onmessage = e => console.log(JSON.parse(e.data))

Skeleton 合格标准：

- `pnpm dev` 能成功启动，前端不因缺少模块组件而编译失败
- WS 连接不报错，后端收到 `session_start` 不崩溃（返回空或 `{"type":"error"}` 均可，Dev A 实现后才有真实回包）
- `App.vue` 已预埋 correction slot，联调阶段不再改 Skeleton
