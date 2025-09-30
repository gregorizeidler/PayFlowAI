"""
Router de Empresas
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.database import get_db
from app.models import Company
from app.routers.auth import verify_token

router = APIRouter()

@router.get("/")
async def list_companies(
    user_id: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Listar empresas"""
    companies = db.query(Company).filter(Company.is_active == True).all()
    return [
        {
            "id": str(company.id),
            "name": company.name,
            "cnpj": company.cnpj,
            "email": company.email,
            "phone": company.phone,
            "address": company.address,
            "is_active": company.is_active,
            "created_at": company.created_at
        }
        for company in companies
    ]

@router.get("/{company_id}")
async def get_company(
    company_id: UUID,
    user_id: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Obter empresa por ID"""
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empresa não encontrada"
        )
    
    return {
        "id": str(company.id),
        "name": company.name,
        "cnpj": company.cnpj,
        "email": company.email,
        "phone": company.phone,
        "address": company.address,
        "is_active": company.is_active,
        "created_at": company.created_at,
        "updated_at": company.updated_at
    }
