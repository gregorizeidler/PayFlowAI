"""
Modelos SQLAlchemy para o Core API
"""

from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text, DECIMAL, Date, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.types import TypeDecorator, String as SQLString
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database import Base

# Tipo UUID compatível com SQLite
class GUID(TypeDecorator):
    impl = SQLString
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(UUID())
        else:
            return dialect.type_descriptor(SQLString(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return str(value)
        else:
            if not isinstance(value, uuid.UUID):
                return str(value)
            else:
                return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if not isinstance(value, uuid.UUID):
                return uuid.UUID(value)
            return value

class Company(Base):
    """Modelo para empresas/clientes do sistema"""
    __tablename__ = "companies"
    # __table_args__ = {"schema": "financial_automation"}  # Removido para SQLite
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    cnpj = Column(String(18), unique=True, nullable=False)
    email = Column(String(255), nullable=False)
    phone = Column(String(20))
    address = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    
    # Relacionamentos
    users = relationship("User", back_populates="company")
    suppliers = relationship("Supplier", back_populates="company")
    customers = relationship("Customer", back_populates="company")
    documents = relationship("Document", back_populates="company")
    accounts_payable = relationship("AccountPayable", back_populates="company")
    accounts_receivable = relationship("AccountReceivable", back_populates="company")

class User(Base):
    """Modelo para usuários do sistema"""
    __tablename__ = "users"
    # __table_args__ = {"schema": "financial_automation"}  # Removido para SQLite
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    company_id = Column(GUID(), ForeignKey("companies.id", ondelete="CASCADE"))
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    role = Column(String(50), nullable=False, default="user")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relacionamentos
    company = relationship("Company", back_populates="users")

class Supplier(Base):
    """Modelo para fornecedores"""
    __tablename__ = "suppliers"
    # __table_args__ = {"schema": "financial_automation"}  # Removido para SQLite
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    company_id = Column(GUID(), ForeignKey("companies.id", ondelete="CASCADE"))
    name = Column(String(255), nullable=False)
    cnpj = Column(String(18))
    email = Column(String(255))
    phone = Column(String(20))
    address = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    
    # Relacionamentos
    company = relationship("Company", back_populates="suppliers")
    accounts_payable = relationship("AccountPayable", back_populates="supplier")

class Customer(Base):
    """Modelo para clientes"""
    __tablename__ = "customers"
    # __table_args__ = {"schema": "financial_automation"}  # Removido para SQLite
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    company_id = Column(GUID(), ForeignKey("companies.id", ondelete="CASCADE"))
    name = Column(String(255), nullable=False)
    cnpj_cpf = Column(String(18))
    email = Column(String(255))
    phone = Column(String(20))
    address = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    
    # Relacionamentos
    company = relationship("Company", back_populates="customers")
    accounts_receivable = relationship("AccountReceivable", back_populates="customer")

class Document(Base):
    """Modelo para documentos processados"""
    __tablename__ = "documents"
    # __table_args__ = {"schema": "financial_automation"}  # Removido para SQLite
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    company_id = Column(GUID(), ForeignKey("companies.id", ondelete="CASCADE"))
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer)
    mime_type = Column(String(100))
    document_type = Column(String(50), nullable=False)  # 'invoice', 'receipt', 'bank_statement'
    processing_status = Column(String(50), default="pending")  # 'pending', 'processing', 'completed', 'failed'
    ocr_confidence = Column(DECIMAL(5, 2))
    extracted_data = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True))
    
    # Relacionamentos
    company = relationship("Company", back_populates="documents")
    accounts_payable = relationship("AccountPayable", back_populates="document")

class AccountPayable(Base):
    """Modelo para contas a pagar"""
    __tablename__ = "accounts_payable"
    # __table_args__ = {"schema": "financial_automation"}  # Removido para SQLite
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    company_id = Column(GUID(), ForeignKey("companies.id", ondelete="CASCADE"))
    supplier_id = Column(GUID(), ForeignKey("suppliers.id"))
    document_id = Column(GUID(), ForeignKey("documents.id"))
    invoice_number = Column(String(100), nullable=False)
    invoice_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)
    total_amount = Column(DECIMAL(15, 2), nullable=False)
    currency = Column(String(3), default="BRL")
    status = Column(String(50), default="pending")  # 'pending', 'approved', 'paid', 'cancelled'
    payment_method = Column(String(50))
    barcode = Column(String(200))
    digitable_line = Column(String(200))
    matching_status = Column(String(50), default="pending")  # 'pending', 'matched', 'exception'
    approval_workflow = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    paid_at = Column(DateTime(timezone=True))
    
    # Relacionamentos
    company = relationship("Company", back_populates="accounts_payable")
    supplier = relationship("Supplier", back_populates="accounts_payable")
    document = relationship("Document", back_populates="accounts_payable")

class AccountReceivable(Base):
    """Modelo para contas a receber"""
    __tablename__ = "accounts_receivable"
    # __table_args__ = {"schema": "financial_automation"}  # Removido para SQLite
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    company_id = Column(GUID(), ForeignKey("companies.id", ondelete="CASCADE"))
    customer_id = Column(GUID(), ForeignKey("customers.id"))
    invoice_number = Column(String(100), nullable=False)
    invoice_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)
    total_amount = Column(DECIMAL(15, 2), nullable=False)
    currency = Column(String(3), default="BRL")
    status = Column(String(50), default="pending")  # 'pending', 'sent', 'overdue', 'paid', 'cancelled'
    payment_method = Column(String(50))
    barcode = Column(String(200))
    digitable_line = Column(String(200))
    dunning_level = Column(Integer, default=0)
    last_dunning_date = Column(Date)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    paid_at = Column(DateTime(timezone=True))
    
    # Relacionamentos
    company = relationship("Company", back_populates="accounts_receivable")
    customer = relationship("Customer", back_populates="accounts_receivable")

class BankTransaction(Base):
    """Modelo para transações bancárias"""
    __tablename__ = "bank_transactions"
    # __table_args__ = {"schema": "financial_automation"}  # Removido para SQLite
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    company_id = Column(GUID(), ForeignKey("companies.id", ondelete="CASCADE"))
    transaction_date = Column(Date, nullable=False)
    amount = Column(DECIMAL(15, 2), nullable=False)
    transaction_type = Column(String(20), nullable=False)  # 'credit', 'debit'
    description = Column(Text)
    bank_reference = Column(String(100))
    reconciliation_status = Column(String(50), default="pending")  # 'pending', 'matched', 'manual'
    matched_ar_id = Column(GUID(), ForeignKey("accounts_receivable.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ProcessingLog(Base):
    """Modelo para logs de processamento"""
    __tablename__ = "processing_logs"
    # __table_args__ = {"schema": "financial_automation"}  # Removido para SQLite
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    document_id = Column(GUID(), ForeignKey("documents.id"))
    service_name = Column(String(100), nullable=False)
    event_type = Column(String(50), nullable=False)
    event_data = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
