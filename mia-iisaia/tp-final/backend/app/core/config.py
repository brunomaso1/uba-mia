import json

from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://expense_user:changeme@localhost:5432/expense_db"
    keycloak_url: str = "http://localhost:8080"
    keycloak_realm: str = "expense-app"
    keycloak_client_id: str = "expense-frontend"
    backend_cors_origins: list[str] = ["http://localhost:4200"]

    @field_validator("backend_cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: object) -> list[str]:
        if isinstance(v, str):
            return json.loads(v)
        return v

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
