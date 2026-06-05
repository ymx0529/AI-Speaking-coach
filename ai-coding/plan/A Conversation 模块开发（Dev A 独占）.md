> 文件归属：`backend/app/modules/conversation/**`、`backend/tests/conversation/**`、`frontend/src/modules/conversation/**`
> 分支：`feat/conversation`（从 tag `v0-skeleton` 拉出）
> 不得修改 `backend/app/core/`、`backend/app/main.py`、`frontend/src/core/`、`frontend/src/App.vue` 等骨架文件。
> **本期目标是“按住说话、松手出结果”的低延迟回合制 Demo，不做全双工实时打断。**

---

任务清单（按顺序完成）

Phase A1 · 回合主链路跑通（Day 1 下午）

[] A1-1 创建 `backend/app/modules/conversation/scene_router.py`：返回场景与人设列表
[] A1-2 创建 `backend/app/modules/conversation/session_manager.py`：管理会话状态与音频分片
[] A1-3 创建 `backend/app/modules/conversation/router.py`：实现 WS endpoint 与 `session_start/audio_chunk/audio_end/session_end`
[] A1-4 用 mock 语音结果跑通 `asr_final → pron_score → reply_text → turn_end`
[] A1-5 写 `backend/tests/conversation/test_router_protocol.py`

Phase A2 · 语音能力接入 + 前端（Day 2 全天）

[] A2-1 创建 `backend/app/modules/conversation/audio_utils.py`：webm/opus 转 PCM WAV 16kHz
[] A2-2 创建 `backend/app/modules/conversation/azure_speech.py`：STT + 发音评测 + TTS
[] A2-3 创建 `backend/app/modules/conversation/llm_client.py`：基于场景 prompt 生成下一轮回复
[] A2-4 实现 `backend/app/modules/conversation/register.py`
[] A2-5 创建 `frontend/src/modules/conversation/useConversation.ts`
[] A2-6 实现 `SceneSelector.vue`、`ConversationRoom.vue`、`PronScoreBar.vue`
[] A2-7 写 `backend/tests/conversation/test_azure_speech_adapter.py`、`test_session_manager.py`

---

后端文件详解

`backend/app/modules/conversation/scene_router.py`

- `GET /api/scenes`
- 返回 `core/scenes.py` 中的只读配置，前端只依赖此接口渲染场景卡片与 persona 选项
- 不做数据库，不做后台管理

`backend/app/modules/conversation/session_manager.py`

职责：

- 保存 `session_start` 传入的 `scene_id / difficulty / persona_id`
- 累积一轮内的 `audio_chunk` 字节流
- 为每轮生成 `turn_id`
- 保存会话历史，供 `llm_client` 生成上下文回复

建议数据结构：

- `SessionState`
  - `session_id: str`
  - `scene_id: str`
  - `difficulty: int`
  - `persona_id: str`
  - `audio_chunks: list[bytes]`
  - `history: list[dict[str, str]]`
  - `turn_count: int`

对外函数：

- `start_session(session_id, scene_id, difficulty, persona_id) -> None`
- `append_audio_chunk(session_id, seq, chunk_bytes) -> None`
- `consume_audio(session_id) -> bytes`
- `append_turn_history(session_id, user_text, ai_reply) -> None`
- `get_session(session_id) -> SessionState | None`
- `end_session(session_id) -> None`

`backend/app/modules/conversation/audio_utils.py`

职责：

- 把浏览器传来的 webm/opus 合并后转成 Azure 可接收的 PCM WAV
- 输出格式固定为 `16kHz / 16-bit / mono`

实现要求：

- 使用 `pydub.AudioSegment`
- 依赖本机 `ffmpeg`
- 转换失败时抛出明确异常，由 `router.py` 统一转成 `error` 事件

`backend/app/modules/conversation/azure_speech.py`

建议对外接口：

- `async transcribe_and_score(wav_bytes: bytes) -> tuple[str, PronScore]`
- `async synthesize_reply(text: str) -> bytes`

实现要求：

- STT 与发音评测基于同一段 WAV 完成
- 发音评测返回 `overall / accuracy / fluency / completeness / words`
- TTS 固定使用 `en-US-JennyNeural`
- 任一 Azure 调用失败时抛出异常，不在适配器内部吞错

降级策略：

- 演示期间若 Azure TTS 失败，可以仍然返回 `reply_text`，并跳过 `reply_audio`
- 若 STT 或发音评测失败，直接推送 `error`，本轮结束，不继续 LLM

`backend/app/modules/conversation/llm_client.py`

职责：

- 基于场景系统提示、难度、历史对话，生成 AI 下一句英文回复

实现要求：

- 使用 `AsyncOpenAI`
- 系统 prompt 来自 `core/scenes.py` 对应 persona 的 `system_prompt`
- 每次回复控制在 40 词以内
- 历史仅保留最近 6 条 message，避免 prompt 膨胀

建议接口：

- `async generate_reply(scene_id: str, persona_id: str, difficulty: int, history: list[dict[str, str]], user_text: str) -> str`

`backend/app/modules/conversation/router.py`

职责：

- 提供 `ws://localhost:8000/ws/session/{session_id}`
- 处理四类客户端消息：`session_start`、`audio_chunk`、`audio_end`、`session_end`
- 在 `audio_end` 后串起一轮完整流程

一轮处理顺序必须固定为：

1. 合并并消费当前轮音频
2. 转 WAV
3. `transcribe_and_score`
4. 发送 `asr_final`
5. 发送 `pron_score`
6. 调 `generate_reply`
7. 发送 `reply_text`
8. 若 TTS 成功，发送 `reply_audio`
9. `publish(SpeakerTurnEvent)`
10. 发送 `turn_end`
11. 写入会话历史

错误处理：

- 任何一步失败都要发送统一格式的 `error`
- `error.code` 建议使用：`BAD_REQUEST`、`AUDIO_DECODE_FAILED`、`ASR_FAILED`、`PRON_FAILED`、`LLM_FAILED`、`TTS_FAILED`
- 出错后当前轮终止，但 WebSocket 连接不断开

`backend/app/modules/conversation/register.py`

最终实现：

```python
from fastapi import FastAPI


def register_conversation(app: FastAPI) -> None:
    from app.modules.conversation.router import router as ws_router
    from app.modules.conversation.scene_router import router as scene_router

    app.include_router(ws_router)
    app.include_router(scene_router, prefix="/api")
```

---

前端文件详解

`frontend/src/modules/conversation/useConversation.ts`

职责：

- 建立与断开 WS
- 开始会话时发送 `session_start`
- 录音时把 `MediaRecorder` 产生的 blob 逐片 base64 编码为 `audio_chunk`
- 停止录音后发送 `audio_end`
- 消费服务端消息并写入 `store`

需要处理的服务端事件：

- `asr_partial`：更新 `store.asrText`
- `asr_final`：更新 `currentTurnId` 与最终识别文本
- `pron_score`：更新 `currentPronScore`
- `reply_text`：更新 `aiReplyText`
- `reply_audio`：播放音频并设置 `isSpeaking`
- `turn_end`：结束当前轮 loading
- `error`：展示 toast 或错误条

`frontend/src/modules/conversation/SceneSelector.vue`

职责：

- 从 `GET /api/scenes` 拉取场景列表
- 允许选择 `scene_id`、`difficulty`、`persona_id`
- 点击“开始练习”后：
  - 生成 `sessionId`
  - 调 `store.startSession(...)`
  - 建立 WS 并发送 `session_start`

UI 最低要求：

- 三个场景卡片：面试 / 点餐 / 会议
- 难度三档
- 一个开始按钮

`frontend/src/modules/conversation/PronScoreBar.vue`

职责：

- 展示 `overall / accuracy / fluency / completeness`
- 对低分单词做高亮列表
- 仅消费 `PronScore` props，不直接碰全局状态

`frontend/src/modules/conversation/ConversationRoom.vue`

职责：

- 提供录音主交互与对话展示
- 集成 `<slot name="correction" />`，Skeleton 已预埋，后续不改 `App.vue`

页面结构建议：

- 左侧：当前场景、识别文本、AI 回复、发音分数
- 右侧：`<slot name="correction" />`
- 底部：按住说话按钮 + 结束按钮

录音交互约束：

- 默认按钮触发，空格键作为增强能力，不作为唯一入口
- 只允许在 `isSpeaking === false` 时开始下一轮录音
- 一轮未完成时禁止重复发送 `audio_end`

---

独立开发与测试建议

后端先用 mock 打通：

- `transcribe_and_score()` 先返回固定文本和固定 `PronScore`
- `generate_reply()` 先返回固定英文问题
- `synthesize_reply()` 先返回空字节或 fixture

前端先用 `frontend/src/mock/events.ts` 驱动：

- 点击按钮后依次回放 `MOCK_TURN_EVENTS`
- 验证页面能显示识别文本、分数、回复文本

---

Dev A 测试用例

`backend/tests/conversation/test_session_manager.py`

- `start_session` 后能正确保存会话元数据
- `append_audio_chunk + consume_audio` 会按顺序合并并清空缓存
- `append_turn_history` 会追加历史
- `end_session` 会移除状态

`backend/tests/conversation/test_router_protocol.py`

- 缺少 `session_start` 时收到 `audio_chunk`，返回 `BAD_REQUEST`
- 正常一轮会依次产生 `asr_final / pron_score / reply_text / turn_end`
- Azure 或 LLM 抛错时会返回 `error`，连接保持可继续使用

`backend/tests/conversation/test_azure_speech_adapter.py`

- 用 mock 验证 STT、发音评测、TTS 三个适配函数会正确解析结果
- 转码失败时抛出明确异常

---

完成标准

1. 前端可从场景页进入会话页，不报编译错误
2. 一轮录音结束后，能稳定看到 `asr_final + pron_score + reply_text`
3. `reply_audio` 成功时可播放，失败时不阻断本轮
4. `SpeakerTurnEvent` 能成功 publish 给 Coach 模块
5. 三个场景 persona 区分明显，回答语气符合设定
