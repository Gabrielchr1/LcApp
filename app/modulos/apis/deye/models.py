# app/core/modules/apis/deye/models.py
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from app.core.database import Base

class DeyeConfig(Base):
    __tablename__ = "deye_configs"

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    # URL base da API da Deye (US por padrão, conforme sua solicitação)
    api_url = Column(String, default="https://us1-developer.deyecloud.com", nullable=False)
    
    # Credenciais do App
    app_id = Column(String, nullable=False)
    app_secret = Column(String, nullable=False)
    
    # Credenciais do Usuário Deye
    email = Column(String, nullable=False) # Usaremos email como padrão de login
    password_hash = Column(String, nullable=False) # Já vamos salvar no banco o SHA-256 em minúsculo
    
    # Para contas Business (se for Personal, ficará nulo)
    company_id = Column(Integer, nullable=True) 
    
    # Armazenamento do token (na Deye dura 60 dias)
    access_token = Column(String, nullable=True)
    token_expires_at = Column(DateTime(timezone=True), nullable=True)