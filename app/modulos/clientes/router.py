from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi.templating import Jinja2Templates
from datetime import timedelta, datetime, timezone

from app.core.database import get_db
from .models import Cliente, Plano, ContaReceber
from .schemas import ClienteCreate, ClienteResponse, PlanoCreate, PlanoResponse, ClienteUpdate

templates = Jinja2Templates(directory=["app/templates", "app/modulos/clientes/templates"])

router = APIRouter(prefix="/clientes", tags=["Clientes"])

@router.get("/")
async def pagina_clientes(request: Request):
    return templates.TemplateResponse(request=request, name="clientes.html", context={"request": request})

# ==========================================
# ROTAS DE PLANOS
# ==========================================
@router.post("/api/planos/criar")
async def criar_plano(plano: PlanoCreate, db: AsyncSession = Depends(get_db)):
    novo_plano = Plano(**plano.model_dump())
    db.add(novo_plano)
    await db.commit()
    return {"success": True, "message": "Plano criado com sucesso!"}

@router.get("/api/planos/lista")
async def listar_planos(db: AsyncSession = Depends(get_db)):
    resultado = await db.execute(select(Plano).where(Plano.status == True))
    return resultado.scalars().all()



# ==========================================
# ROTAS DE CLIENTES E FINANCEIRO
# ==========================================
@router.get("/api/lista")
async def listar_clientes(db: AsyncSession = Depends(get_db)):
    """Retorna os clientes com indicadores financeiros e KPIs Globais."""
    try:
        res_cli = await db.execute(select(Cliente).order_by(Cliente.id.desc()))
        clientes = res_cli.scalars().all()

        res_contas = await db.execute(select(ContaReceber))
        contas = res_contas.scalars().all()

        hoje = datetime.now().date()
        
        lista_final = []
        kpi_ativos = 0
        kpi_valor_receber = 0.0
        kpi_atrasados = 0
        kpi_valor_atrasado = 0.0 # NOVO INDICADOR

        for cli in clientes:
            if cli.status: 
                kpi_ativos += 1

            contas_cli = [c for c in contas if c.cliente_id == cli.id]
            valor_cli = 0.0
            tem_atraso = False

            for c in contas_cli:
                # Soma tudo que está em aberto no total a receber
                if c.status != "pago":
                    valor_cli += c.valor
                    kpi_valor_receber += c.valor

                data_venc = c.data_vencimento.date() if c.data_vencimento else None

                # Verifica se é uma conta atrasada
                conta_esta_atrasada = c.status == "atrasado" or (c.status == "pendente" and data_venc and data_venc < hoje)
                
                if conta_esta_atrasada:
                    tem_atraso = True
                    kpi_valor_atrasado += c.valor # SOMA O VALOR DESTA CONTA NO INDICADOR DE ATRASO
            
            if tem_atraso:
                kpi_atrasados += 1

            lista_final.append({
                "id": cli.id,
                "nome": cli.nome,
                "email": cli.email,
                "telefone": cli.telefone,
                "cidade": cli.cidade,
                "estado": cli.estado,
                "status": cli.status,
                "valor_total": valor_cli,
                "tem_atraso": tem_atraso
            })

        return {
            "kpis": {
                "ativos": kpi_ativos,
                "valor_receber": kpi_valor_receber,
                "atrasados": kpi_atrasados,
                "valor_atrasado": kpi_valor_atrasado # ENVIANDO PARA O FRONTEND
            },
            "clientes": lista_final
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))





@router.post("/api/criar")
async def criar_cliente(dados: ClienteCreate, db: AsyncSession = Depends(get_db)):
    # 1. Verifica se CPF/CNPJ já existe
    if dados.documento:
        stmt = select(Cliente).where(Cliente.documento == dados.documento)
        resultado = await db.execute(stmt)
        if resultado.scalars().first():
            raise HTTPException(status_code=400, detail="Este CPF/CNPJ já está cadastrado.")

    # 2. Separa os dados do Cliente dos dados Financeiros
    cliente_dict = dados.model_dump(exclude={"gerar_cobranca", "valor_cobranca", "qtd_parcelas", "data_primeiro_vencimento"})
    novo_cliente = Cliente(**cliente_dict)
    
    try:
        db.add(novo_cliente)
        await db.flush() # Salva no banco mas não "commita" ainda, para pegarmos o ID do cliente gerado
        
        # 3. Lógica do Contas a Receber
        if dados.gerar_cobranca and dados.data_primeiro_vencimento and dados.valor_cobranca > 0:
            for i in range(dados.qtd_parcelas):
                # Adiciona aproximadamente 30 dias para cada parcela subsequente
                data_venc = dados.data_primeiro_vencimento + timedelta(days=(30 * i))
                
                nova_cobranca = ContaReceber(
                    cliente_id=novo_cliente.id,
                    descricao=f"Mensalidade/Serviço - Ref. Contrato",
                    valor=dados.valor_cobranca,
                    data_vencimento=data_venc,
                    parcela=f"{i+1}/{dados.qtd_parcelas}"
                )
                db.add(nova_cobranca)

        await db.commit()
        return {"success": True, "message": "Cliente cadastrado e financeiro gerado com sucesso!"}
    
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@router.get("/api/{cliente_id}")
async def obter_cliente(cliente_id: int, db: AsyncSession = Depends(get_db)):
    """Busca os dados de um cliente específico para o Modal de Edição."""
    resultado = await db.execute(select(Cliente).where(Cliente.id == cliente_id))
    cliente = resultado.scalars().first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado.")
    return cliente

@router.put("/api/atualizar/{cliente_id}")
async def atualizar_cliente(cliente_id: int, dados: ClienteUpdate, db: AsyncSession = Depends(get_db)):
    """Atualiza os dados de um cliente existente."""
    resultado = await db.execute(select(Cliente).where(Cliente.id == cliente_id))
    cliente = resultado.scalars().first()
    
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado.")

    # Se estiver alterando o documento, verifica se já não existe outro igual
    if dados.documento and dados.documento != cliente.documento:
        busca = await db.execute(select(Cliente).where(Cliente.documento == dados.documento))
        if busca.scalars().first():
            raise HTTPException(status_code=400, detail="Este CPF/CNPJ já pertence a outro cliente.")

    # Atualiza apenas os campos enviados
    dados_dict = dados.model_dump(exclude_unset=True)
    for key, value in dados_dict.items():
        setattr(cliente, key, value)

    try:
        await db.commit()
        return {"success": True, "message": "Cliente atualizado com sucesso!"}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/api/excluir/{cliente_id}")
async def excluir_cliente(cliente_id: int, db: AsyncSession = Depends(get_db)):
    """Exclui um cliente (e suas contas a receber em cascata)."""
    resultado = await db.execute(select(Cliente).where(Cliente.id == cliente_id))
    cliente = resultado.scalars().first()
    
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado.")
        
    try:
        await db.delete(cliente)
        await db.commit()
        return {"success": True, "message": "Cliente excluído com sucesso!"}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Erro ao excluir cliente. Verifique as dependências.")


# ==========================================
# ROTAS DE DETALHES E BAIXAS FINANCEIRAS
# ==========================================
@router.get("/api/{cliente_id}/faturas")
async def listar_faturas_cliente(cliente_id: int, db: AsyncSession = Depends(get_db)):
    """Retorna todas as faturas (contas a receber) de um cliente."""
    try:
        resultado = await db.execute(
            select(ContaReceber)
            .where(ContaReceber.cliente_id == cliente_id)
            .order_by(ContaReceber.data_vencimento.asc())
        )
        faturas = resultado.scalars().all()
        return faturas
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/api/faturas/{fatura_id}/pagar")
async def pagar_fatura(fatura_id: int, db: AsyncSession = Depends(get_db)):
    """Muda o status de uma fatura para 'pago'."""
    try:
        resultado = await db.execute(select(ContaReceber).where(ContaReceber.id == fatura_id))
        fatura = resultado.scalars().first()
        
        if not fatura:
            raise HTTPException(status_code=404, detail="Fatura não encontrada.")
        
        fatura.status = "pago"
        await db.commit()
        return {"success": True, "message": "Pagamento confirmado com sucesso!"}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))