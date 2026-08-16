from app.core.database import engine, Base

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request

# IMPORTAÇÃO NOVA: Carrega as tabelas na memória do SQLAlchemy
from app.modulos.clientes.models import Cliente
from app.modulos.empresas.models import Empresa 
from app.modulos.apis.growatt.models import GrowattConfig
from app.modulos.apis.saj.models import SajConfig # <--- NOVO: Model da SAJ

from app.modulos.apis.growatt.router import router as growatt_router
from app.modulos.apis.sungrow.router import router as sungrow_router
from app.modulos.apis.solis.router import router as solis_router
from app.modulos.apis.saj.router import router as saj_router # <--- NOVO: Router da SAJ
from app.modulos.apis.deye.router import router as deye_router


from app.modulos.clientes.router import router as clientes_router


app = FastAPI(title="AppSolar Monitor")


# === ADICIONE ESTE BLOCO AQUI ===
@app.on_event("startup")
async def startup_event():
    # Isso vai ler todos os models importados e criar as tabelas que não existem
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
# ===============================

# Montando arquivos estáticos (CSS, JS)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Monta os arquivos estáticos exclusivos do módulo de clientes
app.mount("/static_clientes", StaticFiles(directory="app/modulos/clientes/static"), name="static_clientes")

# Configurando templates HTML
templates = Jinja2Templates(directory="app/templates")

# Incluindo as rotas das APIs
app.include_router(clientes_router)
app.include_router(growatt_router)
app.include_router(sungrow_router) 
app.include_router(solis_router)
app.include_router(saj_router) # <--- NOVO: Incluindo rotas da SAJ no FastAPI
app.include_router(deye_router)

# Modifique a rota principal para apontar para o index.html
# Rota principal renderizando o dashboard diretamente
@app.get("/")
async def serve_dashboard_plantas(request: Request):
    return templates.TemplateResponse(
        request=request, 
        name="dashboard.html", 
        context={"request": request}
    )

# Se quiser manter a rota /dashboard ativa também servindo a mesma página
@app.get("/dashboard")
async def serve_dashboard_alias(request: Request):
    return templates.TemplateResponse(
        request=request, 
        name="dashboard.html", 
        context={"request": request}
    )

# NOVA ROTA: Página de Detalhes da Usina com a Marca dinâmica
@app.get("/dashboard/plantas/{marca}/{plant_id}")
async def serve_detalhes_planta(request: Request, marca: str, plant_id: int):
    # Passamos o plant_id e a marca para o HTML, assim o JS sabe onde buscar
    return templates.TemplateResponse(
        request=request, 
        name="detalhes.html", 
        context={
            "request": request, 
            "plant_id": plant_id,
            "marca": marca.lower() # Garante que seja 'growatt', 'sungrow', 'solis' ou 'saj' minúsculo
        }
    )

# NOVA ROTA: Página de Configurações
@app.get("/dashboard/configuracoes")
async def serve_configuracoes(request: Request):
    return templates.TemplateResponse(
        request=request, 
        name="config.html", 
        context={"request": request}
    )