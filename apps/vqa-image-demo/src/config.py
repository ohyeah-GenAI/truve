from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # DB 연결 (MySQL RDS)
    database_url: str = ""

    # AWS S3
    s3_bucket_name: str = ""
    s3_access_key: str = ""
    s3_secret_key: str = ""
    s3_region: str = "ap-northeast-2"

    # 외부 API
    openai_api_key: str = ""

    # 내부 모듈 통신 URL (ModuleController용)
    illusion_service_url: str = "http://illusion-service:8001"
    receipt_service_url: str = "http://receipt-service:8002"
    mouse_service_url: str = "http://mouse-service:8003"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
