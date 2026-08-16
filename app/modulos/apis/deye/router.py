# app/core/modules/apis/deye/router.py
import traceback
import hashlib
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from .models import DeyeConfig
from .service import obter_detalhes_usina_deye, obter_plantas_deye_com_cache

router = APIRouter(prefix="/api/deye", tags=["DEYE"])

class DeyeConfigRequest(BaseModel):
    api_url: str = "https://us1-developer.deyecloud.com"
    app_id: str
    app_secret: str
    email: str
    password: str  # Senha em texto plano vinda do frontend
    company_id: Optional[int] = None

@router.post("/configurar")
async def save_deye_config(data: DeyeConfigRequest, db: AsyncSession = Depends(get_db)):
    try:
        empresa_id_teste = 1
        
        stmt = select(DeyeConfig).where(DeyeConfig.empresa_id == empresa_id_teste)
        resultado = await db.execute(stmt)
        config = resultado.scalars().first()
        
        if config:
            config.api_url = data.api_url
            config.app_id = data.app_id
            config.app_secret = data.app_secret
            config.email = data.email
            config.company_id = data.company_id
            
            # 4. Só substitui a senha se ela não for nula ou em branco
            if data.password:
                senha_hash = hashlib.sha256(data.password.encode('utf-8')).hexdigest().lower()
                config.password_hash = senha_hash
                
            config.access_token = None 
            config.token_expires_at = None
        else:
            # Para novos registros, exige a conversão
            senha_hash = hashlib.sha256(data.password.encode('utf-8')).hexdigest().lower()
            nova_config = DeyeConfig(
                empresa_id=empresa_id_teste,
                api_url=data.api_url,
                app_id=data.app_id,
                app_secret=data.app_secret,
                email=data.email,
                password_hash=senha_hash,
                company_id=data.company_id
            )
            db.add(nova_config)
            
        await db.commit()
        return {"success": True, "message": "Credenciais da Deye salvas com sucesso!"}

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro Interno: {str(e)}")

@router.get("/plants")
async def list_plants(page: int = 1, db: AsyncSession = Depends(get_db)):
    try:
        empresa_id_teste = 1
        stmt = select(DeyeConfig).where(DeyeConfig.empresa_id == empresa_id_teste)
        resultado = await db.execute(stmt)
        config = resultado.scalars().first()

        if not config or not config.app_id:
            raise HTTPException(status_code=400, detail="Integração com a Deye não configurada.")
        
        # Chama a função do service para gerenciar cache e token
        dados_normalizados = await obter_plantas_deye_com_cache(db, empresa_id_teste, config, page)
        
        return dados_normalizados
        
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dataloggers/{plant_id}")
async def get_plant_details(plant_id: str, db: AsyncSession = Depends(get_db)):
    """Rota unificada que o detalhes.js da Deye vai chamar"""
    try:
        empresa_id_teste = 1
        stmt = select(DeyeConfig).where(DeyeConfig.empresa_id == empresa_id_teste)
        resultado = await db.execute(stmt)
        config = resultado.scalars().first()

        if not config or not config.app_id:
            raise HTTPException(status_code=400, detail="Integração com a Deye não configurada.")
        
        # Chama a função de serviço
        dados = await obter_detalhes_usina_deye(db, empresa_id_teste, config, plant_id)
        
        if "error_msg" in dados:
            raise HTTPException(status_code=400, detail=dados["error_msg"])
            
        return dados
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))