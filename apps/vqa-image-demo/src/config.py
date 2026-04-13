from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = ""
    s3_bucket_name: str = ""
    s3_access_key: str = ""
    s3_secret_key: str = ""
    replicate_api_token: str = ""
    openai_api_key: str = ""
    illusion_service_url: str = ""
    receipt_service_url: str = ""
    mouse_service_url: str = ""
    
    # Supabase (Legacy support)
    supabase_url: str = "dummy"
    supabase_key: str = "dummy"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
