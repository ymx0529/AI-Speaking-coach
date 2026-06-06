# Coach 模块协议补充（Dev B 专属）

> 本文档是 Dev B 对 `PROTOCOL.md` v1 的补充说明，记录 Coach 模块新增的 WS 事件、HTTP 接口和内部事件总线契约。
> 联调完成后，经双人确认可合并回主 `PROTOCOL.md`。

---

## 新增 Server → Client 事件

### `analysis.pronunciation`

由 Coach 模块产出，可能在 `turn_end` 之后异步到达。

```json
{
  "type": "analysis.pronunciation",
  "session_id": "uuid",
  "turn_id": "uuid",
  "overall": 78.2,
  "accuracy": 75.0,
  "fluency": 81.5,
  "completeness": 88.0,
  "words": [
    {
      "word": "pasta",
      "accuracy_score": 61.2,
      "error_type": "Mispronunciation"
    }
  ]
}
```

### `analysis.correction`

由 Coach 模块产出，与 `analysis.pronunciation` 并行或在其后到达。

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

---

## 回合事件顺序

```
（v1 主链路）
asr_partial → asr_final → reply_text → reply_audio → turn_end

（Coach 分析链路，异步，可能晚于 turn_end）
turn_end
  → analysis.pronunciation
  → analysis.correction
```

前端不能假设 `analysis.*` 在 `turn_end` 之前到达。

---

## 新增 HTTP 接口

### `GET /api/sessions/{session_id}/status`

查询会话状态与 summary 是否可取。

```json
{
  "session_id": "uuid",
  "state": "active",
  "summary_ready": false,
  "last_turn_id": "uuid",
  "last_error": null
}
```

---

## 内部事件总线（后端 A → B）

### `TurnTranscriptReadyEvent`

Conversation 模块（Dev A）在每轮结束后通过 event bus 发布，Coach 模块订阅消费。

```json
{
  "session_id": "uuid",
  "turn_id": "uuid",
  "scene_id": "interview",
  "difficulty": 2,
  "persona_id": "strict_interviewer",
  "transcript": "I would like to order a pasta, please.",
  "wav_audio_b64": "<base64 or null>",
  "assistant_reply_text": "Certainly. Would you like anything to drink with that?",
  "turn_duration_ms": 2840
}
```

`wav_audio_b64` 为 null 时，Coach 跳过发音评测，仍继续纠错分析。

---

## 错误码补充

| 错误码 | 含义 |
|--------|------|
| `PRON_ANALYSIS_FAILED` | 发音评测服务调用失败 |
| `CORRECTION_FAILED` | LLM 纠错服务调用失败 |
| `SUMMARY_NOT_READY` | summary 尚未生成完毕，可重试 |
