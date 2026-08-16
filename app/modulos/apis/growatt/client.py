import httpx
from app.core.config import settings

class GrowattClient:
    def __init__(self, api_token: str, api_url: str = "https://openapi.growatt.com/v1"):
        self.base_url = api_url.rstrip('/')
        self.headers = {
            "token": api_token,
            "Content-Type": "application/x-www-form-urlencoded" 
        }

    async def get_plant_list(self, page: int = 1, perpage: int = 100):
            # Rota correta para listar TODAS as usinas do Token
            url = f"{self.base_url}/plant/list"
            
            # Como é GET, os parâmetros vão na URL (params), não no corpo (data)
            params = {"page": page, "perpage": perpage}
            
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.get(url, params=params, headers=self.headers)
                    
                    if response.status_code != 200:
                        return {"error_code": response.status_code, "error_msg": f"Erro HTTP Growatt: {response.text}"}
                    
                    return response.json()
            except Exception as e:
                return {"error_code": 999, "error_msg": f"Erro Local: {str(e)}"}

    async def get_datalogger_list(self, plant_id: int, page: int = 1, perpage: int = 20):
        url = f"{self.base_url}/device/datalogger/list"
        params = {"plant_id": plant_id, "page": page, "perpage": perpage}
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params, headers=self.headers)
                if response.status_code != 200:
                    return {"error_code": response.status_code, "error_msg": f"Erro HTTP Growatt: {response.text}"}
                return response.json()
        except Exception as e:
            return {"error_code": 999, "error_msg": f"Erro de Conexão Local: {str(e)}"}

    # Adicione este novo método no final da classe GrowattClient:

    async def get_plant_data(self, plant_id: int):
        """Busca os dados de geração e potência em tempo real de uma usina específica."""
        url = f"{self.base_url}/plant/data"
        params = {"plant_id": plant_id}
        
        try:
            # Timeout um pouco menor, já que faremos várias requisições em paralelo
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params, headers=self.headers)
                
                if response.status_code != 200:
                    return {"error_code": response.status_code, "error_msg": f"Erro HTTP Growatt: {response.text}"}
                
                return response.json()
        except Exception as e:
            return {"error_code": 999, "error_msg": f"Erro Local: {str(e)}"}