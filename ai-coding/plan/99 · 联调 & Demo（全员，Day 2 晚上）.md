> 前提：feat/conversation 和 feat/coach 均已各自在本地自测通过。

---

联调任务清单

[] INT-1 Dev B：PR feat/coach → main，评审通过后合入
[] INT-2 Dev A：PR feat/conversation → main，评审通过后合入
[] INT-3 全员：从最新 main 拉取，本地启动后端 + 前端
[] INT-4 验证 Skeleton 预埋的 correction slot 已正常显示
[] INT-5 E2E 冒烟测试（3 个场景各一轮）
[] INT-6 发现问题 → 在各自模块文件内修复（不得越界改对方文件）
[] INT-7 录制 Demo 视频（2–3 分钟）
---

CorrectionPanel 联调检查点

由于 `App.vue` 已在 Phase 0 预埋 correction slot，联调阶段只检查两件事：

1. `ConversationRoom.vue` 中是否保留 `<slot name="correction" />`
2. `CorrectionPanel.vue` 在收到 `correction` 事件后是否能正常显示

联调阶段不再改 `frontend/src/App.vue`，避免破坏 Skeleton 冻结规则。

---

E2E 冒烟测试脚本

场景 1：求职面试
1. 打开 http://localhost:5173
2. 选择"求职面试"，难度"入门"，点击"开始练习"
3. 按住录音键，说："Hello, I am interested in this position."，松开
4. 预期：
  - 发音评分出现（overall ≥ 40，word 列表有高亮）
  - AI 语音回复（Jenny 声音）
  - 约 1s 后右侧出现纠错面板（或为空）
5. 再说 2–3 句，然后点击"结束"
6. 预期：跳转到总结页，显示评分卡片 + AI 教练点评
场景 2：餐厅点餐
- 选"餐厅点餐"，说："Can I have the pasta with tomato sauce please?"
- 验证 AI 角色是 Sam（服务员），回复语气友好
场景 3：商务会议
- 选"商务会议"，说："I think we should increase our marketing budget this quarter."
- 验证 AI 角色是 Jordan（同事），回复专业
---

PR 规范

Dev A 的 PR（feat/conversation → main）
- 标题：feat: conversation module — Azure STT/TTS + LLM dialog
- 描述包含：
  - 测试命令：pytest tests/conversation/ -v
  - 前端截图：SceneSelector + ConversationRoom
- 改动文件必须 100% 在 modules/conversation/ 和 tests/conversation/
Dev B 的 PR（feat/coach → main）
- 标题：feat: coach module — correction + session summary
- 描述包含：
  - 测试命令：pytest tests/coach/ -v
  - 前端截图：CorrectionPanel + SessionSummaryPanel
- 改动文件必须 100% 在 modules/coach/ 和 tests/coach/
常见联调问题排查

问题
排查步骤
WS 连接失败
确认 uvicorn 在 8000 端口；检查 CORS_ORIGIN=http://localhost:5173
Azure STT 返回空文字
检查音频格式：pydub 转换后是否为 16kHz WAV；检查 Azure key/region
发音评分全为 0
PronunciationAssessmentConfig.apply_to(recognizer) 是否在 recognize_once_async 前调用
LLM 返回乱码
llm_base_url 末尾不要有斜杠；检查 model name 是否正确
correction 事件未收到
检查 event_bus.subscribe 是否在 register_coach() 中调用；ws_hub session 是否注册
总结页 404
确认 Dev A 的 session_manager 和 Dev B 的 session_accumulator 用的是同一个 session_id（前端 store.sessionId）
前端无法播放音频
检查 base64 mp3 是否完整；确认浏览器已有用户交互（首次需要用户手势才能播放音频）

---

Demo 录制要点

1. 时长：2–3 分钟，完整展示一轮对话 + 纠错 + 课后总结
2. 内容：
- 场景选择（3 秒）
- 2–3 轮对话（清晰说话，让发音分数有变化）
- 展示纠错气泡
- 展示课后总结：评分卡片 + AI 点评
3. 工具：OBS Studio / Loom / QuickTime
