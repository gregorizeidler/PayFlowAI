"""
Configurações do OCR/NLP Service
"""

from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    """Configurações da aplicação"""
    
    # RabbitMQ
    rabbitmq_url: str = os.getenv("RABBITMQ_URL", "amqp://dev_user:dev_password@rabbitmq:5672/")
    
    # MinIO/S3
    minio_endpoint: str = os.getenv("MINIO_ENDPOINT", "minio:9000")
    minio_access_key: str = os.getenv("MINIO_ACCESS_KEY", "dev_user")
    minio_secret_key: str = os.getenv("MINIO_SECRET_KEY", "dev_password123")
    minio_bucket_name: str = os.getenv("MINIO_BUCKET_NAME", "financial-documents")
    minio_secure: bool = os.getenv("MINIO_SECURE", "false").lower() == "true"
    
    # OCR Settings
    tesseract_cmd: str = "/usr/bin/tesseract"
    tesseract_config: str = "--oem 3 --psm 6"
    ocr_languages: str = "por+eng"
    
    # NLP Settings
    spacy_model: str = "pt_core_news_sm"
    
    # Processing Settings
    max_image_size: int = 4096  # pixels
    image_quality: int = 95
    pdf_dpi: int = 300
    
    # Confidence Thresholds
    min_ocr_confidence: float = 60.0
    min_extraction_confidence: float = 70.0
    
    # Environment
    environment: str = os.getenv("ENVIRONMENT", "development")
    debug: bool = os.getenv("DEBUG", "true").lower() == "true"
    
    # Core API URL
    core_api_url: str = os.getenv("CORE_API_URL", "http://core-api:8000")
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Instância global das configurações
settings = Settings()
