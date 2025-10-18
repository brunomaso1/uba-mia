from pathlib import Path
from typing import Optional
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from loguru import logger
import json

ROOT_DIR = Path(__file__).parent.parent.resolve()
env_file_path = ROOT_DIR / ".env"
env_file = str(env_file_path)

if env_file_path.exists():
    logger.warning(f"Using .env file at {env_file_path.resolve()} for configuration.")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=env_file, env_file_encoding="utf-8", extra="ignore")

    openrouter_api_key: Optional[str] = None
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_visual_model: Optional[str] = None

    openai_key: Optional[str] = None
    openai_visual_model: Optional[str] = None

    host: str = "visual-agent"
    port: int = 10000
    server_timeout_keep_alive: int = 300  # seconds

    should_scale_down_images: bool = False
    supported_mimes: set[str] = {"image/png", "image/jpeg", "image/jpg", "image/webp"}

    @model_validator(mode="after")
    def check_keys_and_models(self):
        """Ensure consistency between API keys and models, and at least one provider configured."""
        openrouter_ok = bool(self.openrouter_api_key and self.openrouter_visual_model)
        openai_ok = bool(self.openai_key and self.openai_visual_model)

        if not openrouter_ok and not openai_ok:
            raise ValueError(
                "Error de configuración. Se requiere al menos un proveedor de LLM: "
                "OpenRouter (openrouter_api_key + openrouter_model) "
                "o OpenAI (openai_key + openai_model). Esto debe venir en el archivo .env o en las variables de entorno."
            )

        if self.openrouter_api_key and not self.openrouter_visual_model:
            raise ValueError(
                "Error de configuración: está configurado openrouter_api_key pero falta openrouter_model. Esto debe venir en el archivo .env o en las variables de entorno. Puedes ver un ejemplo en .env.example."
            )

        if self.openai_key and not self.openai_visual_model:
            raise ValueError(
                "Error de configuración: está configurado openai_key pero falta openai_model. Esto debe venir en el archivo .env o en las variables de entorno. Puedes ver un ejemplo en .env.example."
            )

        return self


settings = Settings()
logger.debug(f"Configuration loaded: {json.dumps(settings.model_dump(), indent=2, default=str)}")
