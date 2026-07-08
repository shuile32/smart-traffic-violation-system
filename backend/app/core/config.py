"""应用配置"""

from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # 数据库
    DATABASE_URL: str = "mysql+pymysql://root:password@localhost:3306/traffic_violation"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT
    JWT_SECRET_KEY: str = "change-me-to-a-random-64-char-string"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 30

    # LLM — 智谱 GLM（OpenAI 兼容协议，env 切 provider）
    LLM_BASE_URL: str = "https://open.bigmodel.cn/api/paas/v4"
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "glm-4-flash"

    # 邮件 SMTP
    SMTP_HOST: str = "smtp.qq.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "noreply@traffic-violation.local"

    # 文件存储
    MEDIA_STORAGE_DIR: str = "./media"

    # 应用
    APP_NAME: str = "交通违章智能管理平台"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"
    MEDIA_URL_PREFIX: str = "/media"

    # 图片上传限制
    MAX_IMAGE_SIZE_MB: int = 10
    ALLOWED_IMAGE_TYPES: list[str] = ["image/jpeg", "image/png", "image/webp"]

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
