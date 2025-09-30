"""
Router de Contas a Receber
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import date

from app.database import get_db
from app.models import AccountReceivable
from app.routers.auth import verify_token

router = APIRouter()

@router.get("/")
async def list_accounts_receivable(
    status_filter: Optional[str] = None,
    user_id: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Listar contas a receber"""
    query = db.query(AccountReceivable)
    
    if status_filter:
        query = query.filter(AccountReceivable.status == status_filter)
    
    accounts = query.order_by(AccountReceivable.due_date.asc()).all()
    
    return [
        {
            "id": str(account.id),
            "invoice_number": account.invoice_number,
            "customer_id": str(account.customer_id) if account.customer_id else None,
            "invoice_date": account.invoice_date.isoformat(),
            "due_date": account.due_date.isoformat(),
            "total_amount": float(account.total_amount),
            "currency": account.currency,
            "status": account.status,
            "dunning_level": account.dunning_level,
            "last_dunning_date": account.last_dunning_date.isoformat() if account.last_dunning_date else None,
            "created_at": account.created_at,
            "updated_at": account.updated_at
        }
        for account in accounts
    ]

@router.get("/{ar_id}")
async def get_account_receivable(
    ar_id: UUID,
    user_id: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Obter conta a receber por ID"""
    account = db.query(AccountReceivable).filter(AccountReceivable.id == ar_id).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conta a receber não encontrada"
        )
    
    return {
        "id": str(account.id),
        "company_id": str(account.company_id),
        "customer_id": str(account.customer_id) if account.customer_id else None,
        "invoice_number": account.invoice_number,
        "invoice_date": account.invoice_date.isoformat(),
        "due_date": account.due_date.isoformat(),
        "total_amount": float(account.total_amount),
        "currency": account.currency,
        "status": account.status,
        "payment_method": account.payment_method,
        "barcode": account.barcode,
        "digitable_line": account.digitable_line,
        "dunning_level": account.dunning_level,
        "last_dunning_date": account.last_dunning_date.isoformat() if account.last_dunning_date else None,
        "created_at": account.created_at,
        "updated_at": account.updated_at,
        "paid_at": account.paid_at
    }

@router.post("/{ar_id}/mark-paid")
async def mark_account_receivable_paid(
    ar_id: UUID,
    user_id: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Marcar conta a receber como paga"""
    account = db.query(AccountReceivable).filter(AccountReceivable.id == ar_id).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conta a receber não encontrada"
        )
    
    if account.status == "paid":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Conta já está marcada como paga"
        )
    
    # Atualizar status
    account.status = "paid"
    account.paid_at = date.today()
    db.commit()
    
    return {
        "message": "Conta a receber marcada como paga",
        "ar_id": str(account.id),
        "new_status": account.status
    }

@router.get("/dashboard/stats")
async def get_ar_dashboard_stats(
    user_id: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Estatísticas do dashboard de AR"""
    
    # TODO: Implementar queries reais
    total_pending = db.query(AccountReceivable).filter(AccountReceivable.status == "pending").count()
    total_sent = db.query(AccountReceivable).filter(AccountReceivable.status == "sent").count()
    total_paid = db.query(AccountReceivable).filter(AccountReceivable.status == "paid").count()
    
    # Contas vencidas (due_date < hoje)
    overdue = db.query(AccountReceivable).filter(
        AccountReceivable.due_date < date.today(),
        AccountReceivable.status.in_(["pending", "sent"])
    ).count()
    
    return {
        "total_pending": total_pending,
        "total_sent": total_sent,
        "total_paid": total_paid,
        "overdue": overdue,
        "total_amount_pending": 89500.75,  # TODO: Calcular valor real
        "paid_this_month": 45  # TODO: Calcular valor real
    }
