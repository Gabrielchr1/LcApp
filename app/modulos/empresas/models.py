from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class Empresa(Base):
    __tablename__ = "empresas"

    id = Column(Integer, primary_key=True, index=True)
    nome_fantasia = Column(String, index=True, nullable=False)
    cnpj = Column(String, unique=True, index=True, nullable=False)
    ativo = Column(Boolean, default=True)
    data_criacao = Column(DateTime(timezone=True), server_default=func.now())

    # Relacionamento: Uma empresa pode ter várias credenciais de diferentes APIs
    credenciais = relationship("CredencialAPI", back_populates="empresa", cascade="all, delete-orphan")


class CredencialAPI(Base):
    __tablename__ = "credenciais_api"

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False)
    
    # Ex: 'growatt', 'sungrow', 'saj'
    fornecedor_api = Column(String, nullable=False) 
    
    # Nome de usuário na plataforma original (ex: OSS Growatt)
    usuario_api = Column(String, nullable=False)
    
    # O Token. Em produção, esta coluna deve receber dados criptografados!
    token_acesso = Column(String, nullable=False)

    empresa = relationship("Empresa", back_populates="credenciais")