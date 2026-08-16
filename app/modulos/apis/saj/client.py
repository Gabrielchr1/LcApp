# app/modulos/apis/saj/client.py
import httpx
import hashlib
from datetime import datetime, timezone, timedelta

class SajClient:
    def __init__(self, app_id: str, app_secret: str, api_url: str = "https://intl-developer.saj-electric.com/prod-api", access_token: str = None):
        self.app_id = app_id
        self.app_secret = app_secret
        self.base_url = api_url.rstrip('/')
        self.access_token = access_token
        
    def _generate_signature(self, params: dict) -> str:
        sig_params = params.copy()
        
        # Limpa os parâmetros vazios (A SAJ não assina valores nulos ou vazios)
        clean_params = {k: v for k, v in sig_params.items() if v is not None and str(v).strip() != ""}
        
        if 'appId' not in clean_params:
            clean_params['appId'] = self.app_id
            
        sorted_keys = sorted(clean_params.keys())
        concat_str = ",".join(f"{k}={str(clean_params[k])}" for k in sorted_keys)
        
        return hashlib.sha256(concat_str.encode('utf-8')).hexdigest().upper()

    def _get_headers(self, params: dict = None) -> dict:
        headers = {
            "content-language": "en_US"
        }
        if self.access_token and params is not None:
            headers["accessToken"] = self.access_token
            headers["clientSign"] = self._generate_signature(params)
        return headers

    async def get_access_token(self):
        url = f"{self.base_url}/open/api/access_token"
        params = {
            "appId": self.app_id,
            "appSecret": self.app_secret
        }
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(url, params=params, headers={"content-language": "en_US"})
                if response.status_code != 200:
                    return {"error_code": response.status_code, "error_msg": f"Erro HTTP Token SAJ: {response.text}"}
                
                data = response.json()
                
                # Aceita code 0 ou 200
                if data.get("code") in [0, 200, "0", "200"]:
                    self.access_token = data.get("data", {}).get("access_token")
                return data
        except Exception as e:
            return {"error_code": 999, "error_msg": f"Erro Conexão Local SAJ: {str(e)}"}


    async def get_plant_page(self, page_num: int = 1, page_size: int = 100):
        url = f"{self.base_url}/open/api/developer/plant/page"
        params = {
            "appId": self.app_id,
            "pageNum": str(page_num),
            "pageSize": str(page_size)
        }
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params, headers=self._get_headers(params))
                if response.status_code != 200:
                    return {"error_code": response.status_code, "error_msg": f"Erro HTTP Plantas SAJ: {response.text}"}
                return response.json()
        except Exception as e:
            return {"error_code": 999, "error_msg": f"Erro Conexão Local SAJ: {str(e)}"}

    async def get_device_page(self, page_num: int = 1, page_size: int = 100):
        url = f"{self.base_url}/open/api/developer/device/page"
        params = {
            "appId": self.app_id,
            "pageNum": str(page_num),
            "pageSize": str(page_size)
        }
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params, headers=self._get_headers(params))
                if response.status_code != 200:
                    return {"error_code": response.status_code, "error_msg": f"Erro HTTP Devices SAJ: {response.text}"}
                return response.json()
        except Exception as e:
            return {"error_code": 999, "error_msg": f"Erro Conexão Local SAJ: {str(e)}"}

    async def get_plant_all_device_list(self, plant_id: str):
        url = f"{self.base_url}/open/api/plant/getPlantAllDeviceList"
        params = {
            "appId": self.app_id,
            "plantId": str(plant_id),
            "userId": ""
        }
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params, headers=self._get_headers(params))
                if response.status_code != 200:
                    return {"error_code": response.status_code, "error_msg": f"Erro HTTP Device List SAJ: {response.text}"}
                return response.json()
        except Exception as e:
            return {"error_code": 999, "error_msg": f"Erro Conexão Local SAJ: {str(e)}"}

    async def get_device_baseinfo(self, device_sn: str):
        url = f"{self.base_url}/open/api/device/baseinfo"
        params = {
            "appId": self.app_id,
            "deviceSn": str(device_sn)
        }
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params, headers=self._get_headers(params))
                if response.status_code != 200:
                    return {"error_code": response.status_code, "error_msg": f"Erro HTTP Baseinfo SAJ: {response.text}"}
                return response.json()
        except Exception as e:
            return {"error_code": 999, "error_msg": f"Erro Conexão Local SAJ: {str(e)}"}

    async def get_plant_details(self, plant_id: str):
        url = f"{self.base_url}/open/api/plant/details"
        params = {
            "appId": self.app_id,
            "plantId": str(plant_id)
        }
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params, headers=self._get_headers(params))
                if response.status_code != 200:
                    return {"error_code": response.status_code, "error_msg": f"Erro HTTP Plant Details SAJ: {response.text}"}
                return response.json()
        except Exception as e:
            return {"error_code": 999, "error_msg": f"Erro Conexão Local SAJ: {str(e)}"}

    async def get_device_history_data(self, device_sn: str, start_time: str, end_time: str):
        """Nova função para buscar o Histórico do Inversor (Ger. Hoje e demais)"""
        url = f"{self.base_url}/open/api/device/historyDataCommon"
        params = {
            "appId": self.app_id,
            "deviceSn": str(device_sn),
            "startTime": str(start_time),
            "endTime": str(end_time)
        }
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params, headers=self._get_headers(params))
                if response.status_code != 200:
                    return {"error_code": response.status_code, "error_msg": f"Erro HTTP History SAJ: {response.text}"}
                return response.json()
        except Exception as e:
            return {"error_code": 999, "error_msg": f"Erro Conexão Local SAJ: {str(e)}"}