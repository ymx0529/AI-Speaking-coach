# Dev B 需求与接口速览

适用角色：Dev B  
负责模块：Coach Intelligence

---

## 1. 发音评测

**负责需求**
- 对用户每轮口语进行发音质量评估

**对应功能**
- 基于音频和 transcript 计算发音总分
- 输出准确度、流利度、完整度
- 标记低分单词和错误类型

**主要接口**
- 事件输入：`TurnTranscriptReadyEvent`
- WS 输出：`analysis.pronunciation`

**关键代码接口**
- `backend/app/modules/coach/pronunciation_service.py`
- `backend/app/modules/coach/turn_handler.py`
- `backend/app/modules/coach/store.py`

---

## 2. 语法 / 表达 / 词汇纠错

**负责需求**
- 指出用户本轮表达中的关键问题，并给出更自然的说法

**对应功能**
- 分析 grammar / expression / vocabulary 问题
- 返回纠错建议和简短解释
- 按严重程度排序

**主要接口**
- 事件输入：`TurnTranscriptReadyEvent`
- WS 输出：`analysis.correction`

**关键代码接口**
- `backend/app/modules/coach/correction_service.py`
- `backend/app/modules/coach/turn_handler.py`
- `frontend/src/modules/coach/CorrectionPanel.vue`

---

## 3. 单轮语言能力评分

**负责需求**
- 不只是给纠错，还要把本轮语言能力量化

**对应功能**
- 生成 `grammar_score`
- 生成 `expression_score`
- 生成 `vocabulary_score`
- 将分数与本轮纠错一起写入 Coach store

**主要接口**
- 内部分析结果：`TurnAnalysisReadyEvent`
- 共享模型：`CorrectionIssue`、回合评分字段

**关键代码接口**
- `backend/app/modules/coach/correction_service.py`
- `backend/app/modules/coach/store.py`
- `backend/app/core/types.py`
- `frontend/src/core/types.ts`

---

## 4. 教练分析结果实时回推

**负责需求**
- 分析完成后，前端能在当前会话里看到发音与纠错结果

**对应功能**
- 根据 `session_id` 回推分析事件
- 支持分析延迟到达
- 不影响主对话链路继续进行

**主要接口**
- WS：`analysis.pronunciation`
- WS：`analysis.correction`

**关键代码接口**
- `backend/app/modules/coach/turn_handler.py`
- `backend/app/modules/coach/register.py`
- `frontend/src/modules/coach/useCoach.ts`

---

## 5. 课后总结

**负责需求**
- 用户结束练习后，生成一份有量化数据的总结报告

**对应功能**
- 聚合多轮发音均分
- 聚合语言能力分数
- 统计纠错次数
- 输出教练点评与重点建议

**主要接口**
- HTTP：`POST /api/sessions/{session_id}/summary`

**关键代码接口**
- `backend/app/modules/coach/summary_service.py`
- `backend/app/modules/coach/router.py`
- `backend/app/modules/coach/store.py`

---

## 6. 总结页展示

**负责需求**
- 用户能直观看到本次练习结果与改进建议

**对应功能**
- 展示发音维度评分
- 展示语言维度评分
- 展示纠错统计
- 展示重点建议、空态、加载态、失败重试

**主要接口**
- HTTP：`POST /api/sessions/{session_id}/summary`

**关键代码接口**
- `frontend/src/modules/coach/useCoach.ts`
- `frontend/src/modules/coach/SessionSummaryPanel.vue`
- `frontend/src/core/store.ts`

---

## 7. Coach 自有数据真值

**负责需求**
- 教练分析必须有独立数据来源，不能依赖 Conversation 的临时状态

**对应功能**
- 用 `session_id + turn_id` 保存回合分析结果
- 支持 `pending / analyzed / failed`
- 为 summary 提供稳定数据源

**主要接口**
- 事件输入：`TurnTranscriptReadyEvent`
- 内部存储接口：Coach store

**关键代码接口**
- `backend/app/modules/coach/store.py`
- `backend/app/modules/coach/turn_handler.py`

---

## 8. Dev B 对 Dev A 的依赖

**必须由 Dev A 提供**
- `TurnTranscriptReadyEvent`
- `session_id`
- `turn_id`
- `transcript`
- 可消费音频或音频引用
- `assistant_reply_text`
- 会话结束后不立即清理 session

如果这些没冻结，Dev B 的发音评测和总结接口都不稳。
