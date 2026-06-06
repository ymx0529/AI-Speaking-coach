# SpeakCoach

一个基于 Vue 3 + FastAPI 的 AI 英语口语陪练项目。

当前仓库已经接入：

- Qwen ASR：`qwen3-asr-flash`
- CosyVoice TTS：`cosyvoice-v3-flash`
- 本地规则式对话回复
- Azure 发音评测保留为可选能力

## Structure

- `backend/`: FastAPI app and shared types
- `frontend/`: Vue 3 app and placeholder modules
- `ai-coding/`: planning and design documents

## Local Setup

### 1. Conda 环境

```powershell
conda activate qniu
```

### 2. 后端依赖

```powershell
cd D:\Desktop\QiNiu
conda run -n qniu python -m pip install -e backend
```

### 3. 前端依赖

```powershell
cd D:\Desktop\QiNiu\frontend
npm.cmd install
```

## Start Services

### Backend

```powershell
cd D:\Desktop\QiNiu\backend
conda run -n qniu uvicorn app.main:app --reload --port 8000
```

### Frontend

```powershell
cd D:\Desktop\QiNiu\frontend
npm.cmd run dev
```

启动后：

- 前端页面：`http://localhost:5173`
- 后端健康检查：`http://localhost:8000/health`

## How To Test

### 真实录音测试

1. 打开前端页面
2. 选择任一场景，例如 `求职面试`
3. 浏览器允许麦克风权限
4. 点击 `点击开始录音`
5. 说一句英文，例如：`Hello, I would like to introduce myself.`
6. 再点一次按钮结束录音
7. 观察：
   - 页面出现识别文本
   - AI 返回下一句英文回复
   - 若 TTS 成功，会自动播放语音
   - 右侧纠错面板有结果
8. 点击 `结束对话`
9. 进入总结页，查看 summary 返回

### 模拟模式测试

如果当前浏览器无法调用麦克风，可以在会话页点击 `使用模拟模式`，验证完整链路是否能跑通。

## Notes

- `.env.example` 只保留占位符，不要把真实密钥提交进仓库。
- 当前 `.env` 已按本机环境准备好，供本地调试使用。
- 如果 CosyVoice 的默认音色 `longanyang` 不符合你的预期，可以改 `.env` 中的 `COSYVOICE_VOICE`。
- 如果 `ffmpeg` 没有加入系统 `PATH`，也可以直接在 `.env` 中配置 `FFMPEG_BINARY` 为 `ffmpeg.exe` 的绝对路径。
