"""
Configuration loader - reads environment variables from .env.bot.secret.

Usage:
    from config import load_config, Config
    config = load_config()
    print(config.lms_api_url)
"""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass
class Config:
    """Bot configuration loaded from environment variables."""

    bot_token: str = ""
    lms_api_url: str = ""
    lms_api_key: str = ""
    llm_api_key: str = ""
    llm_api_base_url: str = ""
    llm_api_model: str = ""
    proxy_url: str = ""


def load_config() -> Config:
    """
    Load configuration from .env.bot.secret in the project root.

    Returns a Config dataclass with all settings.
    """
    # Find .env.bot.secret in the project root (parent of bot/)
    bot_dir = Path(__file__).parent
    project_root = bot_dir.parent
    env_file = project_root / ".env.bot.secret"

    # Load environment variables from file
    load_dotenv(env_file)

    return Config(
        bot_token=os.getenv("BOT_TOKEN", ""),
        lms_api_url=os.getenv("LMS_API_URL", ""),
        lms_api_key=os.getenv("LMS_API_KEY", ""),
        llm_api_key=os.getenv("LLM_API_KEY", ""),
        llm_api_base_url=os.getenv("LLM_API_BASE_URL", ""),
        llm_api_model=os.getenv("LLM_API_MODEL", ""),
        proxy_url=os.getenv("PROXY_URL", ""),
    )
