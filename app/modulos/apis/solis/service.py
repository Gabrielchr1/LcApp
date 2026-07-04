# app/modulos/apis/solis/service.py

from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql import func
from app.modulos.apis.models import CacheAPI
from .client import SolisClient

TEMPO_CACHE_MINUTOS = 1

# ==========================================
# 1. NORMALIZAR USINAS (PLANTS)
# ==========================================
def normalizar_plantas_solis(dados_brutos):
    """Transforma o JSON da Solis no padrão universal do Frontend"""
    
    # A Solis retorna success = True e code = "0" quando dá certo
    if str(dados_brutos.get("code")) != "0":
        return {
            "plants": [],
            "error_msg": dados_brutos.get("msg", "Erro de comunicação na SolisCloud")
        }

    plantas_normalizadas = []
    
    records = dados_brutos.get("data", {}).get("page", {}).get("records", [])
    
    for p in records:
        # Status da Solis: 1=online, 2=offline, 3=alarm
        status_raw = p.get("state", 2)
        status_final = 0
        if status_raw == 1:
            status_final = 1  # Online
        elif status_raw == 3:
            status_final = -1 # Falha
        else:
            status_final = 0  # Offline
            
        # Monta o endereço de forma inteligente (Fallback para Cidade/Estado)
        endereco = p.get("addr") or ""
        endereco = endereco.strip()
        
        if not endereco:
            cidade = p.get("cityStr", "")
            regiao = p.get("regionStr", "")
            # Ex: "Forster NSW" ou apenas a cidade se o estado não vier
            endereco = f"{cidade} {regiao}".strip()
            
        if not endereco:
            endereco = "Local não informado"
            
        plantas_normalizadas.append({
            # Envia como String para o JS não arredondar os 19 dígitos!
            "plant_id": str(p.get("id")),
            "name": p.get("stationName", "Usina sem nome"),
            "status": status_final,
            "peak_power": p.get("capacity", "0"),
            "total_energy": p.get("allEnergy", "0"),
            
            # Dados em tempo real para o nosso dashboard Premium
            "current_power": p.get("power", "0"),
            "current_power_unit": p.get("powerStr", "kW"),
            "daily_energy": p.get("dayEnergy", "0"),
            "daily_energy_unit": p.get("dayEnergyStr", "kWh"),
            "address": endereco,
            
            "marca": "Solis" 
        })
        
    return {"plants": plantas_normalizadas}

async def obter_plantas_solis_com_cache(db: AsyncSession, empresa_id: int, api_url: str, key_id: str, key_secret: str, page: int = 1):
    chave = f"solis_plant_list_{empresa_id}_page_{page}"
    
    stmt = select(CacheAPI).where(CacheAPI.chave_cache == chave)
    resultado = await db.execute(stmt)
    cache = resultado.scalars().first()

    agora = datetime.now(timezone.utc)

    if cache:
        tempo_passado = agora - cache.atualizado_em.replace(tzinfo=timezone.utc)
        if tempo_passado.total_seconds() < (TEMPO_CACHE_MINUTOS * 60):
            return normalizar_plantas_solis(cache.dados)

    client = SolisClient(api_url, key_id, key_secret)
    dados_frescos = await client.get_station_list(page=page, size=100)

    if str(dados_frescos.get("code")) == "0":
        if cache:
            cache.dados = dados_frescos
            cache.atualizado_em = func.now()
        else:
            novo_cache = CacheAPI(empresa_id=empresa_id, chave_cache=chave, dados=dados_frescos)
            db.add(novo_cache)
        await db.commit()
    
    return normalizar_plantas_solis(dados_frescos)

# ==========================================
# 2. NORMALIZAR EQUIPAMENTOS (COLLECTORS)
# ==========================================
def normalizar_dispositivos_solis(dados_brutos):
    if str(dados_brutos.get("code")) != "0":
        return {
            "dataloggers": [],
            "error_msg": dados_brutos.get("msg", "Erro ao buscar dataloggers na Solis")
        }

    dispositivos_normalizados = []
    
    # Acessa os dados dos collectors
    records = dados_brutos.get("data", {}).get("page", {}).get("records", [])
    
    for dev in records:
        # Status Solis Collector: 1=online, 2=offline, 3=alarm
        is_lost = str(dev.get("state")) != "1"

        last_time_obj = None
        ts = dev.get("dataTimestamp")
        if ts:
            try:
                dt = datetime.fromtimestamp(int(ts) / 1000)
                last_time_obj = {
                    "date": dt.day,
                    "month": dt.month,
                    "year": dt.year - 1900,
                    "hours": dt.hour,
                    "minutes": dt.minute,
                    "seconds": dt.second
                }
            except Exception as e:
                print(f"Erro ao converter data do Collector Solis: {e}")

        dispositivos_normalizados.append({
            "sn": dev.get("sn", "SN Desconhecido"),
            "manufacturer": "Solis",
            "model": dev.get("model", "Datalogger"), # Solis não manda modelo claro do datalogger sempre
            "type": "Collector",
            "lost": is_lost,
            "last_update_time": last_time_obj
        })
        
    return {"dataloggers": dispositivos_normalizados}

async def obter_dispositivos_solis_com_cache(db: AsyncSession, empresa_id: int, api_url: str, key_id: str, key_secret: str, ps_id: str, page: int = 1):
    chave = f"solis_collectors_ps_{ps_id}_{empresa_id}_page_{page}"
    
    stmt = select(CacheAPI).where(CacheAPI.chave_cache == chave)
    resultado = await db.execute(stmt)
    cache = resultado.scalars().first()

    agora = datetime.now(timezone.utc)

    if cache:
        tempo_passado = agora - cache.atualizado_em.replace(tzinfo=timezone.utc)
        if tempo_passado.total_seconds() < (TEMPO_CACHE_MINUTOS * 60):
            return normalizar_dispositivos_solis(cache.dados)

    client = SolisClient(api_url, key_id, key_secret)
    # Mudamos a chamada de get_inverter_list para get_collector_list!
    dados_frescos = await client.get_collector_list(station_id=ps_id, page=page, size=50)

    if str(dados_frescos.get("code")) == "0":
        if cache:
            cache.dados = dados_frescos
            cache.atualizado_em = func.now()
        else:
            novo_cache = CacheAPI(empresa_id=empresa_id, chave_cache=chave, dados=dados_frescos)
            db.add(novo_cache)
        await db.commit()
    
    return normalizar_dispositivos_solis(dados_frescos)