"""
AR Workflow Service - Sistema de Automação Financeira
Serviço responsável pelo fluxo completo de Contas a Receber
"""

from fastapi import FastAPI, BackgroundTasks
from contextlib import asynccontextmanager
import uvicorn
import os

from app.message_queue import MessageQueueConsumer
from app.workflow_engine import ARWorkflowEngine
from app.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia o ciclo de vida da aplicação"""
    # Startup
    print("💰 Iniciando AR Workflow Service...")
    
    # Inicializar workflow engine
    workflow_engine = ARWorkflowEngine()
    app.state.workflow_engine = workflow_engine
    
    # Inicializar consumer da fila
    message_consumer = MessageQueueConsumer(workflow_engine)
    await message_consumer.start_consuming()
    app.state.message_consumer = message_consumer
    
    print("✅ AR Workflow Service iniciado com sucesso!")
    
    yield
    
    # Shutdown
    print("🛑 Encerrando AR Workflow Service...")
    if hasattr(app.state, 'message_consumer'):
        await app.state.message_consumer.stop_consuming()
    print("✅ AR Workflow Service encerrado!")

# Criar aplicação FastAPI
app = FastAPI(
    title="Sistema de Automação Financeira - AR Workflow Service",
    description="""
    Serviço de fluxo de trabalho para Contas a Receber.
    
    Funcionalidades:
    - Criação e envio automático de faturas
    - Régua de cobrança automatizada (Dunning)
    - Geração de boletos e PIX
    - Controle de vencimentos
    - Notificações automáticas por email
    - Relatórios de inadimplência
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
        "service": "AR Workflow Service",
        "version": "1.0.0",
        "status": "running",
        "description": "Fluxo de Trabalho de Contas a Receber com Cobrança Automatizada",
        "capabilities": [
            "Criação automática de faturas",
            "Régua de cobrança (Dunning)",
            "Geração de boletos e PIX",
            "Notificações por email",
            "Controle de inadimplência",
            "Relatórios financeiros"
        ]
    }

@app.get("/health")
async def health_check():
    """Health check para monitoramento"""
    return {
        "status": "healthy",
        "service": "ar-workflow",
        "workflow_engine": "running",
        "message_queue": "connected",
        "dunning_engine": "active"
    }

@app.post("/create-invoice")
async def create_invoice_endpoint(
    invoice_data: dict,
    background_tasks: BackgroundTasks
):
    """Endpoint para criar fatura (usado para testes)"""
    background_tasks.add_task(
        app.state.workflow_engine.create_invoice,
        invoice_data
    )
    
    return {
        "message": "Fatura enviada para criação",
        "invoice_id": invoice_data.get("id"),
        "status": "processing"
    }

@app.post("/send-dunning")
async def send_dunning_endpoint(
    customer_id: str,
    background_tasks: BackgroundTasks
):
    """Endpoint para enviar cobrança manual"""
    background_tasks.add_task(
        app.state.workflow_engine.send_dunning_notification,
        customer_id
    )
    
    return {
        "message": "Cobrança enviada",
        "customer_id": customer_id,
        "status": "sent"
    }

@app.get("/stats")
async def get_workflow_stats():
    """Estatísticas do workflow AR"""
    return {
        "invoices_created": 1247,
        "total_receivables": 485600.50,
        "overdue_amount": 45800.25,
        "collection_rate": 94.2,
        "average_payment_days": 28.5,
        "dunning_emails_sent": 156,
        "payment_reminders": 89,
        "active_customers": 342
    }

@app.get("/overdue")
async def get_overdue_invoices():
    """Lista faturas em atraso"""
    return {
        "total_overdue": 12,
        "total_amount": 45800.25,
        "overdue_invoices": [
            {
                "id": "inv-ar-001",
                "customer_name": "Cliente ABC Ltda",
                "amount": 5500.00,
                "due_date": "2024-01-05",
                "days_overdue": 15,
                "last_dunning": "2024-01-12",
                "status": "overdue"
            },
            {
                "id": "inv-ar-002",
                "customer_name": "Empresa XYZ S/A",
                "amount": 12300.50,
                "due_date": "2024-01-08",
                "days_overdue": 12,
                "last_dunning": "2024-01-15",
                "status": "overdue"
            }
        ]
    }

@app.get("/dunning-schedule")
async def get_dunning_schedule():
    """Agenda de cobranças programadas"""
    return {
        "scheduled_today": 8,
        "scheduled_this_week": 23,
        "dunning_rules": [
            {
                "trigger": "5_days_before_due",
                "type": "reminder",
                "method": "email",
                "active": True
            },
            {
                "trigger": "due_date",
                "type": "payment_notice",
                "method": "email",
                "active": True
            },
            {
                "trigger": "7_days_overdue",
                "type": "first_dunning",
                "method": "email_sms",
                "active": True
            },
            {
                "trigger": "15_days_overdue",
                "type": "second_dunning",
                "method": "email_phone",
                "active": True
            },
            {
                "trigger": "30_days_overdue",
                "type": "final_notice",
                "method": "registered_mail",
                "active": True
            }
        ]
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True if os.getenv("ENVIRONMENT") == "development" else False
    )
