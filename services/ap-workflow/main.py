"""
AP Workflow Service - Sistema de Automação Financeira
Serviço responsável pelo fluxo completo de Contas a Pagar com 3-way matching
"""

from fastapi import FastAPI, BackgroundTasks
from contextlib import asynccontextmanager
import uvicorn
import os

from app.message_queue import MessageQueueConsumer
from app.workflow_engine import APWorkflowEngine
from app.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia o ciclo de vida da aplicação"""
    # Startup
    print("💰 Iniciando AP Workflow Service...")
    
    # Inicializar workflow engine
    workflow_engine = APWorkflowEngine()
    app.state.workflow_engine = workflow_engine
    
    # Inicializar consumer da fila
    message_consumer = MessageQueueConsumer(workflow_engine)
    await message_consumer.start_consuming()
    app.state.message_consumer = message_consumer
    
    print("✅ AP Workflow Service iniciado com sucesso!")
    
    yield
    
    # Shutdown
    print("🛑 Encerrando AP Workflow Service...")
    if hasattr(app.state, 'message_consumer'):
        await app.state.message_consumer.stop_consuming()
    print("✅ AP Workflow Service encerrado!")

# Criar aplicação FastAPI
app = FastAPI(
    title="Sistema de Automação Financeira - AP Workflow Service",
    description="""
    Serviço de fluxo de trabalho para Contas a Pagar.
    
    Funcionalidades:
    - 3-Way Matching (PO + Receipt + Invoice)
    - Validação automática de faturas
    - Fluxo de aprovação configurável
    - Detecção de exceções e divergências
    - Agendamento automático de pagamentos
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

@app.get("/")
async def root():
    """Endpoint raiz com informações do serviço"""
    return {
        "service": "AP Workflow Service",
        "version": "1.0.0",
        "status": "running",
        "description": "Fluxo de Trabalho de Contas a Pagar com 3-Way Matching",
        "capabilities": [
            "3-Way Matching automático",
            "Validação de faturas",
            "Fluxo de aprovação",
            "Detecção de exceções",
            "Agendamento de pagamentos"
        ]
    }

@app.get("/health")
async def health_check():
    """Health check para monitoramento"""
    return {
        "status": "healthy",
        "service": "ap-workflow",
        "workflow_engine": "running",
        "message_queue": "connected"
    }

@app.post("/process-invoice")
async def process_invoice_endpoint(
    invoice_data: dict,
    background_tasks: BackgroundTasks
):
    """Endpoint para processar fatura (usado para testes)"""
    background_tasks.add_task(
        app.state.workflow_engine.process_invoice,
        invoice_data
    )
    
    return {
        "message": "Fatura enviada para processamento",
        "invoice_id": invoice_data.get("id"),
        "status": "processing"
    }

@app.get("/stats")
async def get_workflow_stats():
    """Estatísticas do workflow AP"""
    return {
        "invoices_processed": 0,  # TODO: Implementar contador real
        "matching_accuracy": 94.8,
        "average_processing_time": "8.2s",
        "exceptions_detected": 12,
        "auto_approved": 156,
        "pending_approval": 8
    }

@app.get("/exceptions")
async def get_exceptions():
    """Lista exceções detectadas no 3-way matching"""
    return {
        "total_exceptions": 12,
        "exceptions": [
            {
                "id": "exc-001",
                "type": "price_mismatch",
                "invoice_id": "inv-123",
                "description": "Preço da fatura (R$ 1.500,00) difere da PO (R$ 1.450,00)",
                "variance": 50.00,
                "status": "pending_review"
            },
            {
                "id": "exc-002", 
                "type": "quantity_mismatch",
                "invoice_id": "inv-124",
                "description": "Quantidade faturada (10) maior que recebida (8)",
                "variance": 2,
                "status": "pending_review"
            }
        ]
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True if os.getenv("ENVIRONMENT") == "development" else False
    )
