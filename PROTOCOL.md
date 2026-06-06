# SpeakCoach WebSocket Protocol v2

本文件用于冻结会话主链路与分析链路的共享契约。

## 1. 连接规则

- URL：`ws://{host}/ws/session/{session_id}`
- `session_id` 由前端生成
- 建连后客户端发送 `session.start`
- 同一会话内允许多轮对话

## 2. 兼容说明

当前仓库仍存在旧事件名：
- Client：`session_start`、`audio_chunk`、`audio_end`、`session_end`
- Server：`asr_partial`、`asr_final`、`pron_score`、`reply_text`、`reply_audio`、`correction`、`turn_end`

从本次 shared contract 冻结开始，新开发以 v2 事件名为准。  
旧事件名仅保留为过渡兼容，待 `conversation` / `coach` 模块切换完成后删除。

## 3. Client -> Server

### `session.start`

```json
{
  "type": "session.start",
  "session_id": "uuid",
  "scene_id": "interview",
  "difficulty": 1,
  "persona_id": "strict_interviewer",
  "client_ts": 1717651200000
}
```

### `audio.append`

```json
{
  "type": "audio.append",
  "session_id": "uuid",
  "turn_id": null,
  "seq": 0,
  "encoding": "webm_opus",
  "chunk": "<base64 audio chunk>",
  "is_last": false,
  "client_ts": 1717651200300
}
```

字段说明：
- `turn_id`：第一段音频时可为空，服务端会在 `turn.started` 中回传
- `encoding`：当前固定为 `webm_opus`
- `is_last=true` 表示本轮语音输入结束

### `session.finish`

```json
{
  "type": "session.finish",
  "session_id": "uuid"
}
```

说明：
- `session.finish` 只表示用户结束练习
- 不等于立刻清理会话数据

## 4. Server -> Client

### `session.ready`

```json
{
  "type": "session.ready",
  "session_id": "uuid",
  "server_ts": 1717651200100
}
```

### `turn.started`

```json
{
  "type": "turn.started",
  "session_id": "uuid",
  "turn_id": "uuid",
  "server_ts": 1717651200400
}
```

### `asr.partial`

```json
{
  "type": "asr.partial",
  "session_id": "uuid",
  "turn_id": "uuid",
  "text": "I would like to...",
  "server_ts": 1717651200800
}
```

### `user_turn.final`

```json
{
  "type": "user_turn.final",
  "session_id": "uuid",
  "turn_id": "uuid",
  "text": "I would like to order a pasta, please.",
  "duration_ms": 2600,
  "server_ts": 1717651202000
}
```

### `assistant.reply_text`

```json
{
  "type": "assistant.reply_text",
  "session_id": "uuid",
  "turn_id": "uuid",
  "text": "Certainly. Would you like anything to drink with that?"
}
```

### `assistant.reply_audio`

```json
{
  "type": "assistant.reply_audio",
  "session_id": "uuid",
  "turn_id": "uuid",
  "audio_format": "mp3",
  "data": "<base64 audio>"
}
```

### `analysis.pronunciation`

说明：该事件属于 Coach 模块，不再是 Dev A 的自有业务结果。

```json
{
  "type": "analysis.pronunciation",
  "session_id": "uuid",
  "turn_id": "uuid",
  "overall": 81.0,
  "accuracy": 79.0,
  "fluency": 84.0,
  "completeness": 90.0,
  "words": []
}
```

### `analysis.correction`

说明：该事件属于 Coach 模块，不再是 Dev A 的自有业务结果。

```json
{
  "type": "analysis.correction",
  "session_id": "uuid",
  "turn_id": "uuid",
  "issues": [
    {
      "original": "I want order pasta",
      "corrected": "I want to order pasta",
      "explanation": "Use infinitive after want.",
      "category": "grammar",
      "severity": "high"
    }
  ]
}
```

### `turn.completed`

```json
{
  "type": "turn.completed",
  "session_id": "uuid",
  "turn_id": "uuid",
  "server_ts": 1717651202600
}
```

说明：
- 当前定义为：Conversation 主链路处理完成
- 不代表 Coach 分析一定完成

### `error`

```json
{
  "type": "error",
  "session_id": "uuid",
  "turn_id": "uuid",
  "code": "ASR_FAILED",
  "message": "Speech recognition returned empty result.",
  "retryable": true
}
```

## 5. 推荐错误码

- `BAD_REQUEST`
- `SESSION_NOT_FOUND`
- `AUDIO_DECODE_FAILED`
- `ASR_FAILED`
- `LLM_REPLY_FAILED`
- `TTS_FAILED`
- `PRON_ANALYSIS_FAILED`
- `CORRECTION_FAILED`
- `SUMMARY_NOT_READY`

## 6. A/B 模块边界

### Dev A 负责产出

- `session.ready`
- `turn.started`
- `asr.partial`
- `user_turn.final`
- `assistant.reply_text`
- `assistant.reply_audio`
- `turn.completed`
- `error`
- `TurnTranscriptReadyEvent`

### Dev B 负责产出

- `analysis.pronunciation`
- `analysis.correction`
- `POST /api/sessions/{session_id}/summary`

## 7. 交接事件

Dev A 在一轮完成后必须发布 `TurnTranscriptReadyEvent`，至少包含：
- `session_id`
- `turn_id`
- `scene_id`
- `difficulty`
- `persona_id`
- `transcript`
- `audio_format`
- `audio_b64`
- `assistant_reply_text`
- `turn_duration_ms`

