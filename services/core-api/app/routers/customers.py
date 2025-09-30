"""
Router de Clientes
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.database import get_db
from app.models import Customer
from app.routers.auth import verify_token

router = APIRouter()

@router.get("/")
async def list_customers(
    user_id: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Listar clientes"""
    customers = db.query(Customer).filter(Customer.is_active == True).all()
    return [
        {
            "id": str(customer.id),
            "name": customer.name,
            "cnpj_cpf": customer.cnpj_cpf,
            "email": customer.email,
            "phone": customer.phone,
            "address": customer.address,
            "company_id": str(customer.company_id),
            "is_active": customer.is_active,
            "created_at": customer.created_at
        }
        for customer in customers
    ]

@router.get("/{customer_id}")
async def get_customer(
    customer_id: UUID,
    user_id: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Obter cliente por ID"""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente não encontrado"
        )
    
    return {
        "id": str(customer.id),
        "name": customer.name,
        "cnpj_cpf": customer.cnpj_cpf,
        "email": customer.email,
        "phone": customer.phone,
        "address": customer.address,
        "company_id": str(customer.company_id),
        "is_active": customer.is_active,
        "created_at": customer.created_at,
        "updated_at": customer.updated_at
    }
