# app/core/modules/apis/deye/client.py
import httpx
import hashlib
from typing import Optional

class DeyeClient:
    def __init__(
        self, 
        app_id: str, 
        app_secret: str, 
        email: str, 
        password_hash: str, 
        company_id: Optional[int] = None,
        api_url: str = "https://us1-developer.deyecloud.com", 
        access_token: Optional[str] = None
    ):
        self.app_id = app_id
        self.app_secret = app_secret
        self.email = email
        self.password_hash = password_hash
        self.company_id = company_id
        self.base_url = api_url.rstrip('/')
        self.access_token = access_token

    def _get_headers(self, include_auth: bool = True) -> dict:
        headers = {
            "Content-Type": "application/json"
        }
        if include_auth and self.access_token:
            # Verifica se o token já contém "Bearer " para evitar duplicação
            if self.access_token.lower().startswith("bearer "):
                headers["Authorization"] = self.access_token
            else:
                headers["Authorization"] = f"Bearer {self.access_token}"
        return headers

    async def get_access_token(self) -> dict:
        """Autentica na DeyeCloud e retorna o Token. O App ID vai na URL."""
        url = f"{self.base_url}/v1.0/account/token?appId={self.app_id}"
        
        payload = {
            "appSecret": self.app_secret,
            "email": self.email,
            "password": self.password_hash
        }
        
        # Se for uma conta Business, injetamos o companyId
        if self.company_id:
            payload["companyId"] = self.company_id

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(url, json=payload, headers=self._get_headers(include_auth=False))
                
                if response.status_code != 200:
                    return {"success": False, "msg": f"Erro HTTP Token Deye: {response.text}", "code": response.status_code}
                
                data = response.json()
                
                if data.get("success"):
                    # Extrai o token de dentro do nó "data"
                    payload_resp = data.get("data", data)
                    self.access_token = payload_resp.get("accessToken")
                    
                return data
                
        except Exception as e:
            return {"success": False, "msg": f"Erro Conexão Deye: {str(e)}", "code": 999}

    async def get_account_info(self) -> dict:
        """Busca informações da conta, útil para descobrir o companyId dinamicamente se necessário."""
        url = f"{self.base_url}/v1.0/account/info"
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(url, json={}, headers=self._get_headers(include_auth=True))
                return response.json()
        except Exception as e:
            return {"success": False, "msg": str(e), "code": 999}

    # =========================================================================
    # ENDPOINTS DE MONITORAMENTO
    # =========================================================================
    
    async def get_plant_page(self, page_num: int = 1, page_size: int = 100) -> dict:
        """Busca a lista de usinas e seus respectivos dispositivos na DeyeCloud."""
        url = f"{self.base_url}/v1.0/station/listWithDevice"
        
        payload = {
            "deviceType": "INVERTER",
            "page": page_num,
            "size": page_size
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    url, 
                    json=payload, 
                    headers=self._get_headers(include_auth=True)
                )
                
                if response.status_code != 200:
                    return {
                        "success": False, 
                        "msg": f"Erro HTTP Plantas Deye: {response.text}", 
                        "code": response.status_code
                    }
                    
                return response.json()
        except Exception as e:
            return {"success": False, "msg": f"Erro Conexão Deye: {str(e)}", "code": 999}

    async def get_station_latest(self, station_id: int) -> dict:
        """Busca o resumo atualizado da Usina."""
        url = f"{self.base_url}/v1.0/station/latest"
        payload = {"stationId": station_id}
        
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(url, json=payload, headers=self._get_headers(include_auth=True))
                return response.json()
        except Exception as e:
            return {"success": False, "msg": str(e), "code": 999}

    async def get_station_history(self, station_id: int, start_at: str, end_at: str, granularity: int) -> dict:
        """
        Busca o histórico consolidado da Usina (Geração Diária ou Total).
        granularity: 1 (Frame), 2 (Dia), 3 (Mês), 4 (Ano)
        """
        url = f"{self.base_url}/v1.0/station/history"
        payload = {
            "stationId": station_id,
            "startAt": start_at,
            "endAt": end_at,
            "granularity": granularity
        }
        
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.post(url, json=payload, headers=self._get_headers(include_auth=True))
                return response.json()
        except Exception as e:
            return {"success": False, "msg": str(e), "code": 999}

    async def get_station_chart_data(self, station_id: int, start_ts: int, end_ts: int) -> dict:
        """
        Busca os pontos de potência para montar o gráfico de linha (curva de geração).
        Passamos o início e fim do dia atual em timestamp (segundos).
        """
        url = f"{self.base_url}/v1.0/station/history/power"
        payload = {
            "stationId": station_id,
            "startTimestamp": start_ts,
            "endTimestamp": end_ts
        }
        
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.post(url, json=payload, headers=self._get_headers(include_auth=True))
                return response.json()
        except Exception as e:
            return {"success": False, "msg": str(e), "code": 999}