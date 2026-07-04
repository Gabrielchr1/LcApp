from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from app.core.database import Base

class CacheAPI(Base):
    __tablename__ = "cache_api"

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False)
    
    # Identificador único da requisição. Ex: 'growatt_plant_list' ou 'growatt_datalogger_24765'
    chave_cache = Column(String, unique=True, index=True, nullable=False)
    
    # O payload JSON devolvido pela API da Growatt
    dados = Column(JSON, nullable=False)
    
    # Controle de tempo para expiração
    atualizado_em = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
