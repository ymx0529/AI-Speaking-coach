from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    azure_speech_key: str = ""
    azure_speech_region: str = "eastasia"
    llm_api_key: str = ""
    llm_base_url: str = "https://api.deepseek.com/v1"
    llm_model: str = "deepseek-chat"
    cors_origin: str = "http://localhost:5173"
    session_max_turns: int = 20


settings = Settings()

