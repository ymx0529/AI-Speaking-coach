# Dev A 需求与接口速览

适用角色：Dev A  
负责模块：Conversation Runtime

---

## 1. 场景选择与开始练习

**负责需求**
- 用户选择场景、难度、角色后开始一场口语练习

**对应功能**
- 展示场景列表
- 生成 `session_id`
- 建立 WebSocket 会话
- 发送会话启动事件

**主要接口**
- HTTP：`GET /api/scenes`
- WS：`session.start`
- WS：`session.ready`

**关键代码接口**
- `frontend/src/modules/conversation/SceneSelector.vue`
- `frontend/src/modules/conversation/useConversation.ts`
- `backend/app/modules/conversation/scene_router.py`
- `backend/app/modules/conversation/router.py`

---

## 2. 用户语音输入与回合管理

**负责需求**
- 用户发起一轮说话，系统正确接收并管理本轮状态

**对应功能**
- 录音开始/结束控制
- 音频分片上传
- 首个分片触发 `turn.started`
- 一轮结束后进入处理态

**主要接口**
- WS：`audio.append`
- WS：`turn.started`
- WS：`turn.completed`
- WS：`error`

**关键代码接口**
- `frontend/src/modules/conversation/ConversationRoom.vue`
- `frontend/src/modules/conversation/useConversation.ts`
- `backend/app/modules/conversation/session_manager.py`
- `backend/app/modules/conversation/router.py`

---

## 3. 实时识别文本反馈

**负责需求**
- 用户说话过程中能尽快看到识别结果，提升实时感

**对应功能**
- 返回中间识别结果
- 返回本轮最终识别文本
- 在前端更新当前回合文本

**主要接口**
- WS：`asr.partial`
- WS：`user_turn.final`

**关键代码接口**
- `backend/app/modules/conversation/azure_speech.py`
- `backend/app/modules/conversation/audio_utils.py`
- `backend/app/modules/conversation/router.py`
- `frontend/src/modules/conversation/useConversation.ts`

---

## 4. AI 对话回复

**负责需求**
- 系统基于场景上下文生成自然的下一句回复

**对应功能**
- 根据场景、角色、难度生成回复
- 控制回复长度
- 保留有限上下文历史

**主要接口**
- WS：`assistant.reply_text`

**关键代码接口**
- `backend/app/modules/conversation/llm_client.py`
- `backend/app/modules/conversation/session_manager.py`
- `backend/app/modules/conversation/router.py`

---

## 5. AI 语音播放

**负责需求**
- AI 回复不仅有文字，还要有语音播放

**对应功能**
- 将回复文本转成音频
- 前端播放 AI 回复音频
- TTS 失败时文本回复仍可用

**主要接口**
- WS：`assistant.reply_audio`
- WS：`error`（TTS 降级场景）

**关键代码接口**
- `backend/app/modules/conversation/azure_speech.py`
- `backend/app/modules/conversation/router.py`
- `frontend/src/modules/conversation/useConversation.ts`
- `frontend/src/modules/conversation/ConversationRoom.vue`

---

## 6. 向 Coach 交接本轮数据

**负责需求**
- 把本轮主链路结果稳定交给 Dev B 做发音和纠错分析

**对应功能**
- 发布本轮 transcript、音频引用、AI 回复、时长等数据
- 保证每轮只发布一次

**主要接口**
- 事件总线：`TurnTranscriptReadyEvent`

**关键代码接口**
- `backend/app/core/event_bus.py`
- `backend/app/core/types.py`
- `backend/app/modules/conversation/router.py`

---

## 7. 会话结束与总结交接

**负责需求**
- 用户结束练习后，前端能进入总结页，后端不会过早清理数据

**对应功能**
- 发送 `session.finish`
- 查询会话状态
- 保留 session，等待 summary 生成

**主要接口**
- WS：`session.finish`
- HTTP：`GET /api/sessions/{session_id}/status`

**关键代码接口**
- `backend/app/modules/conversation/session_manager.py`
- `backend/app/modules/conversation/router.py`
- `frontend/src/modules/conversation/ConversationRoom.vue`

---

## 8. Dev A 不负责的内容

- `analysis.pronunciation`
- `analysis.correction`
- `grammar_score`
- `expression_score`
- `vocabulary_score`
- `SessionSummaryResponse` 的评分与建议生成

这些由 Dev B 负责，Dev A 只消费结果并展示。
