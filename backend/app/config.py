from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator, Field

class Config(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/netra"
    GROQ_API_KEY: str | None = None
    LITELLM_API_KEY: str | None = None
    OPENAI_API_KEY: str | None = None
    GOOGLE_API_KEY: str | None = None
    NETRA_API_KEY: str = ""
    NETRA_OTLP_ENDPOINT: str = ""

    @model_validator(mode="after")
    def llm_api_key_validator(self) -> 'Config':
        if not any([self.GROQ_API_KEY, self.LITELLM_API_KEY, self.OPENAI_API_KEY, self.GOOGLE_API_KEY]):
            raise ValueError("Set the LLM api key(s)")
            
        return self
    
config = Config()