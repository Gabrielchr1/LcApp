from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request

# IMPORTAÇÃO NOVA: Carrega as tabelas na memória do SQLAlchemy
from app.modulos.empresas.models import Empresa 

from app.modulos.apis.growatt.router import router as growatt_router
from app.modulos.apis.sungrow.router import router as sungrow_router

app = FastAPI(title="AppSolar Monitor")

# Montando arquivos estáticos (CSS, JS)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Configurando templates HTML
templates = Jinja2Templates(directory="app/templates")

# Incluindo as rotas das APIs
app.include_router(growatt_router)
app.include_router(sungrow_router) # NOVO

@app.get("/")
async def serve_dashboard(request: Request):
    return templates.TemplateResponse(
        request=request, name="dashboard.html", context={"request": request}
    )

# NOVA ROTA: Página de Detalhes da Usina
@app.get("/dashboard/plantas/{plant_id}")
async def serve_detalhes_planta(request: Request, plant_id: int):
    # Passamos o plant_id para o HTML, assim o JS sabe de qual usina buscar os dados
    return templates.TemplateResponse(
        request=request, 
        name="detalhes.html", 
        context={"request": request, "plant_id": plant_id}
    )

# main.py

# ... [seus imports e rotas anteriores] ...

# NOVA ROTA: Página de Configurações
@app.get("/dashboard/configuracoes")
async def serve_configuracoes(request: Request):
    return templates.TemplateResponse(
        request=request, 
        name="config.html", 
        context={"request": request}
    )