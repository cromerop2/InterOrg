"""Carga y valida las variables de entorno una sola vez para toda la app."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Ruta absoluta al .env de backend/, para no depender del directorio de ejecución.
ENV_FILE = Path(__file__).resolve().parents[1] / ".env"


class Settings(BaseSettings):
    """Variables obligatorias: si falta alguna, la app falla al arrancar con un error claro."""

    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Las variables del entorno del sistema tienen prioridad sobre el archivo .env.
    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore")


settings = Settings()
