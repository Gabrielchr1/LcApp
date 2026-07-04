# app/modulos/apis/solis/models.py

from sqlalchemy import Column, Integer, String, ForeignKey
from app.core.database import Base

class SolisConfig(Base):
    __tablename__ = "solis_configs"

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    # Credenciais exigidas pela SolisCloud
    api_url = Column(String, default="https://www.soliscloud.com:13333", nullable=False)
    key_id = Column(String, nullable=False)
    key_secret = Column(String, nullable=False)