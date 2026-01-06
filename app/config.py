from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    pg_host: str = Field(validation_alias="PGHOST")
    pg_user: str = Field(validation_alias="PGUSER")
    pg_password: str = Field(validation_alias="PGPASSWORD")
    pg_port: int = Field(5432, validation_alias="PGPORT")
    pg_database: str = Field(validation_alias="PGDATABASE")

    rabbitmq_host: str = Field("rabbitmq", validation_alias="RABBITMQ_HOST")
    payment_confirmed_queue: str = Field("payment_confirmed", validation_alias="PAYMENT_CONFIRMED_QUEUE")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

settings = Settings()
