"""
Router de Fornecedores
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.database import get_db
from app.models import Supplier
from app.routers.auth import verify_token

router = APIRouter()

@router.get("/")
async def list_suppliers(
    user_id: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Listar fornecedores"""
    suppliers = db.query(Supplier).filter(Supplier.is_active == True).all()
    return [
        {
            "id": str(supplier.id),
            "name": supplier.name,
            "cnpj": supplier.cnpj,
            "email": supplier.email,
            "phone": supplier.phone,
            "address": supplier.address,
            "company_id": str(supplier.company_id),
            "is_active": supplier.is_active,
            "created_at": supplier.created_at
        }
        for supplier in suppliers
    ]

@router.get("/{supplier_id}")
async def get_supplier(
    supplier_id: UUID,
    user_id: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Obter fornecedor por ID"""
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fornecedor não encontrado"
        )
    
    return {
        "id": str(supplier.id),
        "name": supplier.name,
        "cnpj": supplier.cnpj,
        "email": supplier.email,
        "phone": supplier.phone,
        "address": supplier.address,
        "company_id": str(supplier.company_id),
        "is_active": supplier.is_active,
        "created_at": supplier.created_at,
        "updated_at": supplier.updated_at
    }
