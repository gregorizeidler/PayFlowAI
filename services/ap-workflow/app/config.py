"""
Configurações do AP Workflow Service
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
    
    # 3-Way Matching Configuration
    price_tolerance_percent: float = 5.0  # Tolerância de 5% para diferenças de preço
    quantity_tolerance_percent: float = 2.0  # Tolerância de 2% para diferenças de quantidade
    date_tolerance_days: int = 7  # Tolerância de 7 dias para datas
    
    # Approval Workflow Configuration
    auto_approval_limit: float = 1000.00  # Aprovação automática até R$ 1.000
    manager_approval_limit: float = 10000.00  # Aprovação gerencial até R$ 10.000
    director_approval_limit: float = 50000.00  # Aprovação diretoria até R$ 50.000
    
    # Processing Configuration
    max_retry_attempts: int = 3
    retry_delay_seconds: int = 60
    
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
