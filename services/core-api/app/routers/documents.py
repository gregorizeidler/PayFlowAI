"""
Router de Documentos
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Request
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
import uuid
from datetime import datetime
import os
import tempfile
import logging

from app.database import get_db
from app.models import Document, User
from app.routers.auth import verify_token
from app.services.storage_service import StorageService

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/upload")
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    document_type: str = "invoice",
    user_id: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Upload REAL de documento para processamento"""
    
    try:
        logger.info(f"📤 Iniciando upload de documento: {file.filename}")
        
        # Validar arquivo
        if not file.filename:
            raise HTTPException(status_code=400, detail="Nome do arquivo é obrigatório")
        
        # Validar tipo de arquivo
        allowed_types = ["application/pdf", "image/png", "image/jpeg", "image/jpg"]
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400, 
                detail=f"Tipo de arquivo não suportado: {file.content_type}"
            )
        
        # Validar tamanho (máximo 10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        file_content = await file.read()
        if len(file_content) > max_size:
            raise HTTPException(status_code=400, detail="Arquivo muito grande (máximo 10MB)")
        
        # Obter dados do usuário
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")
        
        # Gerar ID único para o documento
        document_id = str(uuid.uuid4())
        
        # Definir caminho no storage
        file_extension = os.path.splitext(file.filename)[1]
        storage_path = f"documents/{user.company_id}/{document_id}{file_extension}"
        
        # Salvar arquivo temporário
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            temp_file.write(file_content)
            temp_file_path = temp_file.name
        
        try:
            # Upload para MinIO
            storage_service = StorageService()
            upload_success = await storage_service.upload_file(temp_file_path, storage_path)
            
            if not upload_success:
                raise HTTPException(status_code=500, detail="Falha no upload do arquivo")
            
            # Criar registro no banco
            document = Document(
                id=document_id,
                company_id=user.company_id,
                original_filename=file.filename,
                file_path=storage_path,
                file_size=len(file_content),
                mime_type=file.content_type,
                document_type=document_type,
                processing_status="pending"
            )
            
            db.add(document)
            db.commit()
            db.refresh(document)
            
            # Publicar evento na fila para processamento
            message_queue = request.app.state.message_queue
            message_queue.publish_document_received(
                document_id=document_id,
                company_id=str(user.company_id),
                file_path=storage_path
            )
            
            logger.info(f"✅ Upload concluído: {document_id}")
            
            return {
                "document_id": str(document.id),
                "filename": document.original_filename,
                "file_size": document.file_size,
                "status": document.processing_status,
                "message": "Documento enviado para processamento com sucesso"
            }
            
        finally:
            # Limpar arquivo temporário
            try:
                os.unlink(temp_file_path)
            except:
                pass
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro no upload: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno no upload")

@router.get("/")
async def list_documents(
    user_id: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Listar documentos"""
    documents = db.query(Document).order_by(Document.created_at.desc()).all()
    return [
        {
            "id": str(doc.id),
            "original_filename": doc.original_filename,
            "document_type": doc.document_type,
            "processing_status": doc.processing_status,
            "ocr_confidence": float(doc.ocr_confidence) if doc.ocr_confidence else None,
            "created_at": doc.created_at,
            "processed_at": doc.processed_at
        }
        for doc in documents
    ]

@router.get("/{document_id}")
async def get_document(
    document_id: UUID,
    user_id: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Obter documento por ID"""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Documento não encontrado"
        )
    
    return {
        "id": str(document.id),
        "original_filename": document.original_filename,
        "file_path": document.file_path,
        "file_size": document.file_size,
        "mime_type": document.mime_type,
        "document_type": document.document_type,
        "processing_status": document.processing_status,
        "ocr_confidence": float(document.ocr_confidence) if document.ocr_confidence else None,
        "extracted_data": document.extracted_data,
        "created_at": document.created_at,
        "processed_at": document.processed_at
    }

@router.post("/{document_id}/processed")
async def document_processed_callback(
    document_id: UUID,
    result: dict,
    db: Session = Depends(get_db)
):
    """Callback do serviço OCR/NLP quando documento é processado"""
    
    try:
        logger.info(f"📨 Recebendo resultado do processamento: {document_id}")
        
        # Buscar documento
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Documento não encontrado")
        
        # Atualizar documento com resultado
        document.processing_status = result.get("processing_status", "completed")
        document.ocr_confidence = result.get("ocr_confidence")
        document.extracted_data = result.get("extracted_data", {})
        document.processed_at = datetime.utcnow()
        
        db.commit()
        
        # Se processamento foi bem-sucedido, criar conta a pagar/receber
        if document.processing_status == "completed" and document.extracted_data:
            await _create_financial_record(document, db)
        
        logger.info(f"✅ Documento {document_id} atualizado com resultado do processamento")
        
        return {
            "message": "Resultado do processamento recebido com sucesso",
            "document_id": str(document_id),
            "status": document.processing_status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao processar callback: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno")

async def _create_financial_record(document: Document, db: Session):
    """Cria registro financeiro baseado no documento processado"""
    try:
        extracted_data = document.extracted_data
        
        if document.document_type == "invoice" and extracted_data.get("type") == "invoice":
            # Criar conta a pagar
            from app.models import AccountPayable, Supplier
            
            # Buscar ou criar fornecedor
            supplier = None
            if extracted_data.get("extracted_fields", {}).get("cnpj"):
                cnpj = extracted_data["extracted_fields"]["cnpj"]
                supplier = db.query(Supplier).filter(
                    Supplier.cnpj == cnpj,
                    Supplier.company_id == document.company_id
                ).first()
            
            # Criar conta a pagar
            ap = AccountPayable(
                company_id=document.company_id,
                supplier_id=supplier.id if supplier else None,
                document_id=document.id,
                invoice_number=extracted_data.get("extracted_fields", {}).get("invoice_number", "N/A"),
                invoice_date=extracted_data.get("extracted_fields", {}).get("issue_date", datetime.utcnow().date()),
                due_date=extracted_data.get("extracted_fields", {}).get("due_date", datetime.utcnow().date()),
                total_amount=extracted_data.get("extracted_fields", {}).get("total_amount", 0.0),
                digitable_line=extracted_data.get("extracted_fields", {}).get("digitable_line"),
                barcode=extracted_data.get("extracted_fields", {}).get("barcode"),
                status="pending",
                matching_status="pending"
            )
            
            db.add(ap)
            db.commit()
            
            logger.info(f"✅ Conta a pagar criada para documento {document.id}")
            
    except Exception as e:
        logger.error(f"❌ Erro ao criar registro financeiro: {str(e)}")
