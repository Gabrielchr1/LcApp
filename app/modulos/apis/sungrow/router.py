# app/modulos/apis/sungrow/router.py

import traceback
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db

from app.modulos.empresas.models import Empresa
from app.modulos.apis.sungrow.models import SungrowConfig
from app.modulos.apis.sungrow.client import SungrowClient
from .service import (
    obter_dispositivos_sungrow_com_cache, 
    obter_falhas_sungrow_com_cache, 
    obter_plantas_sungrow_com_cache
)

router = APIRouter(prefix="/api/sungrow", tags=["Sungrow"])

class SungrowLoginRequest(BaseModel):
    user_account: str
    user_password: str
    app_key: str
    secret_key: str

# ==========================================
# FUNÇÃO DE RENOVAÇÃO SILENCIOSA DE TOKEN
# ==========================================
async def renovar_token_silenciosamente(db: AsyncSession, config: SungrowConfig) -> str:
    """Faz login nos bastidores usando as credenciais do banco para renovar o token."""
    try:
        client = SungrowClient(api_token="", app_key=config.app_key, secret_key=config.secret_key)
        result = await client.login(config.user_account, config.user_password)
        
        if str(result.get("result_code")) == "1":
            result_data = result.get("result_data", {})
            if str(result_data.get("login_state")) == "1":
                novo_token = result_data.get("token")
                
                # Salva o novo token no banco de dados para as próximas requisições
                config.token = novo_token
                await db.commit()
                
                print("🔄 [Sungrow] Token expirado. Novo token gerado e salvo com sucesso!")
                return novo_token
    except Exception as e:
        print(f"❌ [Sungrow] Falha na tentativa de renovação silenciosa: {str(e)}")
        
    return None

# ==========================================
# ROTAS DA APLICAÇÃO
# ==========================================

@router.get("/plants")
async def list_plants(page: int = 1, db: AsyncSession = Depends(get_db)):
    try:
        empresa_id_teste = 1
        
        stmt = select(SungrowConfig).where(SungrowConfig.empresa_id == empresa_id_teste)
        resultado = await db.execute(stmt)
        config = resultado.scalars().first()
        
        if not config or not config.token or not config.app_key:
            raise HTTPException(status_code=400, detail="Integração com a Sungrow não configurada. Por favor, acesse as configurações e realize o login.")
            
        # PRIMEIRA TENTATIVA
        dados_normalizados = await obter_plantas_sungrow_com_cache(
            db, empresa_id=empresa_id_teste, api_token=config.token, 
            app_key=config.app_key, secret_key=config.secret_key, page=page
        )
        
        # SE DEU ERRO (Possível Token Expirado)
        if not dados_normalizados.get("plants") and dados_normalizados.get("error_msg"):
             
             # Tenta renovar o token silenciosamente
             novo_token = await renovar_token_silenciosamente(db, config)
             
             if novo_token:
                 # SEGUNDA TENTATIVA com o Token Novo
                 dados_normalizados = await obter_plantas_sungrow_com_cache(
                     db, empresa_id=empresa_id_teste, api_token=novo_token, 
                     app_key=config.app_key, secret_key=config.secret_key, page=page
                 )
             
             # Se ainda assim falhar, lança o erro para o Front
             if not dados_normalizados.get("plants") and dados_normalizados.get("error_msg"):
                 raise HTTPException(status_code=400, detail=dados_normalizados.get("error_msg"))
            
        return dados_normalizados
        
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro Interno: {str(e)}")
    

@router.get("/faults")
async def list_faults(page: int = 1, ps_id: int = None, db: AsyncSession = Depends(get_db)):
    try:
        empresa_id_teste = 1
        
        stmt = select(SungrowConfig).where(SungrowConfig.empresa_id == empresa_id_teste)
        resultado = await db.execute(stmt)
        config = resultado.scalars().first()
        
        if not config or not config.token or not config.app_key:
            raise HTTPException(status_code=400, detail="Integração com a Sungrow não configurada.")
        
        # PRIMEIRA TENTATIVA
        dados_normalizados = await obter_falhas_sungrow_com_cache(
            db, empresa_id=empresa_id_teste, api_token=config.token, 
            app_key=config.app_key, secret_key=config.secret_key, page=page, ps_id=ps_id
        )
        
        # SE DEU ERRO (Possível Token Expirado)
        if not dados_normalizados.get("faults") and dados_normalizados.get("error_msg"):
             novo_token = await renovar_token_silenciosamente(db, config)
             if novo_token:
                 # SEGUNDA TENTATIVA com o Token Novo
                 dados_normalizados = await obter_falhas_sungrow_com_cache(
                     db, empresa_id=empresa_id_teste, api_token=novo_token, 
                     app_key=config.app_key, secret_key=config.secret_key, page=page, ps_id=ps_id
                 )
             
             if not dados_normalizados.get("faults") and dados_normalizados.get("error_msg"):
                 raise HTTPException(status_code=400, detail=dados_normalizados.get("error_msg"))
            
        return dados_normalizados
        
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro Interno: {str(e)}")
    

@router.get("/dataloggers/{ps_id}")
async def list_dataloggers(ps_id: int, page: int = 1, db: AsyncSession = Depends(get_db)):
    try:
        empresa_id_teste = 1
        
        stmt = select(SungrowConfig).where(SungrowConfig.empresa_id == empresa_id_teste)
        resultado = await db.execute(stmt)
        config = resultado.scalars().first()
        
        if not config or not config.token or not config.app_key:
            raise HTTPException(status_code=400, detail="Integração com a Sungrow não configurada.")
        
        # PRIMEIRA TENTATIVA
        dados_normalizados = await obter_dispositivos_sungrow_com_cache(
            db, empresa_id=empresa_id_teste, api_token=config.token, 
            app_key=config.app_key, secret_key=config.secret_key, ps_id=ps_id, page=page
        )
        
        # SE DEU ERRO (Possível Token Expirado)
        if not dados_normalizados.get("dataloggers") and dados_normalizados.get("error_msg"):
             novo_token = await renovar_token_silenciosamente(db, config)
             if novo_token:
                 # SEGUNDA TENTATIVA com o Token Novo
                 dados_normalizados = await obter_dispositivos_sungrow_com_cache(
                     db, empresa_id=empresa_id_teste, api_token=novo_token, 
                     app_key=config.app_key, secret_key=config.secret_key, ps_id=ps_id, page=page
                 )
                 
             if not dados_normalizados.get("dataloggers") and dados_normalizados.get("error_msg"):
                 raise HTTPException(status_code=400, detail=dados_normalizados.get("error_msg"))
            
        return dados_normalizados
        
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro Interno: {str(e)}")
    

@router.post("/login")
async def authenticate_sungrow(data: SungrowLoginRequest, db: AsyncSession = Depends(get_db)):
    """Realiza o login na iSolarCloud e salva as credenciais no banco de dados. (Ação Manual)"""
    try:
        empresa_id_teste = 1 
        
        client = SungrowClient(api_token="", app_key=data.app_key, secret_key=data.secret_key)
        result = await client.login(data.user_account, data.user_password)
        
        if str(result.get("result_code")) == "1":
            result_data = result.get("result_data", {})
            login_state = str(result_data.get("login_state"))
            
            if login_state == "1":
                token = result_data.get("token")
                
                stmt = select(SungrowConfig).where(SungrowConfig.empresa_id == empresa_id_teste)
                resultado = await db.execute(stmt)
                config = resultado.scalars().first()
                
                if config:
                    config.app_key = data.app_key
                    config.secret_key = data.secret_key
                    config.user_account = data.user_account
                    config.user_password = data.user_password
                    config.token = token
                else:
                    nova_config = SungrowConfig(
                        empresa_id=empresa_id_teste, app_key=data.app_key, secret_key=data.secret_key,
                        user_account=data.user_account, user_password=data.user_password, token=token
                    )
                    db.add(nova_config)
                    
                await db.commit()
                
                return {"success": True, "token": token, "message": "Login realizado e credenciais salvas com sucesso!"}
            else:
                mensagens_erro = {
                    "-1": "A conta não existe.", "0": "A senha está incorreta.",
                    "2": "Conta bloqueada devido a senha incorreta.", "5": "Conta bloqueada pelo administrador."
                }
                msg = mensagens_erro.get(login_state, "Falha na autenticação.")
                return {"success": False, "message": msg}
        else:
            return {"success": False, "message": result.get("result_msg", "Erro na iSolarCloud.")}
            
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro Interno: {str(e)}")