from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    
    DATABASE_URL: str = "postgresql+asyncpg://Maira:admin@localhost:5432/mydb"
    
    
    REDIS_URL: str = "redis://localhost:6379/0"
    
  
    SECRET_KEY: str = "your-secret-key-here"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
 
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Notes API with Redis Caching"
    
  
    LOG_LEVEL: str = "INFO"
    
  
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    
   
    CACHE_TTL: int = 300  # 5 minutes default
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
