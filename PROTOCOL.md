# SpeakCoach WebSocket Protocol v1

## Connection

- URL: `ws://{host}/ws/session/{session_id}`
- Client generates `session_id` and sends `session_start` after connect.

## Client -> Server

### `session_start`

```json
{
  "type": "session_start",
  "scene_id": "interview",
  "difficulty": 1,
  "persona_id": "strict_interviewer"
}
```

### `audio_chunk`

```json
{
  "type": "audio_chunk",
  "data": "<base64 webm chunk>",
  "seq": 0
}
```

### `audio_end`

```json
{
  "type": "audio_end",
  "seq_count": 12
}
```

### `session_end`

```json
{
  "type": "session_end"
}
```

## Server -> Client

- `asr_partial`
- `asr_final`
- `pron_score`
- `reply_text`
- `reply_audio`
- `correction`
- `turn_end`
- `error`

