import asyncio
import random
from datetime import datetime, timedelta, timezone
from app.core.database import SessionLocal
from app.modulos.clientes.models import Cliente, ContaReceber

# Dados fictícios para gerar variedade
NOMES = [
    "Solar Sul Engenharia", "TechNova Energia", "João Carlos Silva", 
    "Maria Antonieta Guedes", "Condomínio Flores do Campo", "Supermercado Bairro",
    "Agropecuária Boi Gordo", "Padaria Pão de Ouro", "Lucas Fernandes",
    "Carla Ribeiro Arquitetura", "Posto Estrela do Sul", "Farmácia Saúde Mais",
    "Escola Caminho do Saber", "Roberto Almeida", "Clínica Sorriso",
    "Indústria MetalTech", "Restaurante Sabor de Casa", "Pedro Henrique Santos",
    "Academia Body Fit", "Auto Center Roda Viva"
]
CIDADES = ["Campo Grande", "Dourados", "Três Lagoas", "São Paulo", "Curitiba"]
ESTADOS = ["MS", "MS", "MS", "SP", "PR"]
STATUS_OPCOES = ["pago", "pendente", "atrasado"]

async def popular_banco():
    async with SessionLocal() as db:
        print("🌱 Iniciando o plantio de dados (Seed)...")
        
        hoje = datetime.now(timezone.utc)
        clientes_criados = 0
        faturas_criadas = 0

        for i in range(20):
            nome = NOMES[i]
            is_cnpj = i % 3 == 0 # 1 a cada 3 será CNPJ
            
            # Gera Cliente
            novo_cliente = Cliente(
                nome=nome,
                tipo_documento="CNPJ" if is_cnpj else "CPF",
                documento=f"{random.randint(100, 999)}.{random.randint(100, 999)}.{random.randint(100, 999)}-{random.randint(10, 99)}",
                email=f"contato{i}@emailficticio.com",
                telefone=f"(67) 9{random.randint(1000, 9999)}-{random.randint(1000, 9999)}",
                cidade=random.choice(CIDADES),
                estado=random.choice(ESTADOS),
                status=random.choice([True, True, True, False]) # Maioria ativo
            )
            
            db.add(novo_cliente)
            await db.flush() # Para pegar o ID gerado
            clientes_criados += 1

            # Gera Contas a Receber (Faturas) para 80% dos clientes
            if random.random() < 0.8:
                qtd_parcelas = random.choice([6, 12, 24, 36])
                valor_parcela = round(random.uniform(150.0, 1200.0), 2)
                
                # Simula que o contrato começou alguns meses atrás (para ter faturas pagas e atrasadas)
                meses_atras = random.randint(1, 5)
                data_inicio = hoje - timedelta(days=(30 * meses_atras))
                
                for p in range(qtd_parcelas):
                    data_venc = data_inicio + timedelta(days=(30 * p))
                    
                    # Define o status inteligentemente com base na data
                    if data_venc < hoje:
                        # Se já venceu, 80% de chance de estar pago e 20% de estar atrasado
                        status_fatura = "pago" if random.random() < 0.8 else "atrasado"
                    else:
                        # Se vai vencer no futuro, fica pendente
                        status_fatura = "pendente"

                    nova_fatura = ContaReceber(
                        cliente_id=novo_cliente.id,
                        descricao="Mensalidade O&M - Monitoramento",
                        valor=valor_parcela,
                        data_vencimento=data_venc,
                        status=status_fatura,
                        parcela=f"{p+1}/{qtd_parcelas}"
                    )
                    db.add(nova_fatura)
                    faturas_criadas += 1

        await db.commit()
        print(f"✅ Sucesso! {clientes_criados} clientes e {faturas_criadas} faturas geradas.")

if __name__ == "__main__":
    # Roda a função assíncrona
    asyncio.run(popular_banco())