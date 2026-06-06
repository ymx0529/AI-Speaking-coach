# Dev B 教练智能实施计划

> **供执行型 Agent 使用：** 实施本计划时，建议使用 `superpowers:subagent-driven-development` 或 `superpowers:executing-plans`，并按任务逐项勾选执行。

**目标：** 完成教练智能层，使每一轮用户输入都能得到发音分析与语言纠错，并在整场练习结束后生成可量化、可执行的总结反馈。

**架构说明：** Dev B 负责“用户说得怎么样”这条分析链路。后端 `coach` 模块消费 `TurnTranscriptReadyEvent`，完成发音评测、语言质量分析、回合聚合与会话总结，并暴露 summary 接口。前端 `coach` 模块负责展示纠错卡片、延迟分析态和最终总结页，不直接依赖 Conversation 内部状态。

**技术栈：** FastAPI、Vue 3、Pinia、Azure Pronunciation Assessment 或等价发音评测链路、OpenAI 兼容 LLM API、pytest、pytest-asyncio

---

## 职责范围

Dev B 独占以下目录：
- `backend/app/modules/coach/**`
- `backend/tests/coach/**`
- `frontend/src/modules/coach/**`

Dev B 依赖但不拥有的共享层：
- `PROTOCOL.md`
- `backend/app/core/types.py`
- `frontend/src/core/types.ts`
- `backend/app/core/event_bus.py`
- `frontend/src/core/store.ts`

Dev B 不应继续依赖这些临时实现：
- 直接从 `backend/app/modules/conversation/session_manager.py` 读取最终 summary 真值
- 依赖仅存在于 mock 路由里的临时事件名

Coach 模块应成为以下内容的唯一业务真值来源：
- `analysis.pronunciation`
- `analysis.correction`
- 每轮语言能力评分
- `SessionSummaryResponse`

---

## 前置条件

正式开发前必须先统一这些内容：

- [ ] 冻结 `TurnTranscriptReadyEvent` 载荷，至少包含 `session_id`、`turn_id`、`scene_id`、`difficulty`、`persona_id`、`transcript`、音频引用、`assistant_reply_text`、`turn_duration_ms`
- [ ] 在 `PROTOCOL.md` 中冻结 Coach 相关 WS 事件名
- [ ] 在 `backend/app/core/types.py` 与 `frontend/src/core/types.ts` 中冻结共享模型
- [ ] 给 summary 相关类型补齐字段：`grammar_score`、`expression_score`、`vocabulary_score`、`avg_response_latency_ms`、`focus_recommendations`
- [ ] 决定旧事件 `pron_score`、`correction` 是否保留短期兼容
- [ ] 确认 session 保留策略，保证 `session.finish` 后 Coach summary 仍可读取
- [ ] 在 `backend/pyproject.toml` 中补齐 Dev B 所需依赖：Azure Speech SDK 或发音评测依赖、OpenAI client、pytest、pytest-asyncio

如果 `TurnTranscriptReadyEvent` 中没有可消费的音频或音频引用，不要进入任务 3。

---

### 任务 1：冻结教练分析契约与评分模型

**涉及文件：**
- 修改：`PROTOCOL.md`
- 修改：`backend/app/core/types.py`
- 修改：`frontend/src/core/types.ts`
- 修改：`frontend/src/core/store.ts`
- 复核：`documents/ai-speaking-coach-dual-dev-spec-20260606.md`

- [ ] 定义 Coach 所有的 WS 事件名：`analysis.pronunciation`、`analysis.correction`，以及必要的分析就绪状态
- [ ] 给 `CorrectionIssue` 增加至少 `severity`
- [ ] 扩展 summary 类型，补齐最终总结页所需的语言与体验指标
- [ ] 明确 `turn.completed` 到底表示“主链路回复完成”还是“包含分析在内的整轮完成”；必要时单独增加 ready 语义
- [ ] 定义 summary 就绪规则，让前端知道何时拉取或重试
- [ ] 如果前端需要同时兼容旧事件名与新事件名，写明过渡规则

执行后验证：
- `cd backend && python -m compileall app`
- `cd frontend && npm run type-check`

完成标准：
- Dev B 的后端输出和前端渲染拥有统一目标模型

---

### 任务 2：搭建 Coach 回合存储与事件消费骨架

**涉及文件：**
- 修改：`backend/app/modules/coach/register.py`
- 修改：`backend/app/modules/coach/turn_handler.py`
- 新建：`backend/app/modules/coach/store.py`
- 测试：`backend/tests/coach/test_store.py`
- 测试：`backend/tests/coach/test_turn_handler.py`

- [ ] 将空的 `turn_handler.py` 升级为真实事件消费者
- [ ] 建立以 `session_id + turn_id` 为键的 Coach 自有存储
- [ ] 每轮至少维护三种状态：`pending`、`analyzed`、`failed`
- [ ] 保证存储不依赖 Conversation 会话的短生命周期
- [ ] 让事件消费具备幂等性，避免重复事件导致重复统计
- [ ] 增加测试：
  - [ ] 创建 session 桶
  - [ ] 单轮只写入一次
  - [ ] 同一 `turn_id` 重放仍安全
  - [ ] 分析失败后仍保留 transcript 基础数据

执行验证：
- `cd backend && pytest tests/coach/test_store.py tests/coach/test_turn_handler.py -q`

完成标准：
- 即使还没接入真实分析服务，Dev B 也能先稳定接收并存储每轮数据

---

### 任务 3：实现发音评测链路

**涉及文件：**
- 新建：`backend/app/modules/coach/pronunciation_service.py`
- 修改：`backend/app/modules/coach/turn_handler.py`
- 测试：`backend/tests/coach/test_pronunciation_service.py`

- [ ] 建立独立的发音评测服务，直接消费冻结后的回合事件
- [ ] 使用音频与 transcript 计算 `overall`、`accuracy`、`fluency`、`completeness`、`words[]`
- [ ] 统一处理缺音频、空 transcript、评分结果不完整等失败场景
- [ ] 将发音分析结果写回 Coach store 的对应 `turn_id`
- [ ] 分析成功后通过 WS 推送 `analysis.pronunciation`
- [ ] 增加测试：
  - [ ] 正常评分结构正确
  - [ ] 空 transcript 快速返回
  - [ ] 缺失音频的错误处理
  - [ ] 发音评分结果可正确序列化为 WS payload

执行验证：
- `cd backend && pytest tests/coach/test_pronunciation_service.py tests/coach/test_turn_handler.py -q`

完成标准：
- 发音评分完全收口到 Coach，而不再属于 Conversation

---

### 任务 4：实现纠错与语言评分链路

**涉及文件：**
- 新建：`backend/app/modules/coach/correction_service.py`
- 修改：`backend/app/modules/coach/turn_handler.py`
- 修改：`frontend/src/modules/coach/CorrectionPanel.vue`
- 测试：`backend/tests/coach/test_correction_service.py`

- [ ] 基于 transcript 与 AI reply 上下文生成语法、表达、词汇问题
- [ ] 控制问题数量，避免纠错提示过多影响节奏
- [ ] 给每条纠错增加 `severity`，用于前端排序
- [ ] 为每轮计算 `grammar_score`、`expression_score`、`vocabulary_score`
- [ ] 将纠错结果和语言评分写入 Coach store
- [ ] 根据契约，在发音分析之后或并行推送 `analysis.correction`
- [ ] 更新 `CorrectionPanel.vue`，支持空态、分析中、按严重级别排序展示
- [ ] 增加测试：
  - [ ] 无错误时返回空数组
  - [ ] LLM 返回非法结构时安全降级
  - [ ] `severity` 排序稳定
  - [ ] 前端可展示多种问题类别

执行验证：
- `cd backend && pytest tests/coach/test_correction_service.py -q`
- `cd frontend && npm run type-check`

完成标准：
- Dev B 可输出可展示、可排序、可量化的单轮语言反馈

---

### 任务 5：实现课后总结聚合与 Summary API

**涉及文件：**
- 修改：`backend/app/modules/coach/router.py`
- 新建：`backend/app/modules/coach/summary_service.py`
- 修改：`backend/app/modules/coach/store.py`
- 测试：`backend/tests/coach/test_summary_service.py`
- 测试：`backend/tests/coach/test_router_summary.py`

- [ ] 停止将 Conversation session 数据作为 summary 的主真值
- [ ] 从 Coach 自有回合记录中聚合会话级均分
- [ ] 在发音均分之外，输出语言维度评分和可执行建议
- [ ] 明确处理这些状态：
  - [ ] session 不存在
  - [ ] session 存在但还没有分析完成的回合
  - [ ] summary 请求早于分析完成
- [ ] 即使部分回合分析失败，也要返回稳定的 `SessionSummaryResponse`
- [ ] 增加测试：
  - [ ] 空 session 返回
  - [ ] 多轮平均值计算正确
  - [ ] 建议生成失败时能回退
  - [ ] 404 与 not-ready 行为清晰

执行验证：
- `cd backend && pytest tests/coach/test_summary_service.py tests/coach/test_router_summary.py -q`

完成标准：
- Summary 能稳定生成，且不再依赖 Conversation 的临时 turns

---

### 任务 6：完成 Coach 前端数据流与展示

**涉及文件：**
- 新建：`frontend/src/modules/coach/useCoach.ts`
- 修改：`frontend/src/modules/coach/CorrectionPanel.vue`
- 修改：`frontend/src/modules/coach/SessionSummaryPanel.vue`
- 修改：`frontend/src/core/store.ts`
- 修改：`frontend/src/mock/events.ts`

- [ ] 新建 `useCoach.ts`，统一订阅 Coach WS 分析事件并拉取 summary
- [ ] 将适合复用的 summary 请求逻辑从组件中抽离
- [ ] 让 `CorrectionPanel.vue` 只读取 Coach 事件与共享状态
- [ ] 让 `SessionSummaryPanel.vue` 至少展示：
  - [ ] 发音维度指标
  - [ ] 语言维度指标
  - [ ] 总纠错数
  - [ ] 重点建议
  - [ ] 加载、空态、失败重试
- [ ] 保持 mock 支持，保证 Dev B 不依赖真实语音链路也能迭代 UI

执行验证：
- `cd frontend && npm run type-check`
- `cd frontend && npm run build`

完成标准：
- Dev B 可以独立用 mock 数据或真实事件演示教练 UI

---

### 任务 7：与 Dev A 联调实时推送与 summary 就绪状态

**涉及文件：**
- 修改：`backend/app/modules/coach/turn_handler.py`
- 修改：`backend/app/modules/coach/router.py`
- 修改：`backend/app/modules/coach/store.py`
- 协同：`backend/app/modules/conversation/router.py`

- [ ] 验证 `TurnTranscriptReadyEvent` 对每轮只到达一次
- [ ] 使用 `session_id` 将发音与纠错结果回推到正确的 WS 会话
- [ ] 让 summary 就绪状态对前端可观测
- [ ] 确认 Dev A 已经停止直接发送 Coach 分析结果
- [ ] 确认 `session.finish` 不会打断待完成的 Coach 分析
- [ ] 增加一条跨模块联调测试或检查清单，覆盖“事件发布 -> Coach 分析 -> summary 获取”

执行验证：
- `cd backend && pytest tests/coach -q`

完成标准：
- Dev B 已从 mock 集成升级为真实主链路集成

---

### 任务 8：最终验收与交接清单

**涉及文件：**
- 测试：`backend/tests/coach/**`
- 修改：`frontend/src/mock/events.ts`
- 复核：`documents/ai-speaking-coach-dual-dev-spec-20260606.md`

- [ ] 验证一条纯 mock 单轮链路：UI 能展示发音分析与纠错
- [ ] 验证一条 mock 多轮链路：summary 能稳定生成
- [ ] 验证至少一个真实场景、两轮以上的联调链路
- [ ] 验证分析延迟不会破坏会话页展示
- [ ] 验证 `session.finish` 后不会再因为过早清理导致假 404
- [ ] 补充交接说明：事件顺序、summary ready 行为、已知失败模式

执行验证：
- `cd backend && pytest tests/coach -q`
- `cd frontend && npm run type-check && npm run build`

完成标准：
- Dev B 可向最终联调和 demo 录制阶段交付稳定的教练智能模块

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
- 任务 1 冻结模型后，任务 4、任务 5、任务 6 都可以先用 mock 数据推进
- 任务 3 必须等待 Dev A 在 `TurnTranscriptReadyEvent` 中提供可消费音频

## 完成定义

- Dev B 完整拥有发音分析、纠错分析和总结生成
- Coach 不再依赖 Conversation 的临时 turns 作为最终真值
- 前端可同时展示单轮延迟分析和多轮总结
- 用户结束会话后 summary 仍然可取
- 教练智能链路既能用 mock 验证，也能用真实数据联调
