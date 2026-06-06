# Dev A 会话运行时实施计划

> **供执行型 Agent 使用：** 实施本计划时，建议使用 `superpowers:subagent-driven-development` 或 `superpowers:executing-plans`，并按任务逐项勾选执行。

**目标：** 完成从“用户开始练习 -> 上传一轮语音 -> 返回识别结果 -> 生成 AI 回复 -> 将本轮数据交给 Coach 分析”的会话主链路。

**架构说明：** Dev A 负责“用户说话 -> 系统回复”的主流程。后端 `conversation` 模块负责 WebSocket 会话生命周期、回合状态、音频接收、ASR、回复生成、TTS，以及发布 `TurnTranscriptReadyEvent`。前端 `conversation` 模块负责场景进入、录音控制、识别文本展示、AI 回复展示，并消费冻结后的共享契约。

**技术栈：** FastAPI、WebSocket、Vue 3、Pinia、Azure Speech SDK、OpenAI 兼容 LLM API、pydub/ffmpeg、pytest、pytest-asyncio

---

## 职责范围

Dev A 独占以下目录：
- `backend/app/modules/conversation/**`
- `backend/tests/conversation/**`
- `frontend/src/modules/conversation/**`

Dev A 依赖但不拥有的共享层：
- `PROTOCOL.md`
- `backend/app/core/types.py`
- `frontend/src/core/types.ts`
- `backend/app/core/event_bus.py`
- `frontend/src/core/ws.ts`
- `frontend/src/core/store.ts`

以下内容不再由 Dev A 负责业务实现：
- `analysis.pronunciation`
- `analysis.correction`
- `SessionSummaryResponse` 的评分逻辑

以上分析能力归 Dev B 所有。

---

## 前置条件

正式开发前必须先统一这些内容：

- [ ] 在 `PROTOCOL.md` 冻结升级后的 WS 事件名和字段
- [ ] 在 `backend/app/core/event_bus.py` 与 `backend/app/core/types.py` 中冻结 `TurnTranscriptReadyEvent`
- [ ] 在 `backend/app/core/types.py` 与 `frontend/src/core/types.ts` 中冻结前后端共享类型
- [ ] 确认 `frontend/src/core/ws.ts` 是否需要兼容旧事件名
- [ ] 明确会话保留规则：`session.finish` 不能立即删除会话状态
- [ ] 在 `backend/pyproject.toml` 中补齐 Dev A 所需依赖：Azure Speech SDK、OpenAI client、pydub、multipart、pytest、pytest-asyncio

如果共享契约还没有冻结，不要进入任务 2 之后的开发。

---

### 任务 1：冻结会话链路契约与依赖基线

**涉及文件：**
- 修改：`PROTOCOL.md`
- 修改：`backend/app/core/types.py`
- 修改：`frontend/src/core/types.ts`
- 修改：`frontend/src/core/ws.ts`
- 修改：`frontend/src/core/store.ts`
- 修改：`backend/pyproject.toml`

- [ ] 确认 Dev A 主链路事件集合：`session.start`、`session.ready`、`audio.append`、`turn.started`、`asr.partial`、`user_turn.final`、`assistant.reply_text`、`assistant.reply_audio`、`turn.completed`、`error`
- [ ] 补齐主链路所需字段：`session_id`、`turn_id`、`client_ts`、`server_ts`、`encoding`、`is_last`、`retryable`
- [ ] 将 `pron_score`、`correction` 从 Dev A 自有事件中移除，或明确标为 Dev B 分析事件
- [ ] 定义 `TurnTranscriptReadyEvent` 载荷，保证 Dev B 无需依赖 Conversation 内部状态也能分析本轮
- [ ] 更新 `backend/pyproject.toml` 依赖清单
- [ ] 如果需要兼容旧事件名，补充一段过渡说明

执行后验证：
- 后端类型检查：`cd backend && python -m compileall app`
- 前端类型检查：`cd frontend && npm run type-check`

完成标准：
- 共享契约只冻结一次
- A/B 可在不反复改 `turn_id` 和事件归属的前提下并行开发

---

### 任务 2：重构会话与回合状态管理

**涉及文件：**
- 修改：`backend/app/modules/conversation/session_manager.py`
- 测试：`backend/tests/conversation/test_session_manager.py`

- [ ] 将当前最小缓存结构升级为显式会话模型，至少包含 `session_id`、`scene_id`、`difficulty`、`persona_id`、当前回合状态、音频缓冲、历史消息、保留状态
- [ ] 增加这些函数能力：开始会话、开始回合、追加 chunk、结束回合、写入历史、读取会话状态、延迟清理
- [ ] 将 `turn_id` 生成收口到会话状态流中，不再由路由临时处理
- [ ] 保留足够的上下文给 LLM，但不要把 Coach 负责的分析数据混入 Conversation 状态
- [ ] 为以下场景补单测：
  - [ ] 启动会话时生成干净状态
  - [ ] 第一段音频会自动开启一轮
  - [ ] 多个 chunk 会按顺序累积
  - [ ] 回合结束只清理本轮缓冲
  - [ ] `session.finish` 后仍可查询
  - [ ] 只有过期会话才被真正清理

执行验证：
- `cd backend && pytest tests/conversation/test_session_manager.py -q`

完成标准：
- 会话生命周期清晰
- 用户结束会话后不会立刻影响 summary 获取

---

### 任务 3：将 WebSocket 路由升级为回合状态机

**涉及文件：**
- 修改：`backend/app/modules/conversation/router.py`
- 修改：`backend/app/modules/conversation/register.py`
- 测试：`backend/tests/conversation/test_router_protocol.py`

- [ ] 用冻结后的 WS 协议替换当前 `session_start / audio_end / turn_end` 的 mock 流程
- [ ] 接收 `session.start` 并返回 `session.ready`
- [ ] 在收到首个合法音频 chunk 时创建回合并发送 `turn.started`
- [ ] 正常接收带 `seq`、`encoding`、`is_last` 的 `audio.append`
- [ ] 在 `is_last=true` 时结束当前音频采集并进入处理状态
- [ ] 对异常事件、缺失 session、错误序号、解码失败返回统一的 `error`
- [ ] 单轮失败后保持 WS 连接不断开，允许继续练习
- [ ] 停止由 Conversation 直接发送 Coach 负责的业务事件
- [ ] 增加路由测试：
  - [ ] 未 `session.start` 就发音频
  - [ ] 正常一轮事件顺序正确
  - [ ] 非法事件名
  - [ ] 畸形 payload
  - [ ] 一轮失败后还能恢复

执行验证：
- `cd backend && pytest tests/conversation/test_router_protocol.py -q`

完成标准：
- WS 层足够稳定，可同时支撑前端联调和 Coach 集成

---

### 任务 4：补齐音频转换与 ASR 适配层

**涉及文件：**
- 新建：`backend/app/modules/conversation/audio_utils.py`
- 新建：`backend/app/modules/conversation/azure_speech.py`
- 修改：`backend/app/modules/conversation/router.py`
- 测试：`backend/tests/conversation/test_audio_utils.py`
- 测试：`backend/tests/conversation/test_azure_speech_adapter.py`

- [ ] 实现浏览器音频 chunk 合并，并转为 PCM WAV `16kHz / 16-bit / mono`
- [ ] 将 ffmpeg/pydub 处理逻辑封装在 `audio_utils.py`
- [ ] 提供可产出 `asr.partial` 与 `user_turn.final` 的 ASR 适配接口
- [ ] 保留 mock 路径，便于本地无 Azure key 时继续开发
- [ ] 将适配层错误统一为路由级错误码，例如 `AUDIO_DECODE_FAILED`、`ASR_FAILED`
- [ ] 增加测试：
  - [ ] 正常转换
  - [ ] 非法音频转换失败
  - [ ] ASR 返回最终识别文本与时长
  - [ ] 适配器错误可稳定映射到路由错误事件

执行验证：
- `cd backend && pytest tests/conversation/test_audio_utils.py tests/conversation/test_azure_speech_adapter.py -q`

完成标准：
- 无论走真实链路还是 mock 链路，识别输出都能挂在稳定的路由契约上

---

### 任务 5：补齐对话 LLM、TTS 与事件总线交接

**涉及文件：**
- 新建：`backend/app/modules/conversation/llm_client.py`
- 修改：`backend/app/modules/conversation/azure_speech.py`
- 修改：`backend/app/modules/conversation/router.py`
- 修改：`backend/app/modules/conversation/session_manager.py`
- 测试：`backend/tests/conversation/test_llm_client.py`

- [ ] 根据 `scene_id`、`persona_id`、`difficulty` 和有限历史生成 AI 回复
- [ ] 控制回复长度，保证口语交互节奏自然
- [ ] 为最终回复生成 TTS 音频
- [ ] 固定事件顺序：`user_turn.final` -> `assistant.reply_text` -> `assistant.reply_audio` -> 发布 `TurnTranscriptReadyEvent` -> `turn.completed`
- [ ] 发布完整的 `TurnTranscriptReadyEvent`，至少包含 transcript、音频引用、回复文本、回合时长、会话元数据
- [ ] 如果 TTS 失败，仍要返回 `assistant.reply_text`，不能中断整轮
- [ ] 增加测试：
  - [ ] 历史截断有效
  - [ ] 回复生成受场景与 persona 控制
  - [ ] TTS 失败不导致整轮失败
  - [ ] 每轮只发布一次事件总线消息

执行验证：
- `cd backend && pytest tests/conversation/test_llm_client.py tests/conversation/test_router_protocol.py -q`

完成标准：
- Conversation 模块完整拥有“用户一轮输入 -> AI 一轮输出”的主链路

---

### 任务 6：完成前端会话流转

**涉及文件：**
- 新建：`frontend/src/modules/conversation/useConversation.ts`
- 修改：`frontend/src/modules/conversation/SceneSelector.vue`
- 修改：`frontend/src/modules/conversation/ConversationRoom.vue`
- 修改：`frontend/src/modules/conversation/PronScoreBar.vue`
- 修改：`frontend/src/core/store.ts`
- 测试：`frontend/src/mock/events.ts`

- [ ] 将 WS 订阅和消息映射从 `ConversationRoom.vue` 下沉到 `useConversation.ts`
- [ ] 更新 `SceneSelector.vue`，支持选择难度、persona、建会话、处理建连失败
- [ ] 将当前“模拟一轮对话”替换为真实会话动作：开始录音、结束录音、等待处理、展示识别文本与 AI 回复
- [ ] 键盘增强可以保留，但按钮交互必须可用
- [ ] 让 `ConversationRoom.vue` 明确展示这些状态：空闲、录音中、处理中、AI 播放中、错误
- [ ] 保持 `PronScoreBar.vue` 为被动展示组件，能容忍 Dev B 的分析结果延迟到达
- [ ] 使用 `frontend/src/mock/events.ts` 保留无后端的 UI 调试路径

执行验证：
- `cd frontend && npm run type-check`
- `cd frontend && npm run build`

完成标准：
- Dev A 可以分别用 mock 数据和真实后端演示完整会话页

---

### 任务 7：补齐会话结束、状态查询与总结交接

**涉及文件：**
- 修改：`backend/app/modules/conversation/register.py`
- 修改：`backend/app/modules/conversation/router.py`
- 修改：`backend/app/modules/conversation/session_manager.py`
- 修改：`frontend/src/modules/conversation/ConversationRoom.vue`
- 协同：`backend/app/modules/coach/router.py`

- [ ] 将 `session.finish` 实现为状态变更，而不是立即删除
- [ ] 增加或暴露 session 状态查询接口，让前端能判断 summary 是否可取
- [ ] 将前端“结束”按钮正确接入结束流程并进入 summary 页
- [ ] 确保用户结束后 Dev B 仍能读取或汇总分析结果
- [ ] 记录清理触发方式：TTL 或显式 `summary_ack`

执行验证：
- `cd backend && pytest tests/conversation -q`
- `cd frontend && npm run type-check`

完成标准：
- Dev A 不会再因为过早清理会话而导致 summary 404

---

### 任务 8：联调验收与交接清单

**涉及文件：**
- 测试：`backend/tests/conversation/**`
- 修改：`frontend/src/mock/events.ts`
- 复核：`documents/ai-speaking-coach-dual-dev-spec-20260606.md`

- [ ] 验证一条成功链路：连接 -> 音频上传 -> partial -> final -> 回复文本 -> 回复音频 -> 回合完成
- [ ] 验证一条失败链路：坏音频或 ASR 失败返回稳定 `error`，且 WS 可继续使用
- [ ] 验证一次交接：每轮只发布一次 `TurnTranscriptReadyEvent`
- [ ] 验证前端能容忍 Dev B 的分析事件延迟到达
- [ ] 补充给 Dev B 的交接说明：事件顺序、关键字段、已知边界情况

执行验证：
- `cd backend && pytest tests/conversation -q`
- `cd frontend && npm run type-check && npm run build`

完成标准：
- Dev A 可向 Dev B 和最终联调阶段交付稳定的会话运行时

---

## 建议执行顺序

1. 任务 1
2. 任务 2
3. 任务 3
4. 任务 4
5. 任务 5
6. 任务 6
7. 任务 7
8. 任务 8

并行建议：
- 任务 1 冻结共享契约后，任务 6 可以先基于 mock 开始
- 任务 4 和任务 5 在 key 未就绪时也可以先走 mock 适配器开发

## 完成定义

- Dev A 不再直接产出 Coach 负责的分析结果
- 升级后的 WS 协议能够支撑完整一轮会话
- 前端会话页可以同时支持 mock 事件和真实事件
- `TurnTranscriptReadyEvent` 能按冻结字段稳定发布
- 用户结束会话后不会影响 summary 获取
