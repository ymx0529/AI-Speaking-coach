# Dev B Coach Intelligence — 实施设计文档

更新时间：2026-06-06
适用范围：Dev B（`lsz` 分支）整个开发周期的冲突规避与任务执行

---

## 1. 核心原则

Dev B 独占以下目录，PR 期间不与 Dev A 产生文件交叉：

```
backend/app/modules/coach/**
backend/tests/coach/**
frontend/src/modules/coach/**
```

Dev B **主导且唯一负责** Phase 0 共享文件升级。Dev A 在 Phase 0 PR 合并后才开始改任何文件，这样从根本上消除共享文件的 merge conflict。

---

## 2. PR 顺序与分支规则

```
main
 └─ lsz（你的主分支，PR 到 main）
      ├─ PR 0：Phase 0 契约冻结（共享文件，Dev A review 后合并）
      ├─ PR 1：Task 2 — Coach 存储与事件消费骨架
      ├─ PR 2：Task 3 — 发音评测链路
      ├─ PR 3：Task 4 — 纠错与语言评分链路
      ├─ PR 4：Task 5 — 总结聚合与 Summary API
      ├─ PR 5：Task 6 — Coach 前端数据流与展示
      └─ PR 6：Task 7 — 联调
```

**规则：**
- 每个 PR 只包含当前任务涉及的文件，不捎带无关改动
- PR 0 必须合并到 main 后，Dev A 才能从 main 切自己的分支
- PR 1 开始，每个 PR 在上一个合并后再开，避免本地积压多个任务的未合并状态
- PR 6（联调）需要 Dev A 同步完成 `conversation/router.py` 的相关改动（见第 5 节）

---

## 3. PR 0：Phase 0 共享契约升级（最高优先级）

**目标**：一次性冻结所有跨人协作边界，之后 Dev A 和 Dev B 均不再改共享文件。

### 3.1 `PROTOCOL.md` — 从 v1 升级到 v2

删除旧事件名，全部替换为点分命名，并补充回合状态事件和 Coach 分析事件。

| 旧事件名（删除） | 新事件名 | 归属 |
|---|---|---|
| `session_start` | `session.start` | Dev A |
| `audio_chunk` | `audio.append` | Dev A |
| `audio_end` | （合并到 `audio.append` is_last=true） | Dev A |
| `session_end` | `session.finish` | Dev A |
| `asr_partial` | `asr.partial` | Dev A |
| `asr_final` | `user_turn.final` | Dev A |
| `reply_text` | `assistant.reply_text` | Dev A |
| `reply_audio` | `assistant.reply_audio` | Dev A |
| `pron_score` | `analysis.pronunciation` | **Dev B** |
| `correction` | `analysis.correction` | **Dev B** |
| `turn_end` | `turn.completed` | Dev A 发出时机，Dev B 在分析完成后确认 |

新增必须记录的事件：
- `session.ready`（Server → Client）：会话初始化成功
- `turn.started`（Server → Client）：含 `turn_id`，前端用于关联后续所有分析事件

完整字段结构参照 `documents/ai-speaking-coach-dual-dev-spec-20260606.md` 第 6.1 节。

### 3.2 `backend/app/core/types.py`

在现有类型基础上做以下修改，**不删除**现有字段（向前兼容，等 Dev A PR 合并后再一起清理旧字段）：

```python
# CorrectionIssue 新增
severity: Literal["high", "medium", "low"]

# SessionSummaryResponse 新增
grammar_score: float
expression_score: float
vocabulary_score: float
avg_response_latency_ms: int
focus_recommendations: list[str]

# 替换 SpeakerTurnEvent（保留原名作为 alias 直到 Dev A 切换完毕）
class TurnTranscriptReadyEvent(BaseModel):
    session_id: str
    turn_id: str
    scene_id: str
    difficulty: int
    persona_id: str
    transcript: str
    wav_audio_b64: str | None  # 发音评测必须有此字段
    assistant_reply_text: str
    turn_duration_ms: int

# 新增 Dev B 内部事件
class TurnAnalysisReadyEvent(BaseModel):
    session_id: str
    turn_id: str
    pronunciation: dict
    corrections: list
    grammar_score: float
    expression_score: float
    vocabulary_score: float
```

### 3.3 `frontend/src/core/types.ts`

与 `types.py` 保持镜像，新增：

```typescript
// CorrectionIssue 新增
severity: 'high' | 'medium' | 'low'

// SessionSummaryResponse 新增
grammar_score: number
expression_score: number
vocabulary_score: number
avg_response_latency_ms: number
focus_recommendations: string[]

// TurnTranscriptReadyEvent（内部用，前端不消费，但类型文件里记录供文档参考）
```

### 3.4 `frontend/src/core/store.ts`

在现有 Pinia store 中，**在对话状态区块之后**，追加 Coach 专属状态区，并加注释边界标记，Dev A 不应改动此区块之后的内容：

```typescript
// ── Coach 分析状态（Dev B 维护区）────────────────────────
pronunciationByTurn: Record<string, PronScore>   // turn_id → 发音结果
correctionsByTurn: Record<string, CorrectionIssue[]>  // turn_id → 纠错列表
coachAnalysisStatus: Record<string, 'pending' | 'analyzed' | 'failed'>
summaryReady: boolean
summaryLoading: boolean
// ────────────────────────────────────────────────────────
```

### 3.5 `backend/app/core/event_bus.py`

将事件类型泛型从 `SpeakerTurnEvent` 改为 `TurnTranscriptReadyEvent`，或升级为泛型 Any 支持多事件类型（由于当前实现是简单 dict，主要是确保 subscribe/publish 签名不再硬编码旧类型名）。

### PR 0 验收标准

```bash
cd backend && python -m compileall app
cd frontend && npm run type-check
```

两个命令均通过，且 Dev A 已在 PR 上完成 review。

---

## 4. PR 1–6：Dev B 独占任务

以下任务全部只改 `backend/app/modules/coach/**`、`backend/tests/coach/**`、`frontend/src/modules/coach/**`，不碰共享文件。

### PR 1 — Coach 存储与事件消费骨架（Task 2）

**新增文件：**
- `backend/app/modules/coach/store.py`：以 `session_id + turn_id` 为主键，维护 `pending / analyzed / failed` 三态

**修改文件：**
- `backend/app/modules/coach/register.py`
- `backend/app/modules/coach/turn_handler.py`：从空实现升级为真实消费 `TurnTranscriptReadyEvent`

**测试：**
- `backend/tests/coach/test_store.py`
- `backend/tests/coach/test_turn_handler.py`

验收：`pytest tests/coach/test_store.py tests/coach/test_turn_handler.py -q` 通过

---

### PR 2 — 发音评测链路（Task 3）

**前置条件（阻塞项）：**
> Dev A 必须在 `TurnTranscriptReadyEvent` 的 `wav_audio_b64` 字段中提供可消费音频。在确认 Dev A 已提供音频之前，此 PR 不进入开发，用 mock 音频先跑通流程。

**新增文件：**
- `backend/app/modules/coach/pronunciation_service.py`

**修改文件：**
- `backend/app/modules/coach/turn_handler.py`：调用发音服务，写回 store，推送 `analysis.pronunciation`

**测试：**
- `backend/tests/coach/test_pronunciation_service.py`

验收：`pytest tests/coach/test_pronunciation_service.py tests/coach/test_turn_handler.py -q` 通过

---

### PR 3 — 纠错与语言评分链路（Task 4）

**新增文件：**
- `backend/app/modules/coach/correction_service.py`

**修改文件：**
- `backend/app/modules/coach/turn_handler.py`：并行或串行调用纠错服务，推送 `analysis.correction`
- `frontend/src/modules/coach/CorrectionPanel.vue`：支持空态、加载中、按 `severity` 排序

**测试：**
- `backend/tests/coach/test_correction_service.py`

验收：
```bash
pytest tests/coach/test_correction_service.py -q
cd frontend && npm run type-check
```

---

### PR 4 — 总结聚合与 Summary API（Task 5）

**新增文件：**
- `backend/app/modules/coach/summary_service.py`

**修改文件：**
- `backend/app/modules/coach/router.py`：`POST /api/sessions/{session_id}/summary` 改为从 Coach store 聚合
- `backend/app/modules/coach/store.py`：增加 session 级聚合方法

**测试：**
- `backend/tests/coach/test_summary_service.py`
- `backend/tests/coach/test_router_summary.py`

不再从 `conversation/session_manager.py` 读取数据。

验收：`pytest tests/coach/test_summary_service.py tests/coach/test_router_summary.py -q` 通过

---

### PR 5 — Coach 前端数据流与展示（Task 6）

**新增文件：**
- `frontend/src/modules/coach/useCoach.ts`：统一订阅 `analysis.*` 事件，封装 summary 拉取逻辑

**修改文件：**
- `frontend/src/modules/coach/CorrectionPanel.vue`：只读 store coach 区
- `frontend/src/modules/coach/SessionSummaryPanel.vue`：展示发音 + 语言维度 + 建议 + 重试
- `frontend/src/mock/events.ts`：补充 `analysis.pronunciation`、`analysis.correction` mock 数据

**注意**：`store.ts` 的 Coach 状态区已在 PR 0 中建立，此 PR 只通过 `useCoach.ts` 读写，不新增 store 字段。

验收：
```bash
cd frontend && npm run type-check && npm run build
```

---

### PR 6 — 联调（Task 7）

**前置条件（两个阻塞项）：**
1. Dev A 已从 `conversation/router.py` 删除直接发送 `correction` 和 `pron_score` 的逻辑
2. Dev A 已确认每轮只发布一次 `TurnTranscriptReadyEvent`

**改动范围：**
- `backend/app/modules/coach/turn_handler.py`：确认幂等性
- `backend/app/modules/coach/router.py`：补充 `summary_ready` 状态
- `backend/app/modules/coach/store.py`：确认 session 结束后数据不丢失

**跨模块检查清单：**
- [ ] 同一 `turn_id` 贯穿 `TurnTranscriptReadyEvent` → Coach 分析 → `analysis.*` WS 推送
- [ ] `session.finish` 后 summary 仍可取（不因 Conversation session 清理而 404）
- [ ] Dev A 已停止直接发送 Coach 分析结果

验收：`pytest tests/coach -q` 全部通过

---

## 5. 对 Dev A 的依赖与沟通要点

下表是需要提前告知 Dev A 的内容，以免他走错方向：

| 时机 | 需要告知 Dev A 的事 |
|---|---|
| PR 0 之前 | 请等 PR 0 合并后再从 main 切你的分支，避免共享文件冲突 |
| PR 0 review 时 | 确认 `TurnTranscriptReadyEvent` 字段（尤其是 `wav_audio_b64`）他可以提供 |
| PR 2 之前 | 确认他的 `conversation/router.py` 能在事件里带上音频，否则 PR 2 先用 mock |
| PR 6 之前 | 他需要先删掉 `router.py` 里直接发 `correction` / `pron_score` 的代码 |

---

## 6. 完成定义

- Dev B 独占目录通过所有 pytest + type-check + build
- 发音、纠错、总结均由 Coach 模块统一产出，不依赖 Conversation 私有状态
- 前端可用 mock 数据独立演示教练 UI
- session 结束后 summary 稳定可取
- 联调链路覆盖"事件发布 → Coach 分析 → summary 获取"端到端
