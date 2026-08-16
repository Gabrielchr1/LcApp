import traceback
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel # NOVO
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select # NOVO

from app.core.database import get_db
# Removemos o app.core.config import settings

from .service import obter_plantas_com_cache
from .client import GrowattClient
from .models import GrowattConfig # NOVO

router = APIRouter(prefix="/api/growatt", tags=["Growatt"])

# Schema para receber os dados do Frontend
class GrowattConfigRequest(BaseModel):
    api_url: str = "https://openapi.growatt.com/v1"
    api_token: str

@router.post("/configurar")
async def save_growatt_config(data: GrowattConfigRequest, db: AsyncSession = Depends(get_db)):
    """Salva o Token da Growatt no banco de dados."""
    try:
        empresa_id_teste = 1
        
        stmt = select(GrowattConfig).where(GrowattConfig.empresa_id == empresa_id_teste)
        resultado = await db.execute(stmt)
        config = resultado.scalars().first()
        
        if config:
            config.api_url = data.api_url
            config.api_token = data.api_token
        else:
            nova_config = GrowattConfig(
                empresa_id=empresa_id_teste,
                api_url=data.api_url,
                api_token=data.api_token
            )
            db.add(nova_config)
            
        await db.commit()
        
        return {"success": True, "message": "Credenciais da Growatt salvas com sucesso!"}
        
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro Interno: {str(e)}")

@router.get("/plants")
async def list_plants(page: int = 1, db: AsyncSession = Depends(get_db)):
    try:
        empresa_id_teste = 1
        
        stmt = select(GrowattConfig).where(GrowattConfig.empresa_id == empresa_id_teste)
        resultado = await db.execute(stmt)
        config = resultado.scalars().first()

        if not config or not config.api_token:
            raise HTTPException(
                status_code=400, 
                detail="Integração com a Growatt não configurada. Por favor, acesse as configurações e insira o Token."
            )
        
        # O retorno agora já vem no formato {"plants": [...]}
        dados_normalizados = await obter_plantas_com_cache(db, empresa_id_teste, config.api_token, config.api_url, page)
        
        # Verifica se deu erro na normalização
        if not dados_normalizados.get("plants") and dados_normalizados.get("error_msg"):
            raise HTTPException(status_code=400, detail=dados_normalizados.get("error_msg"))
            
        return dados_normalizados
        
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))




@router.get("/dataloggers/{plant_id}")
async def list_dataloggers(plant_id: int, page: int = 1, perpage: int = 20, db: AsyncSession = Depends(get_db)): # Adicionado db dependency
    try:
        empresa_id_teste = 1
        
        # 1. Busca as credenciais no Banco de Dados
        stmt = select(GrowattConfig).where(GrowattConfig.empresa_id == empresa_id_teste)
        resultado = await db.execute(stmt)
        config = resultado.scalars().first()

        if not config or not config.api_token:
            raise HTTPException(status_code=400, detail="Integração com a Growatt não configurada.")
            
        # 2. Instancia o cliente com dados do banco
        client = GrowattClient(api_token=config.api_token, api_url=config.api_url)
        
        dados = await client.get_datalogger_list(plant_id, page, perpage)
        
        if dados.get("error_code") != 0:
            raise HTTPException(status_code=400, detail=dados.get("error_msg", "Erro desconhecido na API"))
            
        return dados.get("data", {})
        
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))