# app/core/modules/apis/deye/service.py
import asyncio
import calendar
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql import func

from app.modulos.apis.models import CacheAPI
from .client import DeyeClient
from .models import DeyeConfig

TEMPO_CACHE_MINUTOS = 5

async def get_valid_deye_client(db: AsyncSession, config: DeyeConfig) -> DeyeClient:
    agora = datetime.now(timezone.utc)
    
    # 1. Proteção de timezone igual a que você fez no cache
    expires_at = config.token_expires_at.replace(tzinfo=timezone.utc) if config.token_expires_at else None
    
    # Usa a nova variável expires_at na verificação
    if not config.access_token or not expires_at or agora >= (expires_at - timedelta(minutes=5)):
        
        client = DeyeClient(
            app_id=config.app_id, 
            app_secret=config.app_secret,
            email=config.email,
            password_hash=config.password_hash,
            company_id=config.company_id,
            api_url=config.api_url
        )
        
        res = await client.get_access_token()
        
        if not res.get("success"):
            raise Exception(f"Falha ao autenticar na Deye: {res.get('msg', 'Desconhecido')} - Code: {res.get('code')}")
            
        # 2. Busca os dados dentro do nó "data", com fallback para a raiz
        payload = res.get("data", res)
        
        expires_in = int(payload.get("expiresIn", 5183999)) 
        
        # Puxa o token do payload correto
        config.access_token = payload.get("accessToken")
        config.token_expires_at = agora + timedelta(seconds=expires_in)
        
        db.add(config)
        await db.commit()
        
        return client
            
    return DeyeClient(
        app_id=config.app_id, 
        app_secret=config.app_secret,
        email=config.email,
        password_hash=config.password_hash,
        company_id=config.company_id,
        api_url=config.api_url,
        access_token=config.access_token
    )

async def obter_plantas_deye_com_cache(db: AsyncSession, empresa_id: int, config: DeyeConfig, page: int = 1):
    chave = f"deye_plants_enriched_{empresa_id}_page_{page}"
    
    # 1. Verifica se existe cache válido
    stmt = select(CacheAPI).where(CacheAPI.chave_cache == chave)
    resultado = await db.execute(stmt)
    cache = resultado.scalars().first()

    if cache:
        tempo_passado = datetime.now(timezone.utc) - cache.atualizado_em.replace(tzinfo=timezone.utc)
        if tempo_passado < timedelta(minutes=TEMPO_CACHE_MINUTOS):
            return cache.dados

    # 2. Obtém o cliente autenticado (renova o token se necessário)
    try:
        client = await get_valid_deye_client(db, config)
    except Exception as e:
         return {"plants": [], "error_msg": str(e)}

    # 3. Busca a lista de Usinas + Inversores na Deye
    res_list = await client.get_plant_page(page_num=page, page_size=49)

    # VAMOS ADICIONAR ESTES DOIS PRINTS AQUI PARA DEBUGAR:
    print("\n" + "="*50)
    print(f"[DEBUG DEYE] Resposta bruta da API: {res_list}")
    print("="*50 + "\n")

    if not res_list.get("success"):
        msg = res_list.get("msg", "Erro desconhecido na Deye")
        return {"plants": [], "error_msg": msg}

    plantas_lista = res_list.get("stationList", [])
    if not plantas_lista:
        plantas_lista = []

    # ================= LÓGICA DE ENRIQUECIMENTO DE DADOS =================
    async def fetch_and_normalize(p):
        from datetime import datetime, timedelta 

        plant_id = p.get("id")
        name = p.get("name", "Usina sem nome")
        endereco_final = p.get("locationAddress", "Local não informado")
        peak_power = float(p.get("installedCapacity", 0) or 0)
        
        status_inversor = 0
        devices = p.get("deviceListItems", [])
        
        for dev in devices:
            if str(dev.get("connectStatus", "0")) in ["1", "2"]:
                status_inversor = 1

        # --- CORREÇÃO DAS DATAS (O Segredo do "Excluded") ---
        agora = datetime.now()
        
        hoje_str = agora.strftime("%Y-%m-%d")
        amanha = agora + timedelta(days=1)
        amanha_str = amanha.strftime("%Y-%m-%d") # Usado como endAt (excluído)
        
        ano_str = agora.strftime("%Y")
        ano_que_vem_str = str(int(ano_str) + 1) # Usado como endAt (excluído)

        current_power_kw = 0.0
        today_energy = 0.0
        total_energy = 0.0

        # Dispara chamadas pararelas focadas na USINA
        task_latest = client.get_station_latest(plant_id)
        # Passando amanha_str para garantir que 'hoje' venha no resultado
        task_today = client.get_station_history(plant_id, hoje_str, amanha_str, 2)
        # Passando ano_que_vem_str para garantir que o 'ano_atual' venha no resultado
        task_total = client.get_station_history(plant_id, "2020", ano_que_vem_str, 4)

        resultados = await asyncio.gather(task_latest, task_today, task_total, return_exceptions=True)

        res_latest = resultados[0] if isinstance(resultados[0], dict) else {}
        res_today = resultados[1] if isinstance(resultados[1], dict) else {}
        res_total = resultados[2] if isinstance(resultados[2], dict) else {}

        # Extrai a Geração de Hoje
        if res_today.get("success") and res_today.get("stationDataItems"):
            for item in res_today.get("stationDataItems", []):
                today_energy += float(item.get("generationValue", 0) or 0)

        # Extrai a Geração Total (Soma todos os anos retornados)
        if res_total.get("success") and res_total.get("stationDataItems"):
            for item in res_total.get("stationDataItems", []):
                total_energy += float(item.get("generationValue", 0) or 0)

        # Extrai a Potência Atual do LATEST
        if res_latest.get("success"):
            current_power_kw = float(res_latest.get("generationPower", 0) or 0)

        # Retorno pronto para a tela do JS
        return {
            "plant_id": str(plant_id),
            "name": name,
            "status": status_inversor,
            "peak_power": str(round(peak_power, 2)),
            "total_energy": str(round(total_energy, 2)),
            "current_power": str(round(current_power_kw, 2)), 
            "current_power_unit": "kW",
            "daily_energy": str(round(today_energy, 2)),
            "daily_energy_unit": "kWh",
            "address": endereco_final,
            "marca": "DEYE"
        }

    # Processa todas as plantas simultaneamente (concorrência)
    tasks = [fetch_and_normalize(p) for p in plantas_lista]
    plantas_normalizadas = await asyncio.gather(*tasks)

    # Monta o resultado final
    total_plantas = res_list.get("stationTotal", len(plantas_normalizadas))
    resultado_final = {"plants": plantas_normalizadas, "total": total_plantas}

    # 4. Salva ou atualiza o Cache no banco de dados
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


async def obter_detalhes_usina_deye(db: AsyncSession, empresa_id: int, config: DeyeConfig, plant_id: str):
    from datetime import datetime, timedelta, timezone
    import asyncio
    
    # 1. Autentica
    try:
        client = await get_valid_deye_client(db, config)
    except Exception as e:
         return {"error_msg": str(e)}

    agora = datetime.now()
    inicio_dia = agora.replace(hour=0, minute=0, second=0, microsecond=0)
    start_ts = int(inicio_dia.timestamp())
    end_ts = int(agora.timestamp())
    
    hoje_str = agora.strftime("%Y-%m-%d")
    amanha = agora + timedelta(days=1)
    amanha_str = amanha.strftime("%Y-%m-%d")

    # ================= CORREÇÃO DE DATAS PARA A DEYE =================
    primeiro_dia_mes = agora.replace(day=1)
    primeiro_dia_mes_str = primeiro_dia_mes.strftime("%Y-%m-%d") # Ex: 2026-08-01
    
    # Pega exatamente o último dia do mês atual
    _, num_dias_mes = calendar.monthrange(agora.year, agora.month)
    ultimo_dia_mes = agora.replace(day=num_dias_mes)
    ultimo_dia_mes_str = ultimo_dia_mes.strftime("%Y-%m-%d") # Ex: 2026-08-31
    
    ano_str = agora.strftime("%Y")
    ano_que_vem_str = str(int(ano_str) + 1)

    # 2. Chama as rotas em paralelo
    task_latest = client.get_station_latest(int(plant_id))
    task_history_today = client.get_station_history(int(plant_id), hoje_str, amanha_str, 2)
    # Granularidade 2 (Diário) e datas blindadas
    task_history_month = client.get_station_history(int(plant_id), primeiro_dia_mes_str, ultimo_dia_mes_str, 2)
    task_history_total = client.get_station_history(int(plant_id), "2020", ano_que_vem_str, 4)
    task_chart = client.get_station_chart_data(int(plant_id), start_ts, end_ts)
    
    # Busca a lista de inversores e detalhes cadastrais
    task_lista_usinas = client.get_plant_page(1, 100)

    resultados = await asyncio.gather(
        task_latest, task_history_today, task_history_month, task_history_total, task_chart, task_lista_usinas, 
        return_exceptions=True
    )

    res_latest = resultados[0] if isinstance(resultados[0], dict) else {}
    res_today = resultados[1] if isinstance(resultados[1], dict) else {}
    res_month = resultados[2] if isinstance(resultados[2], dict) else {}
    res_total = resultados[3] if isinstance(resultados[3], dict) else {}
    res_chart = resultados[4] if isinstance(resultados[4], dict) else {}
    res_usinas = resultados[5] if isinstance(resultados[5], dict) else {}

    # ====================================================================
    # LOGS DE DIAGNÓSTICO PROFUNDO
    # ====================================================================
    print("\n" + "="*60)
    print(f"📡 [DEBUG DEYE] RESPOSTAS DA USINA ID: {plant_id}")
    print(f"▶️ DATAS ENVIADAS -> Hoje: {hoje_str} | Mês: {primeiro_dia_mes_str} até {ultimo_dia_mes_str}")
    print(f"3. MÊS (Granularity 2): {res_month.get('success')} | Data: {res_month.get('stationDataItems', [])[:1]}")
    print("="*60 + "\n")
    # ====================================================================

    # --- Extração dos Dados Cadastrais e Dataloggers ---
    data_ativacao = "N/A"
    tipo_instalacao = "N/A"
    tipo_interconexao = "N/A"
    dataloggers = []

    if res_usinas.get("success"):
        for station in res_usinas.get("stationList", []):
            if str(station.get("id")) == str(plant_id):
                
                # Dados Cadastrais
                ts_start = station.get("startOperatingTime")
                if ts_start:
                    dt_start = datetime.fromtimestamp(ts_start)
                    data_ativacao = dt_start.strftime("%d/%m/%Y")
                
                tipo_instalacao = station.get("type", "N/A")
                tipo_interconexao = station.get("gridInterconnectionType", "N/A")
                
                # Inversores (Dataloggers)
                for dev in station.get("deviceListItems", []):
                    ts = dev.get("collectionTime", 0)
                    dt = datetime.fromtimestamp(ts) if ts else None
                    
                    dataloggers.append({
                        "sn": dev.get("deviceSn"),
                        "manufacturer": "DEYE",
                        "model": dev.get("deviceType"),
                        "lost": dev.get("connectStatus", 0) == 0,
                        "last_update_time": {
                            "date": dt.day, "month": dt.month, "year": dt.year - 1900,
                            "hours": dt.hour, "minutes": dt.minute, "seconds": dt.second
                        } if dt else None
                    })
                break

    # --- Montagem dos KPIs (Arredondados para 2 casas) ---
    detalhes = {
        "current_power": res_latest.get("generationPower", 0),
        "daily_energy": round(sum([float(i.get("generationValue", 0)) for i in res_today.get("stationDataItems", [])]), 2) if res_today.get("success") else 0,
        "monthly_energy": round(sum([float(i.get("generationValue", 0)) for i in res_month.get("stationDataItems", [])]), 2) if res_month.get("success") else 0,
        "total_energy": round(sum([float(i.get("generationValue", 0)) for i in res_total.get("stationDataItems", [])]), 2) if res_total.get("success") else 0,
        "start_date": data_ativacao,
        "installation_type": tipo_instalacao,
        "interconnection_type": tipo_interconexao
    }

    # --- Montagem do Gráfico de Histórico Mensal ---
    history_chart = []
    if res_month.get("success") and res_month.get("stationDataItems"):
        for item in res_month.get("stationDataItems", []):
            
            # Puxa o ano, mês e dia separados que a Deye manda
            ano = item.get("year")
            mes = item.get("month")
            dia = item.get("day")
            
            # Se vierem separados, montamos no formato "YYYY-MM-DD"
            if ano and mes and dia:
                tempo_formatado = f"{ano}-{mes:02d}-{dia:02d}"
            else:
                # Fallback caso a Deye decida mandar timestamp no futuro
                tempo_formatado = item.get("timeStamp") or item.get("time") or item.get("dateStr")
                
            history_chart.append({
                "time": tempo_formatado,
                "energy": float(item.get("generationValue", 0) or 0)
            })
    detalhes["history_chart"] = history_chart

    # --- Montagem do Fluxo Bateria / Consumo ---
    fluxo = {}
    
    if res_latest.get("batterySOC") is not None:
        fluxo["battery_soc"] = res_latest.get("batterySOC")
    if res_latest.get("chargePower") is not None:
        fluxo["charge_power"] = res_latest.get("chargePower")
    if res_latest.get("dischargePower") is not None:
        fluxo["discharge_power"] = res_latest.get("dischargePower")

    if res_latest.get("consumptionPower") is not None:
        fluxo["consumption_power"] = res_latest.get("consumptionPower")
    if res_latest.get("gridPower") is not None:
        fluxo["grid_power"] = res_latest.get("gridPower")
    if res_latest.get("purchasePower") is not None:
        fluxo["purchase_power"] = res_latest.get("purchasePower")

    detalhes["fluxo"] = fluxo

    # --- Montagem do Gráfico (Time vs Potência Hoje) ---
    chart_data = []
    if res_chart.get("success") and res_chart.get("stationDataItems"):
        for item in res_chart.get("stationDataItems", []):
            chart_data.append({
                "time": item.get("timeStamp") or item.get("time"),
                "power": float(item.get("generationPower", 0) or 0)
            })
    detalhes["chart"] = chart_data
    detalhes["dataloggers"] = dataloggers

    return detalhes