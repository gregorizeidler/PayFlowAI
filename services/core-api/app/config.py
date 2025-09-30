"""
Configurações do Core API Service
"""

from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    """Configurações da aplicação"""
    
    # Database
    database_url: str = os.getenv("DATABASE_URL", "postgresql://dev_user:dev_password@postgres:5432/financial_automation")
    
    # Redis
    redis_url: str = os.getenv("REDIS_URL", "redis://redis:6379")
    
    # RabbitMQ
    rabbitmq_url: str = os.getenv("RABBITMQ_URL", "amqp://dev_user:dev_password@rabbitmq:5672/")
    
    # MinIO/S3
    minio_endpoint: str = os.getenv("MINIO_ENDPOINT", "minio:9000")
    minio_access_key: str = os.getenv("MINIO_ACCESS_KEY", "dev_user")
    minio_secret_key: str = os.getenv("MINIO_SECRET_KEY", "dev_password123")
    minio_bucket_name: str = os.getenv("MINIO_BUCKET_NAME", "financial-documents")
    minio_secure: bool = os.getenv("MINIO_SECURE", "false").lower() == "true"
    
    # JWT
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    algorithm: str = os.getenv("ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # Environment
    environment: str = os.getenv("ENVIRONMENT", "development")
    debug: bool = os.getenv("DEBUG", "true").lower() == "true"
    
    # External Services
    document_ingestion_url: str = os.getenv("DOCUMENT_INGESTION_URL", "http://document-ingestion:8000")
    ocr_nlp_url: str = os.getenv("OCR_NLP_URL", "http://ocr-nlp:8000")
    ap_workflow_url: str = os.getenv("AP_WORKFLOW_URL", "http://ap-workflow:8000")
    ar_workflow_url: str = os.getenv("AR_WORKFLOW_URL", "http://ar-workflow:8000")
    reconciliation_url: str = os.getenv("RECONCILIATION_URL", "http://reconciliation:8000")
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Instância global das configurações
settings = Settings()
