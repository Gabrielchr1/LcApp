# app/apis/saj/models.py
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from app.core.database import Base

class SajConfig(Base):
    __tablename__ = "saj_configs"

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    # URL base da API da SAJ
    api_url = Column(String, default="https://intl-developer.saj-electric.com/prod-api", nullable=False)
    
    # Credenciais fornecidas pela SAJ
    app_id = Column(String, nullable=False)
    app_secret = Column(String, nullable=False)
    
    # Armazenamento do token para evitar sobrecarregar o endpoint de autenticação
    access_token = Column(String, nullable=True)
    token_expires_at = Column(DateTime(timezone=True), nullable=True)