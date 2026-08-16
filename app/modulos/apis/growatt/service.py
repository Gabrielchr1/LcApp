import asyncio
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql import func
from .client import GrowattClient
from app.modulos.apis.models import CacheAPI

# REDUZIDO PARA 5 MINUTOS (Regra da API da Growatt para plant/data)
TEMPO_CACHE_MINUTOS = 5 

async def obter_plantas_com_cache(db: AsyncSession, empresa_id: int, api_token: str, api_url: str, page: int = 1):
    chave = f"growatt_plants_enriched_{empresa_id}_page_{page}"
    
    stmt = select(CacheAPI).where(CacheAPI.chave_cache == chave)
    resultado = await db.execute(stmt)
    cache = resultado.scalars().first()

    agora = datetime.now(timezone.utc)

    if cache:
        tempo_passado = agora - cache.atualizado_em.replace(tzinfo=timezone.utc)
        if tempo_passado < timedelta(minutes=TEMPO_CACHE_MINUTOS):
            return cache.dados

    client = GrowattClient(api_token, api_url)
    
    # 1. Busca a lista básica de usinas
    res_list = await client.get_plant_list(page=page, perpage=100)

    if str(res_list.get("error_code")) != "0":
        return {"plants": [], "error_msg": res_list.get("error_msg", "Erro ao buscar lista na Growatt")}

    # A Growatt às vezes retorna a lista direto em "data", ou dentro de "data" -> "plants"
    dados_brutos = res_list.get("data", [])
    plantas_lista = dados_brutos.get("plants", dados_brutos) if isinstance(dados_brutos, dict) else dados_brutos

    # 2. Função interna para buscar os detalhes de UMA usina e normalizar
    async def fetch_and_normalize(p):
        plant_id = p.get("plant_id") or p.get("id")
        
        # Busca os dados de tempo real
        dados_reais = await client.get_plant_data(plant_id)
        info = dados_reais.get("data", {}) if str(dados_reais.get("error_code")) == "0" else {}
        
        # Define o status (A Growatt geralmente usa 1 para online)
        status_raw = p.get("status", 0)
        status_final = 1 if str(status_raw) == "1" else 0
        
        # fallback de endereço
        endereco = p.get("plant_address", "") or p.get("city", "") or "Local não informado"
        
        return {
            "plant_id": str(plant_id),
            "name": p.get("plant_name", p.get("name", "Usina sem nome")),
            "status": status_final,
            "peak_power": info.get("peak_power_actual", p.get("nominal_power", "0")),
            "total_energy": info.get("total_energy", p.get("total_energy", "0")),
            "current_power": info.get("current_power", "0"),
            "current_power_unit": "kW",
            "daily_energy": info.get("today_energy", "0"),
            "daily_energy_unit": "kWh",
            "address": endereco,
            "marca": "Growatt"
        }

    # 3. Executa todas as requisições de detalhes de forma paralela (Assíncrona)
    tasks = [fetch_and_normalize(p) for p in plantas_lista]
    plantas_normalizadas = await asyncio.gather(*tasks)

    resultado_final = {"plants": plantas_normalizadas}

    # 4. Salva o resultado final rico no Banco de Dados
    if cache:
        cache.dados = resultado_final
        cache.atualizado_em = func.now()
    else:
        novo_cache = CacheAPI(
            empresa_id=empresa_id,
            chave_cache=chave,
            dados=resultado_final
        )
        db.add(novo_cache)
        
    await db.commit()
    
    return resultado_final