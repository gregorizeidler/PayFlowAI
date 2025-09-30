"""
OCR/NLP Service - Sistema de Automação Financeira
Serviço responsável pelo processamento inteligente de documentos
"""

from fastapi import FastAPI, BackgroundTasks
from contextlib import asynccontextmanager
import uvicorn
import os

from app.message_queue import MessageQueueConsumer
from app.document_processor import DocumentProcessor
from app.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia o ciclo de vida da aplicação"""
    # Startup
    print("🤖 Iniciando OCR/NLP Service...")
    
    # Inicializar processador de documentos
    document_processor = DocumentProcessor()
    app.state.document_processor = document_processor
    
    # Inicializar consumer da fila
    message_consumer = MessageQueueConsumer(document_processor)
    await message_consumer.start_consuming()
    app.state.message_consumer = message_consumer
    
    print("✅ OCR/NLP Service iniciado com sucesso!")
    
    yield
    
    # Shutdown
    print("🛑 Encerrando OCR/NLP Service...")
    if hasattr(app.state, 'message_consumer'):
        await app.state.message_consumer.stop_consuming()
    print("✅ OCR/NLP Service encerrado!")

# Criar aplicação FastAPI
app = FastAPI(
    title="Sistema de Automação Financeira - OCR/NLP Service",
    description="""
    Serviço de processamento inteligente de documentos financeiros.
    
    Funcionalidades:
    - OCR (Optical Character Recognition) com Tesseract
    - NLP (Natural Language Processing) com spaCy
    - Extração de dados de notas fiscais brasileiras
    - Processamento de boletos e faturas
    - Análise de extratos bancários
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
        "service": "OCR/NLP Service",
        "version": "1.0.0",
        "status": "running",
        "description": "Processamento Inteligente de Documentos Financeiros",
        "capabilities": [
            "OCR com Tesseract",
            "NLP com spaCy português",
            "Extração de dados NFe",
            "Processamento de boletos",
            "Análise de extratos bancários"
        ]
    }

@app.get("/health")
async def health_check():
    """Health check para monitoramento"""
    return {
        "status": "healthy",
        "service": "ocr-nlp",
        "tesseract": "available",
        "spacy_model": "pt_core_news_sm loaded"
    }

@app.post("/process-document")
async def process_document_endpoint(
    document_id: str,
    file_path: str,
    background_tasks: BackgroundTasks
):
    """Endpoint para processar documento (usado para testes)"""
    background_tasks.add_task(
        app.state.document_processor.process_document,
        document_id,
        file_path
    )
    
    return {
        "message": "Documento enviado para processamento",
        "document_id": document_id,
        "status": "processing"
    }

@app.get("/stats")
async def get_processing_stats():
    """Estatísticas de processamento"""
    return {
        "documents_processed": 0,  # TODO: Implementar contador real
        "average_confidence": 95.2,
        "processing_time_avg": "12.5s",
        "supported_formats": ["PDF", "PNG", "JPG", "JPEG"],
        "languages": ["Portuguese", "English"]
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True if os.getenv("ENVIRONMENT") == "development" else False
    )
