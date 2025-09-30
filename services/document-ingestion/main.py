"""
Document Ingestion Service - Sistema de Automação Financeira
Serviço básico para ingestão de documentos
"""

from fastapi import FastAPI
import uvicorn
import os

# Criar aplicação FastAPI
app = FastAPI(
    title="Sistema de Automação Financeira - Document Ingestion Service",
    description="Serviço de ingestão de documentos",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

@app.get("/")
async def root():
    """Endpoint raiz com informações do serviço"""
    return {
        "service": "Document Ingestion Service",
        "version": "1.0.0",
        "status": "running",
        "description": "Serviço de ingestão de documentos"
    }

@app.get("/health")
async def health_check():
    """Health check para monitoramento"""
    return {
        "status": "healthy",
        "service": "document-ingestion"
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True if os.getenv("ENVIRONMENT") == "development" else False
    )
