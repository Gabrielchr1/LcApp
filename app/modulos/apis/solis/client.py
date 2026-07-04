# app/modulos/apis/solis/client.py

import json
import httpx
import hashlib
import hmac
import base64
from datetime import datetime, timezone

class SolisClient:
    def __init__(self, api_url: str, key_id: str, key_secret: str):
        self.base_url = api_url.rstrip('/')
        self.key_id = key_id.strip() if key_id else ""
        self.key_secret = key_secret.strip() if key_secret else ""
        
    def _generate_headers(self, path: str, body_json: str) -> dict:
        """Gera os headers dinâmicos recebendo a string JSON exata."""
        
        # 1. Content-MD5
        md5_hash = hashlib.md5(body_json.encode('utf-8')).digest()
        content_md5 = base64.b64encode(md5_hash).decode('utf-8')
        
        # 2. Date e Content-Type
        content_type = "application/json"
        now = datetime.now(timezone.utc)
        date_str = now.strftime('%a, %d %b %Y %H:%M:%S GMT')
        
        # 3. Gerar a Assinatura (Authorization)
        sign_string = f"POST\n{content_md5}\n{content_type}\n{date_str}\n{path}"
        
        hmac_hash = hmac.new(
            self.key_secret.encode('utf-8'),
            sign_string.encode('utf-8'),
            hashlib.sha1
        ).digest()
        
        sign_b64 = base64.b64encode(hmac_hash).decode('utf-8')
        
        return {
            "Content-MD5": content_md5,
            "Content-Type": content_type,
            "Date": date_str,
            "Authorization": f"API {self.key_id}:{sign_b64}"
        }

    async def _post(self, path: str, payload: dict):
        url = f"{self.base_url}{path}"
        
        # CUIDADO EXTREMO: Serializa o JSON sem espaços em branco. 
        # Isso garante que o MD5 gerado será igual ao corpo da requisição.
        body_json = json.dumps(payload, separators=(',', ':'))
        headers = self._generate_headers(path, body_json)
        
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                # Enviamos 'content=body_json.encode' em vez de 'json=payload' para o httpx não alterar nada!
                response = await client.post(url, content=body_json.encode('utf-8'), headers=headers)
                
                if response.status_code != 200:
                    return {"code": str(response.status_code), "msg": f"Erro HTTP Solis: {response.text}"}
                
                return response.json()
        except Exception as e:
            return {"code": "999", "msg": f"Erro de Conexão Solis: {str(e)}"}

    async def get_station_list(self, page: int = 1, size: int = 100):
        path = "/v1/api/userStationList"
        payload = {"pageNo": page, "pageSize": size}
        return await self._post(path, payload)

    async def get_inverter_list(self, station_id: str, page: int = 1, size: int = 100):
        path = "/v1/api/inverterList"
        # A doc da Solis exige que stationId seja do tipo Integer. Convertendo aqui.
        payload = {"stationId": int(station_id), "pageNo": page, "pageSize": size}
        return await self._post(path, payload)
    

# Adicione este método no final da classe SolisClient no seu client.py
    async def get_collector_list(self, station_id: str, page: int = 1, size: int = 100):
        """Busca a lista de dataloggers (collectors) de uma usina."""
        path = "/v1/api/collectorList"
        # O stationId deve ser enviado como string para não dar erro de permissão
        payload = {"pageNo": page, "pageSize": size, "stationId": str(station_id)}
        return await self._post(path, payload)