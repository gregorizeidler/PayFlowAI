"""
Core API Service - Sistema de Automação Financeira
Serviço principal que orquestra todos os outros microsserviços
"""

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from contextlib import asynccontextmanager
import uvicorn
import os
from typing import Optional

from app.database import engine, get_db
from app.models import Base
from app.routers import auth, companies, suppliers, customers, documents, accounts_payable, accounts_receivable
from app.config import settings
from app.services.message_queue import MessageQueueService

# Security
security = HTTPBearer()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia o ciclo de vida da aplicação"""
    # Startup
    print("🚀 Iniciando Core API Service...")
    
    # Criar tabelas do banco de dados
    Base.metadata.create_all(bind=engine)
    
    # Inicializar serviços
    message_queue = MessageQueueService()
    await message_queue.connect()
    app.state.message_queue = message_queue
    
    print("✅ Core API Service iniciado com sucesso!")
    
    yield
    
    # Shutdown
    print("🛑 Encerrando Core API Service...")
    if hasattr(app.state, 'message_queue'):
        await app.state.message_queue.disconnect()
    print("✅ Core API Service encerrado!")

# Criar aplicação FastAPI
app = FastAPI(
    title="Sistema de Automação Financeira - Core API",
    description="""
    API principal do sistema de automação de contas a pagar e receber.
    
    Este serviço orquestra todos os outros microsserviços e fornece:
    - Autenticação e autorização
    - Gerenciamento de empresas, fornecedores e clientes
    - Coordenação dos fluxos de AP e AR
    - Interface unificada para o frontend
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://frontend:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Autenticação"])
app.include_router(companies.router, prefix="/api/v1/companies", tags=["Empresas"])
app.include_router(suppliers.router, prefix="/api/v1/suppliers", tags=["Fornecedores"])
app.include_router(customers.router, prefix="/api/v1/customers", tags=["Clientes"])
app.include_router(documents.router, prefix="/api/v1/documents", tags=["Documentos"])
app.include_router(accounts_payable.router, prefix="/api/v1/ap", tags=["Contas a Pagar"])
app.include_router(accounts_receivable.router, prefix="/api/v1/ar", tags=["Contas a Receber"])

@app.get("/")
async def root():
    """Endpoint raiz com informações do serviço"""
    return {
        "service": "Core API",
        "version": "1.0.0",
        "status": "running",
        "description": "Sistema de Automação Financeira - API Principal"
    }

@app.get("/health")
async def health_check():
    """Health check para monitoramento"""
    return {
        "status": "healthy",
        "service": "core-api",
        "database": "connected",
        "message_queue": "connected" if hasattr(app.state, 'message_queue') else "disconnected"
    }

@app.get("/api/v1/dashboard/stats")
async def get_dashboard_stats(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db = Depends(get_db)
):
    """Estatísticas para o dashboard principal"""
    # TODO: Implementar lógica de autenticação
    # TODO: Buscar estatísticas reais do banco
    
    return {
        "accounts_payable": {
            "total": 150,
            "pending_approval": 12,
            "overdue": 5,
            "total_amount": 125000.50
        },
        "accounts_receivable": {
            "total": 89,
            "overdue": 8,
            "paid_this_month": 45,
            "total_amount": 89500.75
        },
        "documents": {
            "processed_today": 23,
            "pending_processing": 7,
            "ocr_accuracy": 96.5
        },
        "cash_flow": {
            "inflow_this_month": 156000.00,
            "outflow_this_month": 98000.00,
            "net_flow": 58000.00
        }
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True if os.getenv("ENVIRONMENT") == "development" else False
    )
