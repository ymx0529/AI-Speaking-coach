from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_ENV_FILE = Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT_ENV_FILE, env_file_encoding="utf-8")

    azure_speech_key: str = ""
    azure_speech_region: str = "eastasia"
    pronunciation_provider: str = "auto"
    xfyun_app_id: str = ""
    xfyun_api_key: str = ""
    xfyun_api_secret: str = ""
    xfyun_ise_ent: str = "en_vip"
    xfyun_ise_category: str = "read_sentence"
    xfyun_ise_aue: str = "raw"
    xfyun_ise_auf: str = "audio/L16;rate=16000"
    xfyun_ise_group: str = "adult"
    xfyun_ise_rst: str = "entirety"
    xfyun_ise_unite: str = "1"
    xfyun_ise_extra_ability: str = "multi_dimension"
    xfyun_ise_timeout_sec: int = 20
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
    cosyvoice_request_timeout_sec: int = 12
    ffmpeg_binary: str = ""
    llm_api_key: str = ""
    llm_base_url: str = "https://api.deepseek.com/v1"
    llm_model: str = "deepseek-chat"
    cors_origin: str = "http://localhost:5173"
    session_max_turns: int = 20


settings = Settings()

