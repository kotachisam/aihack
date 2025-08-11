# ai_hack/config.py
from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # API Keys - matching .example.env variable names
    claude_api_key: str = ""
    google_api_key: str = ""
    openai_api_key: str = ""
    openai_api_version: str = "2024-02-01"
    fireworks_api_key: str = ""
    azure_openai_api_key: str = ""
    azure_openai_endpoint: str = ""
    azure_openai_deployment_name: str = ""
    azure_ai_api_key: str = ""
    azure_ai_endpoint: str = ""

    # Local Model Settings
    mixtral_url: str = "http://localhost:11434"

    # Safety Settings
    safety_level: str = "medium"
    max_file_size_mb: int = 5

    # Paths
    config_dir: Path = Path.home() / ".config" / "ai-hack"
    workspace_dir: Path = Path.home() / "ai-hack-workspace"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
