from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql import func
from .client import SungrowClient
from app.modulos.apis.models import CacheAPI

# Tempo de cache ajustado para desenvolvimento (1 minuto)
TEMPO_CACHE_MINUTOS = 1

# ==========================================
# 1. USINAS (PLANTS)
# ==========================================
def normalizar_dados_sungrow(dados_brutos):
    """Transforma o JSON da Sungrow no padrão unificado do Frontend"""
    
    if str(dados_brutos.get("result_code")) != "1":
        return {
            "plants": [],
            "error_msg": dados_brutos.get("result_msg", "Erro de autenticação ou comunicação na Sungrow")
        }

    plantas_normalizadas = []
    
    result_data = dados_brutos.get("result_data") or {}
    page_list = result_data.get("pageList") or []
    
    for p in page_list:
        status_final = 0
        if p.get("ps_status") == 1:
            if p.get("ps_fault_status") == 3: # 3 = Normal na Sungrow
                status_final = 1 # Online
            else:
                status_final = -1 # Falha/Alarme
                
        # Monta a string de localização combinando endereço, cidade e província
        local = p.get("ps_location")
        cidade = p.get("city_name")
        if not local and cidade:
            local = f"{cidade} - {p.get('province_name', '')}"
        
        plantas_normalizadas.append({
            "plant_id": p.get("ps_id"),
            "name": p.get("ps_name", "Usina sem nome"),
            "status": status_final,
            "peak_power": p.get("total_capcity", {}).get("value", "0"),
            "total_energy": p.get("total_energy", {}).get("value", "0"),
            
            # --- NOVOS CAMPOS ADICIONADOS ---
            "current_power": p.get("curr_power", {}).get("value", "0"),
            "current_power_unit": p.get("curr_power", {}).get("unit", "W"),
            "daily_energy": p.get("today_energy", {}).get("value", "0"),
            "daily_energy_unit": p.get("today_energy", {}).get("unit", "kWh"),
            "address": local or "Local não informado",
            
            "marca": "Sungrow" 
        })
        
    return {"plants": plantas_normalizadas}


async def obter_plantas_sungrow_com_cache(db: AsyncSession, empresa_id: int, api_token: str, app_key: str, secret_key: str, page: int = 1):
    chave = f"sungrow_plant_list_{empresa_id}_page_{page}"
    
    stmt = select(CacheAPI).where(CacheAPI.chave_cache == chave)
    resultado = await db.execute(stmt)
    cache = resultado.scalars().first()

    agora = datetime.now(timezone.utc)

    if cache:
        tempo_passado = agora - cache.atualizado_em.replace(tzinfo=timezone.utc)
        if tempo_passado < timedelta(minutes=TEMPO_CACHE_MINUTOS):
            return normalizar_dados_sungrow(cache.dados)

    client = SungrowClient(api_token, app_key, secret_key)
    dados_frescos = await client.get_plant_list(page=page, size=100)

    if str(dados_frescos.get("result_code")) == "1":
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
    
    return normalizar_dados_sungrow(dados_frescos)


# ==========================================
# 2. ALARMES E FALHAS (FAULTS)
# ==========================================
def normalizar_falhas_sungrow(dados_brutos):
    """Padroniza a lista de falhas para o Frontend"""
    falhas_normalizadas = []
    
    page_list = dados_brutos.get("result_data", {}).get("pageList", []) if dados_brutos.get("result_data") else []
    
    for f in page_list:
        falhas_normalizadas.append({
            "plant_id": f.get("ps_id"),
            "plant_name": f.get("ps_name"),
            "device_name": f.get("device_name"),
            "fault_code": f.get("fault_code"),
            "fault_name": f.get("fault_name"),
            "fault_desc": f.get("fault_desc", "Sem descrição"),
            "create_time": f.get("create_time"),
            "recovery_time": f.get("over_time", ""),
            "status": "Resolvido" if f.get("process_status") == 9 else "Ativo",
            "marca": "Sungrow"
        })
        
    return {"faults": falhas_normalizadas}


async def obter_falhas_sungrow_com_cache(db: AsyncSession, empresa_id: int, api_token: str, app_key: str, secret_key: str, page: int = 1, ps_id: int = None):
    sufixo_usina = f"_ps_{ps_id}" if ps_id else "_all"
    chave = f"sungrow_faults_{empresa_id}{sufixo_usina}_page_{page}"
    
    stmt = select(CacheAPI).where(CacheAPI.chave_cache == chave)
    resultado = await db.execute(stmt)
    cache = resultado.scalars().first()

    agora = datetime.now(timezone.utc)

    if cache:
        tempo_passado = agora - cache.atualizado_em.replace(tzinfo=timezone.utc)
        if tempo_passado < timedelta(minutes=TEMPO_CACHE_MINUTOS):
            return normalizar_falhas_sungrow(cache.dados)

    client = SungrowClient(api_token, app_key, secret_key)
    dados_frescos = await client.get_fault_alarm_info(page=page, size=100, ps_id=ps_id)

    if str(dados_frescos.get("result_code")) == "1":
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
    
    return normalizar_falhas_sungrow(dados_frescos)


# ==========================================
# 3. EQUIPAMENTOS (DATALOGGERS/DEVICES)
# ==========================================
def normalizar_dispositivos_sungrow(dados_brutos):
    """
    Padroniza a lista de dispositivos (dataloggers/inversores) 
    para o Frontend consumir no mesmo formato, independente da marca.
    """
    
    if str(dados_brutos.get("result_code")) != "1":
        return {
            "dataloggers": [],
            "error_msg": dados_brutos.get("result_msg", "Erro ao buscar dispositivos na Sungrow")
        }

    dispositivos_normalizados = []
    
    # Extrai a lista paginada do JSON da Sungrow
    result_data = dados_brutos.get("result_data") or {}
    page_list = result_data.get("pageList") or []
    
    for dev in page_list:
        # LÓGICA DE STATUS
        # dev_status: 0 (Undeployed/Offline), 1 (Deployed/Online)
        # dev_fault_status: 1 (Fault), 2 (Alarm), 4 (Normal)
        is_lost = False
        if str(dev.get("dev_status")) == "0" or str(dev.get("dev_fault_status")) == "1":
            is_lost = True

        # LÓGICA DE DATA
        last_time_obj = None
        raw_time = dev.get("rel_time") or dev.get("grid_connection_date")
        
        if raw_time:
            try:
                from datetime import datetime
                # A API da Sungrow devolve no padrão "2025-07-28 09:57:21"
                dt = datetime.strptime(raw_time, "%Y-%m-%d %H:%M:%S")
                
                # Montamos o objeto exatamente como o Javascript (detalhes.html) espera
                last_time_obj = {
                    "date": dt.day,
                    "month": dt.month,
                    "year": dt.year - 1900,  # O JS soma 1900, então enviamos subtraído
                    "hours": dt.hour,
                    "minutes": dt.minute,
                    "seconds": dt.second
                }
            except Exception as e:
                print(f"Erro ao converter data do dispositivo Sungrow: {e}")
                pass 

        # ADICIONANDO À LISTA NORMALIZADA
        dispositivos_normalizados.append({
            "sn": dev.get("device_sn", "SN Desconhecido"),
            "manufacturer": dev.get("factory_name", "Sungrow"),
            "model": dev.get("device_model_code", "Desconhecido"),
            "type": dev.get("type_name", "Inversor"),
            "lost": is_lost,
            "last_update_time": last_time_obj
        })
        
    return {"dataloggers": dispositivos_normalizados}


async def obter_dispositivos_sungrow_com_cache(db: AsyncSession, empresa_id: int, api_token: str, app_key: str, secret_key: str, ps_id: int, page: int = 1):
    chave = f"sungrow_devices_ps_{ps_id}_{empresa_id}_page_{page}"
    
    stmt = select(CacheAPI).where(CacheAPI.chave_cache == chave)
    resultado = await db.execute(stmt)
    cache = resultado.scalars().first()

    agora = datetime.now(timezone.utc)

    if cache:
        tempo_passado = agora - cache.atualizado_em.replace(tzinfo=timezone.utc)
        if tempo_passado < timedelta(minutes=TEMPO_CACHE_MINUTOS):
            return normalizar_dispositivos_sungrow(cache.dados)

    client = SungrowClient(api_token, app_key, secret_key)
    dados_frescos = await client.get_device_list(ps_id=ps_id, page=page, size=50)

    if str(dados_frescos.get("result_code")) == "1":
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
    
    return normalizar_dispositivos_sungrow(dados_frescos)