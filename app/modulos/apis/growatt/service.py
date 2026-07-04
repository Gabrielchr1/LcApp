from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql import func
from .client import GrowattClient
from app.modulos.apis.models import CacheAPI

TEMPO_CACHE_MINUTOS = 1440

async def obter_plantas_com_cache(db: AsyncSession, empresa_id: int, api_token: str, page: int = 1):
    # A chave do cache agora depende apenas da empresa e da página
    chave = f"growatt_plant_list_{empresa_id}_page_{page}"
    
    stmt = select(CacheAPI).where(CacheAPI.chave_cache == chave)
    resultado = await db.execute(stmt)
    cache = resultado.scalars().first()

    agora = datetime.now(timezone.utc)

    if cache:
        tempo_passado = agora - cache.atualizado_em.replace(tzinfo=timezone.utc)
        if tempo_passado < timedelta(minutes=TEMPO_CACHE_MINUTOS):
            return cache.dados

    client = GrowattClient(api_token)
    # Não passamos mais user_name aqui
    dados_frescos = await client.get_plant_list(page=page, perpage=100)

    if dados_frescos.get("error_code") == 0:
        if cache:
            cache.dados = dados_frescos
            cache.atualizado_em = func.now()
        else:
            novo_cache = CacheAPI(
                empresa_id=empresa_id,
                chave_cache=chave,
                dados=dados_frescos
            )
            db.add(novo_cache)
        await db.commit()
    
    return dados_frescos