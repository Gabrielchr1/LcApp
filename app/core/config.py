import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PROJECT_NAME: str = "AppSolar Monitor"
    
    # Growatt
    GROWATT_API_URL: str = os.getenv("GROWATT_API_URL", "https://openapi.growatt.com/v1")
    GROWATT_TOKEN: str = os.getenv("GROWATT_TOKEN", "")
    
    # Sungrow
    SUNGROW_API_URL: str = os.getenv("SUNGROW_API_URL", "https://gateway.isolarcloud.com.hk")

settings = Settings()