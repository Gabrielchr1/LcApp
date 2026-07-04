import httpx
from app.core.config import settings

class SungrowClient:
    def __init__(self, api_token: str, app_key: str, secret_key: str):
        self.base_url = settings.SUNGROW_API_URL.rstrip('/')
        
        # VALIDAÇÃO DE SEGURANÇA: Impede que o httpx delete o cabeçalho se a chave estiver vazia
        safe_secret_key = secret_key.strip() if secret_key else "CHAVE_VAZIA_ERRO_NO_ENV"
        safe_app_key = app_key.strip() if app_key else ""
        safe_token = api_token.strip() if api_token else ""

        self.headers = {
            "Content-Type": "application/json;charset=UTF-8",
            "sys_code": "901", 
            "x-access-key": safe_secret_key
        }
        
        self.base_payload = {
            "appkey": safe_app_key,
            "token": safe_token,
            "lang": "_pt_BR" 
        }

        # LOGGER PARA DEBUG: Vai imprimir no seu console (VS Code / Terminal)
        print("\n--- INICIANDO CONEXÃO SUNGROW ---")
        print(f"URL Base: {self.base_url}")
        print(f"Headers enviados: {self.headers}")
        print("---------------------------------\n")

    async def get_plant_list(self, page: int = 1, size: int = 100):
        url = f"{self.base_url}/openapi/getPowerStationList"
        payload = {**self.base_payload, "curPage": page, "size": size}
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload, headers=self.headers)
                if response.status_code != 200:
                    return {"result_code": str(response.status_code), "result_msg": f"Erro HTTP Sungrow: {response.text}"}
                return response.json()
        except Exception as e:
            return {"result_code": "999", "result_msg": f"Erro Local Sungrow: {str(e)}"}

    async def get_fault_alarm_info(self, page: int = 1, size: int = 100, ps_id: int = None):
        url = f"{self.base_url}/openapi/getFaultAlarmInfo"
        payload = {**self.base_payload, "curPage": str(page), "size": str(size), "process_status": "999"}
        if ps_id:
            payload["ps_id"] = str(ps_id)
            
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload, headers=self.headers)
                if response.status_code != 200:
                    return {"result_code": str(response.status_code), "result_msg": f"Erro HTTP Sungrow: {response.text}"}
                return response.json()
        except Exception as e:
            return {"result_code": "999", "result_msg": f"Erro Local Sungrow: {str(e)}"}

    async def get_device_list(self, ps_id: int, page: int = 1, size: int = 50):
        url = f"{self.base_url}/openapi/getDeviceList"
        payload = {**self.base_payload, "ps_id": str(ps_id), "curPage": page, "size": size}
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload, headers=self.headers)
                if response.status_code != 200:
                    return {"result_code": str(response.status_code), "result_msg": f"Erro HTTP Sungrow: {response.text}"}
                return response.json()
        except Exception as e:
            return {"result_code": "999", "result_msg": f"Erro Local Sungrow: {str(e)}"}
    
    # NOVO MÉTODOS DE LOGIN
    async def login(self, user_account: str, user_password: str):
        url = f"{self.base_url}/openapi/login"
        
        # A documentação pede user_account e user_password. 
        # Juntamos com o base_payload para garantir o appkey e idioma
        payload = {
            **self.base_payload,
            "user_account": user_account,
            "user_password": user_password
        }
        
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(url, json=payload, headers=self.headers)
                
                if response.status_code != 200:
                    return {"result_code": str(response.status_code), "result_msg": f"Erro HTTP: {response.text}"}
                
                return response.json()
        except Exception as e:
            return {"result_code": "999", "result_msg": f"Erro Local: {str(e)}"}