from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://forensics:forensics@db:5432/forensics_db"
    redis_url: str = "redis://redis:6379/0"
    secret_key: str = "changeme"
    access_token_expire_minutes: int = 480
    algorithm: str = "HS256"

    ansible_ssh_key_path: str = "/root/.ssh/ansible"
    linux_ansible_user: str | None = None
    linux_become_password: str | None = None
    artifacts_dir: str = "/app/artifacts"

    admin_username: str = "admin"
    admin_password: str = "admin"
    admin_email: str = "admin@localhost"


settings = Settings()
