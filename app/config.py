from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuração da API secundária (análise + IA)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # IA local via Ollama
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2:3b"  # troque para gemma2:2b se preferir

    # API externa de enriquecimento
    brasilapi_url: str = "https://brasilapi.com.br/api/cep/v2"


settings = Settings()
