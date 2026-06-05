SpeakCoach — AI 英语口语陪练 设计文档

2026-06-05 · 两人两天 Demo · Vue + FastAPI + Azure Speech + DeepSeek

---

一、产品定位

帮助用户在指定场景（面试 / 点餐 / 商务会议）中与 AI 进行真实对话训练，重点解决：
- 说话即练，无需等待后处理
- 发音有数据（Azure 音素级评分）
- 错误有纠正（实时语法/表达）
- 进步可量化（课后评分报告）

本期范围说明：

- 本版本是“两人两天可演示 Demo”
- 对话交互形态为“按住说话、松手出结果”的低延迟回合制
- 不承诺全双工连续语音、边听边说、可打断式 TTS
--- 

二、整体架构

浏览器 (Vue 3)
  ┌─ SceneSelector ─── 选场景/难度/AI角色
  ├─ ConversationRoom ─ 按住说话 → WS 分片上传 → 松手发送整轮结果
  │    ├─ AudioRecorder  (webm/opus chunks)
  │    └─ PronScoreBar   (实时发音分数)
  ├─ CorrectionPanel ── 当轮语法/表达纠错
  └─ SessionSummaryPanel 课后总结 + 四维评分

        │ WebSocket ws://host/ws/session/{id}
        │ HTTP GET /api/scenes
        │ HTTP POST /api/sessions/{id}/summary
        ↓

FastAPI 后端
  ┌─ core/
  │    ├─ ws_hub.py     — WS 连接注册表（Skeleton，冻结）
  │    ├─ event_bus.py  — 进程内事件总线（Skeleton，冻结）
  │    ├─ types.py      — 共享 Pydantic 类型（Skeleton，冻结）
  │    └─ scenes.py     — 场景/人设配置（Skeleton，冻结）
  │
  ├─ modules/conversation/  ← Dev A 独占
  │    ├─ router.py          WS endpoint + 音频收集
  │    ├─ scene_router.py    GET /api/scenes
  │    ├─ azure_speech.py    STT + TTS + 发音评测
  │    ├─ llm_client.py      DeepSeek 对话生成
  │    └─ session_manager.py 内存会话状态
  │
  └─ modules/coach/          ← Dev B 独占
       ├─ turn_handler.py    订阅 EventBus，接收每轮事件
       ├─ correction_engine.py LLM 语法/表达纠错
       ├─ session_accumulator.py 累积会话数据
       ├─ summary_engine.py  生成课后总结 + 评分
       └─ router.py          POST /api/sessions/{id}/summary

数据流（一轮对话）：
  用户按住录音 → MediaRecorder(webm) → WS audio_chunk × N + audio_end
  → Dev A: concat → convert WAV → Azure STT → Azure Pron → LLM → Azure TTS
  → WS 推 asr_final + pron_score + reply_text + reply_audio
  → 同时 Dev A publish EventBus(SpeakerTurnEvent)
  → Dev B 异步接收 → LLM 纠错 → WS 推 correction 事件
  → 用户看到发音评分 + AI 语音回复 + 语法气泡

说明：这里的“实时”定义为单轮内低延迟上传与回包，不是全双工流式通话。

---

三、关键技术选型

组件
选型
原因
语音 STT
Azure Speech SDK (Python)
与发音评测同一 SDK，免二次对齐
发音评测
Azure Pronunciation Assessment (音素级)
官方打分：准确/流利/完整度
TTS
Azure Speech SDK en-US-JennyNeural
与 STT 同 key，延迟低
对话 LLM
DeepSeek-Chat (OpenAI 兼容)
中文推理强，成本低，API 易用
音频转码
pydub + ffmpeg (webm→PCM wav)
Azure SDK 要求 PCM 16kHz
前端实时通信
WebSocket
双向事件流，低延迟
前端状态
Pinia
Vue 3 官方推荐
前端样式
Tailwind CSS
快速构建 demo UI
后端框架
FastAPI + uvicorn
原生 async/await，WS 支持好

---

四、WS 事件流（完整见 PROTOCOL.md）

Client → Server            Server → Client
─────────────────────────────────────────────────────────
session_start              (连接建立)
audio_chunk × N            asr_partial (STT 流式，可选)
audio_end             →→   asr_final (完整识别文本)
                           pron_score (发音四维评分 + word 列表)
                           reply_text (AI 回复文字)
                           reply_audio (base64 mp3)
                           correction (语法/表达纠错，异步)
                           turn_end
session_end           →→   (断开)

---

五、模块边界（文件集合零交集）

路径 glob
Owner
变更窗口
backend/app/core/** backend/app/main.py
Skeleton
Phase 0 冻结
frontend/src/core/** frontend/src/App.vue frontend/src/main.ts
Skeleton
Phase 0 冻结
frontend/src/mock/** PROTOCOL.md .env.example
Skeleton
Phase 0 冻结
| `backend/app/modules/conversation/**` `backend/tests/conversation/**` `frontend/src/modules/conversation/**` | Dev A | 仅 Dev A |
| `backend/app/modules/coach/**` `backend/tests/coach/**` `frontend/src/modules/coach/**` | Dev B | 仅 Dev B |

---

六、两天时间线

时间
Dev A（对话链路）
Dev B（教练评测）
| D1 上午 | 共同：搭骨架、冻结契约、建分支 | 同左 |
| D1 下午 | WS handler + audio 收集 + mock STT 跑通 | correction_engine mock 测试跑通 |
| D2 上午 | 接入 Azure STT + TTS + 发音评测 | 接入 Azure Pron 累积 + summary_engine |
| D2 下午 | LLM 对话 + 前端 ConversationRoom | 前端 CorrectionPanel + SummaryPanel |
| D2 晚上 | 共同：联调 + demo 录制 | 同左 |

---

七、技术风险与缓解

风险
缓解
Azure Pron Assessment 对 webm/opus 不支持
pydub 提前转 PCM wav 16kHz，完全规避
LLM 纠错延迟影响体验
EventBus fire-and-forget，不阻塞主 TTS 流程
WS 并发 session 冲突
ws_hub 以 session_id 为 key，天然隔离
首版无持久化
纯内存，重启丢会话，Demo 期间可接受

---

八、不在首版范围（见 INNOVATIONS.md）

- AI 角色个性化 + 难度闯关
- 实时纠错气泡（视觉动效）
- 能力雷达图（Chart.js 可视化）
- 错题本 + 个性化复习
