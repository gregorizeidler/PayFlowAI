"""
Configurações do Reconciliation Service
"""

from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    """Configurações da aplicação"""
    
    # Database
    database_url: str = os.getenv("DATABASE_URL", "postgresql://dev_user:dev_password@postgres:5432/financial_automation")
    
    # RabbitMQ
    rabbitmq_url: str = os.getenv("RABBITMQ_URL", "amqp://dev_user:dev_password@rabbitmq:5672/")
    
    # Redis
    redis_url: str = os.getenv("REDIS_URL", "redis://redis:6379")
    
    # Fuzzy Matching Configuration
    similarity_threshold: float = 0.8  # Threshold mínimo para auto-match
    auto_match_threshold: float = 0.95  # Threshold para matching automático
    manual_review_threshold: float = 0.7  # Threshold para revisão manual
    
    # Amount Tolerance
    amount_tolerance_percent: float = 2.0  # 2% de tolerância
    amount_tolerance_absolute: float = 10.0  # R$ 10,00 de tolerância absoluta
    
    # Date Tolerance
    date_tolerance_before: int = 5  # 5 dias antes
    date_tolerance_after: int = 10  # 10 dias depois
    
    # Processing Configuration
    max_transactions_per_batch: int = 1000
    processing_timeout_seconds: int = 300  # 5 minutos
    
    # File Processing
    max_file_size_mb: int = 50
    supported_formats: list = ["ofx", "csv", "pdf"]
    
    # Reconciliation Rules
    enable_fuzzy_matching: bool = True
    enable_amount_matching: bool = True
    enable_date_matching: bool = True
    enable_description_matching: bool = True
    enable_reference_matching: bool = True
    
    # Performance
    parallel_processing: bool = True
    max_workers: int = 4
    
    # Environment
    environment: str = os.getenv("ENVIRONMENT", "development")
    debug: bool = os.getenv("DEBUG", "true").lower() == "true"
    
    # External Services
    core_api_url: str = os.getenv("CORE_API_URL", "http://core-api:8000")
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Instância global das configurações
settings = Settings()
