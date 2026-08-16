import asyncio
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql import func
from .client import SajClient
from .models import SajConfig
from app.modulos.apis.models import CacheAPI 

TEMPO_CACHE_MINUTOS = 5

async def get_valid_saj_client(db: AsyncSession, config: SajConfig) -> SajClient:
    agora = datetime.now(timezone.utc)
    
    # 1. Proteção contra o erro de Timezone (TypeError)
    expires_at = config.token_expires_at.replace(tzinfo=timezone.utc) if config.token_expires_at else None
    
    if not config.access_token or not expires_at or agora >= (expires_at - timedelta(minutes=1)):
        client = SajClient(app_id=config.app_id, app_secret=config.app_secret, api_url=config.api_url)
        res = await client.get_access_token()
        
        if "error_code" in res:
            raise Exception(res.get("error_msg"))
            
        # 2. SAJ aceita 0 ou 200 como sucesso
        code = res.get("code")
        if code in [0, 200, "0", "200"] and "data" in res:
            dados_token = res["data"]
            expires_in = int(dados_token.get("expires", 28800))
            config.access_token = dados_token.get("access_token")
            config.token_expires_at = agora + timedelta(seconds=expires_in)
            
            db.add(config)
            await db.commit()
            
            client.access_token = config.access_token
            return client
        else:
            raise Exception(f"Falha ao autenticar na SAJ: Code {code} - {res.get('msg', 'Desconhecido')}")
            
    return SajClient(
        app_id=config.app_id, 
        app_secret=config.app_secret, 
        api_url=config.api_url, 
        access_token=config.access_token
    )



async def obter_plantas_saj_com_cache(db: AsyncSession, empresa_id: int, config: SajConfig, page: int = 1):
    chave = f"saj_plants_enriched_{empresa_id}_page_{page}"
    
    stmt = select(CacheAPI).where(CacheAPI.chave_cache == chave)
    resultado = await db.execute(stmt)
    cache = resultado.scalars().first()

    agora = datetime.now() # Usa horário local da máquina
    start_time_str = agora.strftime("%Y-%m-%d 00:00:00")
    end_time_str = agora.strftime("%Y-%m-%d 23:59:59") # Coleta tudo do dia atual

    if cache:
        tempo_passado = datetime.now(timezone.utc) - cache.atualizado_em.replace(tzinfo=timezone.utc)
        if tempo_passado < timedelta(minutes=TEMPO_CACHE_MINUTOS):
            return cache.dados

    try:
        client = await get_valid_saj_client(db, config)
    except Exception as e:
         return {"plants": [], "error_msg": str(e)}

    # Busca a lista BÁSICA de usinas
    res_list = await client.get_plant_page(page_num=page, page_size=100)

    if "error_code" in res_list:
        return {"plants": [], "error_msg": res_list.get("error_msg")}

    codigo_retorno = res_list.get("code")
    if codigo_retorno not in [0, 200]:
        msg = res_list.get("msg", "Sem mensagem detalhada")
        return {"plants": [], "error_msg": f"Erro SAJ (Código {codigo_retorno}): {msg}"}

    plantas_lista = res_list.get("rows", [])
    if plantas_lista is None:
        plantas_lista = []

    # ================= LÓGICA DE ENRIQUECIMENTO DE DADOS =================
    async def fetch_and_normalize(p):
        plant_id = str(p.get("plantId", ""))
        name = p.get("plantName", "Usina sem nome")
        
        current_power_w = 0.0
        today_energy = 0.0
        total_energy = 0.0
        peak_power = 0.0
        status_inversor = 0 
        endereco_final = "Local não informado"

        # 1. Puxa os equipamentos da Usina
        dev_res = await client.get_plant_all_device_list(plant_id)
        if dev_res.get("code") in [0, 200]:
            devices = dev_res.get("data", [])
            if devices:
                for dev in devices:
                    if dev.get("deviceType") == 1:
                        inv_data = dev.get("inverterData", {})
                        if inv_data:
                            sn = inv_data.get("deviceSn")
                            
                            # Dados primários do inverterData (Fallback)
                            current_power_w += float(inv_data.get("powerNow", 0) or 0)
                            total_energy += float(inv_data.get("totalEnergy", 0) or 0)
                            
                            state = str(inv_data.get("runningState", "3"))
                            if state in ["1", "2"]:
                                status_inversor = 1 
                                
                            if sn:
                                # 2. Puxa o History Data do dia para pegar a Geração Diária (Ger. Hoje)
                                hist_res = await client.get_device_history_data(sn, start_time_str, end_time_str)
                                if hist_res.get("code") in [0, 200]:
                                    hist_data_list = hist_res.get("data", [])
                                    if hist_data_list and len(hist_data_list) > 0:
                                        # Pegamos o último registro de hoje
                                        last_record = hist_data_list[-1] 
                                        
                                        # A SAJ pode mandar como todayEnergy ou todayPvEnergy
                                        ger_hoje = last_record.get("todayEnergy") or last_record.get("todayPvEnergy", 0)
                                        today_energy += float(ger_hoje or 0)
                                        print(f"[DEBUG SAJ] Histórico do Inversor {sn} encontrado! Ger. Hoje: {ger_hoje}kWh")
                                    else:
                                        print(f"[DEBUG SAJ] Inversor {sn} sem registros no histórico de hoje.")

                                # 3. Puxa Base Info para Potência Pico
                                info_res = await client.get_device_baseinfo(sn)
                                if info_res.get("code") in [0, 200]:
                                    base_data = info_res.get("data", {})
                                    peak_power += float(base_data.get("ratedPower", 0) or 0)

        # 4. Puxa o Endereço (Detalhes)
        details_res = await client.get_plant_details(plant_id)
        if details_res.get("code") in [0, 200]:
            det_data = details_res.get("data", {})
            full_address = det_data.get("fullAddress")
            city = det_data.get("city")
            country = det_data.get("country")
            address = det_data.get("address")
            
            if full_address and str(full_address).strip():
                endereco_final = str(full_address).strip()
            elif city or country:
                endereco_parts = [p for p in [city, country] if p and str(p).strip()]
                endereco_final = ", ".join(endereco_parts)
            elif address and str(address).strip():
                endereco_final = str(address).strip()

        current_power_kw = round(current_power_w / 1000, 2)

        return {
            "plant_id": plant_id,
            "name": name,
            "status": status_inversor,
            "peak_power": str(round(peak_power, 2)),
            "total_energy": str(round(total_energy, 2)),
            "current_power": str(current_power_kw),
            "current_power_unit": "kW",
            "daily_energy": str(round(today_energy, 2)),
            "daily_energy_unit": "kWh",
            "address": endereco_final,
            "marca": "SAJ"
        }

    tasks = [fetch_and_normalize(p) for p in plantas_lista]
    plantas_normalizadas = await asyncio.gather(*tasks)

    total_plantas = res_list.get("total", len(plantas_normalizadas))

    resultado_final = {"plants": plantas_normalizadas, "total": total_plantas}

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