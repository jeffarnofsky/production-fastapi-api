from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    secret_key: SecretStr
    algorithm: str = "HS256"
    access_token_expire_minutes: int = Field(default=30, gt=0)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, value: SecretStr) -> SecretStr:
        secret = value.get_secret_value()

        if len(secret) < 32:
            raise ValueError(
                "SECRET_KEY must be at least 32 characters long"
            )

        if secret.lower().startswith("replace_with_"):
            raise ValueError(
                "Replace the example SECRET_KEY with a real secret"
            )

        return value

    @field_validator("algorithm")
    @classmethod
    def validate_algorithm(cls, value: str) -> str:
        if value != "HS256":
            raise ValueError(
                "Only HS256 is supported by this configuration"
            )
        return value


settings = Settings()
