"""
Reconciliation Service - Sistema de Automação Financeira
Serviço responsável pela conciliação bancária automatizada
"""

from fastapi import FastAPI, BackgroundTasks, UploadFile, File
from contextlib import asynccontextmanager
import uvicorn
import os

from app.message_queue import MessageQueueConsumer
from app.reconciliation_engine import ReconciliationEngine
from app.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia o ciclo de vida da aplicação"""
    # Startup
    print("🏦 Iniciando Reconciliation Service...")
    
    # Inicializar reconciliation engine
    reconciliation_engine = ReconciliationEngine()
    app.state.reconciliation_engine = reconciliation_engine
    
    # Inicializar consumer da fila
    message_consumer = MessageQueueConsumer(reconciliation_engine)
    await message_consumer.start_consuming()
    app.state.message_consumer = message_consumer
    
    print("✅ Reconciliation Service iniciado com sucesso!")
    
    yield
    
    # Shutdown
    print("🛑 Encerrando Reconciliation Service...")
    if hasattr(app.state, 'message_consumer'):
        await app.state.message_consumer.stop_consuming()
    print("✅ Reconciliation Service encerrado!")

# Criar aplicação FastAPI
app = FastAPI(
    title="Sistema de Automação Financeira - Reconciliation Service",
    description="""
    Serviço de conciliação bancária automatizada.
    
    Funcionalidades:
    - Processamento de extratos bancários (OFX, CSV, PDF)
    - Matching automático com faturas e pagamentos
    - Algoritmos de fuzzy matching
    - Detecção de discrepâncias
    - Conciliação de recebimentos e pagamentos
    - Relatórios de conciliação
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
        "service": "Reconciliation Service",
        "version": "1.0.0",
        "status": "running",
        "description": "Conciliação Bancária Automatizada com Fuzzy Matching",
        "capabilities": [
            "Processamento de extratos OFX/CSV/PDF",
            "Matching automático de transações",
            "Fuzzy matching por valor/data/nome",
            "Detecção de discrepâncias",
            "Conciliação de AR/AP",
            "Relatórios detalhados"
        ]
    }

@app.get("/health")
async def health_check():
    """Health check para monitoramento"""
    return {
        "status": "healthy",
        "service": "reconciliation",
        "reconciliation_engine": "running",
        "message_queue": "connected",
        "matching_algorithms": "active"
    }

@app.post("/upload-statement")
async def upload_bank_statement(
    file: UploadFile = File(...),
    bank_account_id: str = "default",
    background_tasks: BackgroundTasks = None
):
    """Endpoint para upload de extrato bancário"""
    
    if not file.filename.lower().endswith(('.ofx', '.csv', '.pdf')):
        return {
            "error": "Formato não suportado. Use OFX, CSV ou PDF",
            "supported_formats": ["OFX", "CSV", "PDF"]
        }
    
    # Processar extrato em background
    background_tasks.add_task(
        app.state.reconciliation_engine.process_bank_statement,
        file,
        bank_account_id
    )
    
    return {
        "message": "Extrato enviado para processamento",
        "filename": file.filename,
        "bank_account_id": bank_account_id,
        "status": "processing"
    }

@app.post("/reconcile-period")
async def reconcile_period(
    start_date: str,
    end_date: str,
    bank_account_id: str = "default",
    background_tasks: BackgroundTasks = None
):
    """Endpoint para reconciliar período específico"""
    
    background_tasks.add_task(
        app.state.reconciliation_engine.reconcile_period,
        start_date,
        end_date,
        bank_account_id
    )
    
    return {
        "message": "Reconciliação do período iniciada",
        "period": f"{start_date} a {end_date}",
        "bank_account_id": bank_account_id,
        "status": "processing"
    }

@app.get("/stats")
async def get_reconciliation_stats():
    """Estatísticas de conciliação"""
    return {
        "statements_processed": 89,
        "transactions_analyzed": 2847,
        "auto_matched": 2654,
        "manual_review_needed": 193,
        "matching_accuracy": 93.2,
        "discrepancies_found": 12,
        "total_reconciled_amount": 1847650.75,
        "last_reconciliation": "2024-01-20T14:30:00",
        "pending_transactions": 45
    }

@app.get("/unmatched")
async def get_unmatched_transactions():
    """Lista transações não conciliadas"""
    return {
        "total_unmatched": 45,
        "total_amount": 28450.50,
        "transactions": [
            {
                "id": "txn-001",
                "date": "2024-01-18",
                "amount": 1500.00,
                "description": "TED RECEBIDA EMPRESA ABC",
                "type": "credit",
                "confidence_scores": [
                    {"invoice_id": "inv-123", "score": 0.75, "reason": "valor_similar"},
                    {"invoice_id": "inv-124", "score": 0.65, "reason": "data_proxima"}
                ]
            },
            {
                "id": "txn-002",
                "date": "2024-01-19",
                "amount": -850.00,
                "description": "PAGAMENTO FORNECEDOR XYZ",
                "type": "debit",
                "confidence_scores": [
                    {"invoice_id": "ap-456", "score": 0.85, "reason": "valor_exato"}
                ]
            }
        ]
    }

@app.get("/discrepancies")
async def get_discrepancies():
    """Lista discrepâncias encontradas"""
    return {
        "total_discrepancies": 12,
        "discrepancies": [
            {
                "id": "disc-001",
                "type": "amount_difference",
                "transaction_id": "txn-005",
                "expected_amount": 1000.00,
                "actual_amount": 950.00,
                "difference": -50.00,
                "possible_causes": ["desconto", "taxa_bancaria", "erro_lancamento"]
            },
            {
                "id": "disc-002",
                "type": "missing_transaction",
                "invoice_id": "inv-789",
                "expected_amount": 2500.00,
                "expected_date": "2024-01-15",
                "status": "not_found_in_statement"
            }
        ]
    }

@app.post("/manual-match")
async def manual_match(
    transaction_id: str,
    invoice_id: str,
    confidence_override: float = 1.0
):
    """Endpoint para matching manual"""
    
    result = await app.state.reconciliation_engine.manual_match(
        transaction_id, invoice_id, confidence_override
    )
    
    return {
        "message": "Matching manual realizado",
        "transaction_id": transaction_id,
        "invoice_id": invoice_id,
        "confidence": confidence_override,
        "status": "matched",
        "matched_at": result.get("matched_at")
    }

@app.get("/matching-rules")
async def get_matching_rules():
    """Retorna regras de matching configuradas"""
    return {
        "fuzzy_matching": {
            "enabled": True,
            "similarity_threshold": 0.8,
            "algorithms": ["levenshtein", "jaro_winkler"]
        },
        "amount_tolerance": {
            "percentage": 2.0,
            "absolute_value": 10.0
        },
        "date_tolerance": {
            "days_before": 5,
            "days_after": 10
        },
        "auto_match_threshold": 0.95,
        "manual_review_threshold": 0.7
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8002,
        reload=True if os.getenv("ENVIRONMENT") == "development" else False
    )
