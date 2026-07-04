import traceback

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.config import settings
from .service import obter_plantas_com_cache
from .client import GrowattClient

router = APIRouter(prefix="/api/growatt", tags=["Growatt"])

# A rota agora é limpa: /api/growatt/plants
@router.get("/plants")
async def list_plants(page: int = 1, db: AsyncSession = Depends(get_db)):
    try:
        empresa_id_teste = 1
        api_token_teste = settings.GROWATT_TOKEN
        
        # Chamamos o serviço sem o user_name
        dados = await obter_plantas_com_cache(db, empresa_id_teste, api_token_teste, page)
        
        if dados.get("error_code") != 0:
            raise HTTPException(status_code=400, detail=dados.get("error_msg", "Erro na API Growatt"))
            
        return dados.get("data", {})
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))



@router.get("/dataloggers/{plant_id}")
async def list_dataloggers(plant_id: int, page: int = 1, perpage: int = 20):
    try:
        # Rota de dataloggers (ainda sem cache para simplificar o teste inicial)
        api_token_teste = settings.GROWATT_TOKEN
        client = GrowattClient(api_token_teste)
        
        dados = await client.get_datalogger_list(plant_id, page, perpage)
        
        if dados.get("error_code") != 0:
            raise HTTPException(status_code=400, detail=dados.get("error_msg", "Erro desconhecido na API"))
            
        return dados.get("data", {})
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))