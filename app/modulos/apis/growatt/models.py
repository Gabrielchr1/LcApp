from sqlalchemy import Column, Integer, String, ForeignKey
from app.core.database import Base

class GrowattConfig(Base):
    __tablename__ = "growatt_configs"

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    # URL base da API (caso a Growatt mude no futuro, você pode alterar pelo frontend)
    api_url = Column(String, default="https://openapi.growatt.com/v1", nullable=False)
    
    # O Token gerado pela plataforma
    api_token = Column(String, nullable=False)