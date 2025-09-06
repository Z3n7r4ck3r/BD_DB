from pydantic import BaseSettings

class Settings(BaseSettings):
    database_url: str = ""
    redis_url: str = ""
    jwt_secret_key: str = "changeme"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    admin_email: str = "admin@example.com"
    admin_password: str = "admin"

    class Config:
        env_file = ".env"

settings = Settings()
