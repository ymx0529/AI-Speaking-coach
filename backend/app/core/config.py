from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_ENV_FILE = Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT_ENV_FILE, env_file_encoding="utf-8")

    azure_speech_key: str = ""
    azure_speech_region: str = "eastasia"
    dashscope_api_key: str = ""
    dashscope_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    qwen_asr_model: str = "qwen3-asr-flash"
    qwen_chat_model: str = "qwen3.5-flash"
    qwen_enable_thinking: bool = True
    qwen_input_language: str = "en"
    qwen_request_timeout_sec: int = 30
    cosyvoice_api_url: str = "https://dashscope.aliyuncs.com/api/v1/services/audio/tts/SpeechSynthesizer"
    cosyvoice_model: str = "cosyvoice-v3-flash"
    cosyvoice_voice: str = "longanyang"
    cosyvoice_format: str = "wav"
    cosyvoice_sample_rate: int = 16000
    ffmpeg_binary: str = ""
    llm_api_key: str = ""
    llm_base_url: str = "https://api.deepseek.com/v1"
    llm_model: str = "deepseek-chat"
    cors_origin: str = "http://localhost:5173"
    session_max_turns: int = 20


settings = Settings()

