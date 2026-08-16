# app/apis/saj/router.py
import traceback
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from .service import obter_plantas_saj_com_cache, get_valid_saj_client
from .models import SajConfig

router = APIRouter(prefix="/api/saj", tags=["SAJ"])

# Schema para receber os dados do Frontend
class SajConfigRequest(BaseModel):
    api_url: str = "https://intl-developer.saj-electric.com/prod-api"
    app_id: str
    app_secret: str

@router.post("/configurar")
async def save_saj_config(data: SajConfigRequest, db: AsyncSession = Depends(get_db)):
    """Salva as credenciais da SAJ no banco de dados."""
    try:
        empresa_id_teste = 1
        
        stmt = select(SajConfig).where(SajConfig.empresa_id == empresa_id_teste)
        resultado = await db.execute(stmt)
        config = resultado.scalars().first()
        
        if config:
            config.api_url = data.api_url
            config.app_id = data.app_id
            
            # Só atualiza o secret se ele não vier vazio e não for uma máscara de segurança do front
            if data.app_secret and not data.app_secret.startswith("***"):
                config.app_secret = data.app_secret
                # Força renovação do token APENAS se as credenciais realmente mudaram
                config.access_token = None 
                config.token_expires_at = None
                
        else:
            nova_config = SajConfig(
                empresa_id=empresa_id_teste,
                api_url=data.api_url,
                app_id=data.app_id,
                app_secret=data.app_secret
            )
            db.add(nova_config)
            
        await db.commit()
        
        return {"success": True, "message": "Credenciais da SAJ salvas com sucesso!"}
        
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro Interno: {str(e)}")

@router.get("/plants")
async def list_plants(page: int = 1, db: AsyncSession = Depends(get_db)):
    try:
        empresa_id_teste = 1
        
        stmt = select(SajConfig).where(SajConfig.empresa_id == empresa_id_teste)
        resultado = await db.execute(stmt)
        config = resultado.scalars().first()

        if not config or not config.app_id or not config.app_secret:
            raise HTTPException(
                status_code=400, 
                detail="Integração com a SAJ não configurada. Por favor, acesse as configurações e insira o App ID e App Secret."
            )
        
        # Chama a função do service que já gerencia o Cache e o Token
        dados_normalizados = await obter_plantas_saj_com_cache(db, empresa_id_teste, config, page)
        
        if not dados_normalizados.get("plants") and dados_normalizados.get("error_msg"):
            raise HTTPException(status_code=400, detail=dados_normalizados.get("error_msg"))
            
        return dados_normalizados
        
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/devices")
async def list_devices(page: int = 1, page_size: int = 100, db: AsyncSession = Depends(get_db)):
    """Rota para listar todos os dispositivos da desenvolvedora, já que a SAJ gerencia isso globalmente."""
    try:
        empresa_id_teste = 1
        
        stmt = select(SajConfig).where(SajConfig.empresa_id == empresa_id_teste)
        resultado = await db.execute(stmt)
        config = resultado.scalars().first()

        if not config:
            raise HTTPException(status_code=400, detail="Integração com a SAJ não configurada.")
            
        # Garante que temos um cliente com token válido
        client = await get_valid_saj_client(db, config)
        
        dados = await client.get_device_page(page_num=page, page_size=page_size)
        
        if dados.get("code") != 200:
            raise HTTPException(status_code=400, detail=dados.get("msg", "Erro desconhecido na API da SAJ"))
            
        # Opcional: Aqui você pode formatar/mapear os devices se quiser um padrão universal
        return {"devices": dados.get("rows", []), "total": dados.get("total", 0)}
        
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))