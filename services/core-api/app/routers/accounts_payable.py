"""
Router de Contas a Pagar
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import date

from app.database import get_db
from app.models import AccountPayable
from app.routers.auth import verify_token

router = APIRouter()

@router.get("/")
async def list_accounts_payable(
    status_filter: Optional[str] = None,
    user_id: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Listar contas a pagar"""
    query = db.query(AccountPayable)
    
    if status_filter:
        query = query.filter(AccountPayable.status == status_filter)
    
    accounts = query.order_by(AccountPayable.due_date.asc()).all()
    
    return [
        {
            "id": str(account.id),
            "invoice_number": account.invoice_number,
            "supplier_id": str(account.supplier_id) if account.supplier_id else None,
            "invoice_date": account.invoice_date.isoformat(),
            "due_date": account.due_date.isoformat(),
            "total_amount": float(account.total_amount),
            "currency": account.currency,
            "status": account.status,
            "matching_status": account.matching_status,
            "created_at": account.created_at,
            "updated_at": account.updated_at
        }
        for account in accounts
    ]

@router.get("/{ap_id}")
async def get_account_payable(
    ap_id: UUID,
    user_id: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Obter conta a pagar por ID"""
    account = db.query(AccountPayable).filter(AccountPayable.id == ap_id).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conta a pagar não encontrada"
        )
    
    return {
        "id": str(account.id),
        "company_id": str(account.company_id),
        "supplier_id": str(account.supplier_id) if account.supplier_id else None,
        "document_id": str(account.document_id) if account.document_id else None,
        "invoice_number": account.invoice_number,
        "invoice_date": account.invoice_date.isoformat(),
        "due_date": account.due_date.isoformat(),
        "total_amount": float(account.total_amount),
        "currency": account.currency,
        "status": account.status,
        "payment_method": account.payment_method,
        "barcode": account.barcode,
        "digitable_line": account.digitable_line,
        "matching_status": account.matching_status,
        "approval_workflow": account.approval_workflow,
        "created_at": account.created_at,
        "updated_at": account.updated_at,
        "paid_at": account.paid_at
    }

@router.post("/{ap_id}/approve")
async def approve_account_payable(
    ap_id: UUID,
    user_id: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Aprovar conta a pagar"""
    account = db.query(AccountPayable).filter(AccountPayable.id == ap_id).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conta a pagar não encontrada"
        )
    
    if account.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Conta não está pendente de aprovação"
        )
    
    # Atualizar status
    account.status = "approved"
    db.commit()
    
    # TODO: Publicar evento de aprovação na fila
    
    return {
        "message": "Conta a pagar aprovada com sucesso",
        "ap_id": str(account.id),
        "new_status": account.status
    }

@router.get("/dashboard/stats")
async def get_ap_dashboard_stats(
    user_id: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Estatísticas do dashboard de AP"""
    
    # TODO: Implementar queries reais
    total_pending = db.query(AccountPayable).filter(AccountPayable.status == "pending").count()
    total_approved = db.query(AccountPayable).filter(AccountPayable.status == "approved").count()
    total_paid = db.query(AccountPayable).filter(AccountPayable.status == "paid").count()
    
    # Contas vencidas (due_date < hoje)
    overdue = db.query(AccountPayable).filter(
        AccountPayable.due_date < date.today(),
        AccountPayable.status.in_(["pending", "approved"])
    ).count()
    
    return {
        "total_pending": total_pending,
        "total_approved": total_approved,
        "total_paid": total_paid,
        "overdue": overdue,
        "pending_approval": total_pending,
        "total_amount_pending": 125000.50  # TODO: Calcular valor real
    }
