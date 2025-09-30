"""
Configurações do AR Workflow Service
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
    
    # Dunning Configuration
    dunning_enabled: bool = True
    reminder_days_before_due: int = 5
    first_dunning_days_after_due: int = 7
    second_dunning_days_after_due: int = 15
    final_notice_days_after_due: int = 30
    
    # Email Configuration
    smtp_server: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_username: str = os.getenv("SMTP_USERNAME", "")
    smtp_password: str = os.getenv("SMTP_PASSWORD", "")
    from_email: str = os.getenv("FROM_EMAIL", "noreply@financialautomation.com")
    
    # Payment Configuration
    payment_gateway_url: str = os.getenv("PAYMENT_GATEWAY_URL", "https://api.pagarmepay.com")
    payment_gateway_key: str = os.getenv("PAYMENT_GATEWAY_KEY", "")
    pix_key: str = os.getenv("PIX_KEY", "")
    
    # Invoice Configuration
    invoice_due_days_default: int = 30
    late_fee_percentage: float = 2.0  # 2% ao mês
    interest_rate_daily: float = 0.033  # 1% ao mês / 30 dias
    
    # Notification Configuration
    max_dunning_attempts: int = 5
    dunning_cooldown_hours: int = 24
    
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
