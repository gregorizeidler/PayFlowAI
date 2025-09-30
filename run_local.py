#!/usr/bin/env python3
"""
Script para rodar o sistema localmente sem Docker
Usa SQLite em memória para ser mais rápido nos testes
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def setup_environment():
    """Configura variáveis de ambiente para execução local"""
    # Carregar variáveis do arquivo .env se existir
    env_file = Path(".env")
    if env_file.exists():
        print("📄 Carregando configurações do arquivo .env...")
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
    
    # Configurações padrão para desenvolvimento local
    default_config = {
        # Database (SQLite em memória para testes rápidos)
        "DATABASE_URL": "sqlite:///./test_financial.db",
        
        # Desabilitar serviços externos para testes
        "REDIS_URL": "redis://localhost:6379",
        "RABBITMQ_URL": "amqp://guest:guest@localhost:5672/",
        
        # MinIO local (opcional)
        "MINIO_ENDPOINT": "localhost:9000",
        "MINIO_ACCESS_KEY": "minioadmin",
        "MINIO_SECRET_KEY": "minioadmin",
        "MINIO_SECURE": "false",
        
        # JWT (usar variável de ambiente se disponível)
        "SECRET_KEY": os.getenv("SECRET_KEY", "test-secret-key-for-local-development-only"),
        "ALGORITHM": "HS256",
        "ACCESS_TOKEN_EXPIRE_MINUTES": "30",
        
        # Environment
        "ENVIRONMENT": "development",
        "DEBUG": "true",
    }
    
    # Aplicar configurações padrão apenas se não estiverem definidas
    for key, value in default_config.items():
        if key not in os.environ:
            os.environ[key] = value

def install_dependencies():
    """Instala dependências do Core API"""
    print("📦 Instalando dependências...")
    
    core_api_path = Path("services/core-api")
    if not core_api_path.exists():
        print("❌ Diretório services/core-api não encontrado!")
        return False
    
    try:
        # Instalar dependências
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", 
            str(core_api_path / "requirements.txt")
        ], check=True, cwd=core_api_path)
        
        print("✅ Dependências instaladas!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao instalar dependências: {e}")
        return False

def create_simple_database():
    """Cria um banco SQLite simples para testes"""
    print("🗄️ Criando banco de dados SQLite...")
    
    # Adicionar SQLAlchemy ao path
    sys.path.insert(0, str(Path("services/core-api")))
    
    try:
        from sqlalchemy import create_engine, text
        from app.models import Base
        
        # Criar engine SQLite
        engine = create_engine("sqlite:///./test_financial.db", echo=True)
        
        # Criar todas as tabelas
        Base.metadata.create_all(engine)
        
        # Inserir dados de exemplo
        with engine.connect() as conn:
            # Empresa de exemplo
            conn.execute(text("""
                INSERT OR IGNORE INTO companies (id, name, cnpj, email, phone, address, is_active)
                VALUES (
                    'company-test-id',
                    'Empresa Demo LTDA',
                    '12.345.678/0001-90',
                    'contato@empresademo.com.br',
                    '(11) 99999-9999',
                    'Rua das Flores, 123 - São Paulo, SP',
                    1
                )
            """))
            
            # Usuário de exemplo (senha: admin123)
            conn.execute(text("""
                INSERT OR IGNORE INTO users (id, company_id, email, password_hash, first_name, last_name, role, is_active)
                VALUES (
                    'user-test-id',
                    'company-test-id',
                    'admin@empresademo.com.br',
                    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4Ov0BqZXvO',
                    'Admin',
                    'Sistema',
                    'admin',
                    1
                )
            """))
            
            # Fornecedor de exemplo
            conn.execute(text("""
                INSERT OR IGNORE INTO suppliers (id, company_id, name, cnpj, email, phone, is_active)
                VALUES (
                    'supplier-test-id',
                    'company-test-id',
                    'Fornecedor ABC LTDA',
                    '98.765.432/0001-10',
                    'contato@fornecedorabc.com.br',
                    '(11) 88888-8888',
                    1
                )
            """))
            
            conn.commit()
        
        print("✅ Banco de dados criado com dados de exemplo!")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao criar banco: {e}")
        return False

def run_core_api():
    """Executa o Core API localmente"""
    print("🚀 Iniciando Core API...")
    
    core_api_path = Path("services/core-api")
    
    try:
        # Executar FastAPI com uvicorn
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "main:app", 
            "--host", "0.0.0.0", 
            "--port", "8000", 
            "--reload"
        ], cwd=core_api_path)
        
    except KeyboardInterrupt:
        print("\n🛑 Parando Core API...")
    except Exception as e:
        print(f"❌ Erro ao executar Core API: {e}")

def main():
    """Função principal"""
    print("🎯 Sistema de Automação Financeira - Execução Local")
    print("=" * 60)
    
    # Configurar ambiente
    setup_environment()
    
    # Verificar se está no diretório correto
    if not Path("services/core-api").exists():
        print("❌ Execute este script no diretório raiz do projeto!")
        return
    
    # Instalar dependências
    if not install_dependencies():
        return
    
    # Criar banco de dados
    if not create_simple_database():
        return
    
    print("\n🎉 Sistema configurado! Iniciando servidor...")
    print("📚 API Docs: http://localhost:8000/docs")
    print("🔍 Health Check: http://localhost:8000/health")
    print("📊 Dashboard Stats: http://localhost:8000/api/v1/dashboard/stats")
    print("\n⚠️  Pressione Ctrl+C para parar o servidor")
    print("-" * 60)
    
    # Executar Core API
    run_core_api()

if __name__ == "__main__":
    main()
