from pydantic import BaseSettings


class Settings(BaseSettings):
    database_hostname: str
    database_port: str
    database_password: str
    database_name: str
    database_username: str
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int
    box_uganda_username: str
    box_uganda_password: str
    twilio_account_sid: str
    twilio_auth_token: str

    class Config:
        env_file =".env"



settings = Settings()
