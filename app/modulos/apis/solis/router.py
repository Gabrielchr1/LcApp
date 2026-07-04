# app/modulos/apis/solis/router.py

import traceback
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db

from app.modulos.apis.solis.models import SolisConfig
from .service import (
    obter_plantas_solis_com_cache,
    obter_dispositivos_solis_com_cache
)

router = APIRouter(prefix="/api/solis", tags=["Solis"])

# Schema para receber as chaves do frontend
class SolisConfigRequest(BaseModel):
    api_url: str = "https://www.soliscloud.com:13333"
    key_id: str
    key_secret: str

@router.get("/plants")
async def list_plants(page: int = 1, db: AsyncSession = Depends(get_db)):
    """Retorna a lista de usinas cadastradas na SolisCloud consumindo as chaves do banco."""
    try:
        empresa_id_teste = 1
        
        stmt = select(SolisConfig).where(SolisConfig.empresa_id == empresa_id_teste)
        resultado = await db.execute(stmt)
        config = resultado.scalars().first()
        
        if not config or not config.key_id or not config.key_secret:
            raise HTTPException(
                status_code=400, 
                detail="Integração com a Solis não configurada. Por favor, acesse as configurações e insira a Key ID e Key Secret."
            )
            
        dados_normalizados = await obter_plantas_solis_com_cache(
            db, 
            empresa_id=empresa_id_teste, 
            api_url=config.api_url, 
            key_id=config.key_id, 
            key_secret=config.key_secret, 
            page=page
        )
        
        if not dados_normalizados.get("plants") and dados_normalizados.get("error_msg"):
             raise HTTPException(status_code=400, detail=dados_normalizados.get("error_msg"))
            
        return dados_normalizados
        
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro Interno Solis: {str(e)}")


@router.get("/dataloggers/{ps_id}")
async def list_dataloggers(ps_id: str, page: int = 1, db: AsyncSession = Depends(get_db)):
    """Retorna a lista de inversores (devices) da usina específica."""
    try:
        empresa_id_teste = 1
        
        stmt = select(SolisConfig).where(SolisConfig.empresa_id == empresa_id_teste)
        resultado = await db.execute(stmt)
        config = resultado.scalars().first()
        
        if not config or not config.key_id:
            raise HTTPException(status_code=400, detail="Integração com a Solis não configurada.")
        
        dados_normalizados = await obter_dispositivos_solis_com_cache(
            db, 
            empresa_id=empresa_id_teste, 
            api_url=config.api_url, 
            key_id=config.key_id, 
            key_secret=config.key_secret, 
            ps_id=ps_id, 
            page=page
        )
        
        if not dados_normalizados.get("dataloggers") and dados_normalizados.get("error_msg"):
             raise HTTPException(status_code=400, detail=dados_normalizados.get("error_msg"))
            
        return dados_normalizados
        
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro Interno Solis: {str(e)}")


@router.post("/configurar")
async def save_solis_config(data: SolisConfigRequest, db: AsyncSession = Depends(get_db)):
    """Salva a KeyID e KeySecret da Solis no banco de dados."""
    try:
        empresa_id_teste = 1
        
        stmt = select(SolisConfig).where(SolisConfig.empresa_id == empresa_id_teste)
        resultado = await db.execute(stmt)
        config = resultado.scalars().first()
        
        if config:
            config.api_url = data.api_url
            config.key_id = data.key_id
            config.key_secret = data.key_secret
        else:
            nova_config = SolisConfig(
                empresa_id=empresa_id_teste,
                api_url=data.api_url,
                key_id=data.key_id,
                key_secret=data.key_secret
            )
            db.add(nova_config)
            
        await db.commit()
        
        return {"success": True, "message": "Credenciais da Solis salvas com sucesso!"}
        
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro Interno: {str(e)}")