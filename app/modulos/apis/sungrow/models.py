# app/modulos/apis/sungrow/models.py

from sqlalchemy import Column, Integer, String, ForeignKey
from app.core.database import Base

class SungrowConfig(Base):
    __tablename__ = "sungrow_configs"

    id = Column(Integer, primary_key=True, index=True)
    # Relacionamento com a tabela de empresas
    empresa_id = Column(Integer, ForeignKey("empresas.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    # Credenciais
    app_key = Column(String, nullable=False)
    secret_key = Column(String, nullable=False)
    user_account = Column(String, nullable=False)
    user_password = Column(String, nullable=False)
    token = Column(String, nullable=True)