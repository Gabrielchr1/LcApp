from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base

class Plano(Base):
    __tablename__ = "planos"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    valor = Column(Float, nullable=False)
    ciclo = Column(String, default="mensal") # mensal, anual, unico
    status = Column(Boolean, default=True)
    criado_em = Column(DateTime(timezone=True), server_default=func.now())

class Cliente(Base):
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, index=True, nullable=False)
    tipo_documento = Column(String, default="CPF") # NOVO: Para a animação CPF/CNPJ
    documento = Column(String, unique=True, index=True)
    email = Column(String, index=True)
    telefone = Column(String)
    
    # NOVOS CAMPOS DE ENDEREÇO
    cep = Column(String)
    logradouro = Column(String)
    numero = Column(String)
    complemento = Column(String)
    bairro = Column(String)
    cidade = Column(String)
    estado = Column(String)

    # VÍNCULO COM O PLANO CONTRATADO
    plano_id = Column(Integer, ForeignKey("planos.id", ondelete="SET NULL"), nullable=True)

    status = Column(Boolean, default=True)
    criado_em = Column(DateTime(timezone=True), server_default=func.now())

class ContaReceber(Base):
    __tablename__ = "contas_receber"

    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id", ondelete="CASCADE"), nullable=False)
    descricao = Column(String, nullable=False) # Ex: "Mensalidade Plano Pro"
    valor = Column(Float, nullable=False)
    data_vencimento = Column(DateTime(timezone=True), nullable=False)
    status = Column(String, default="pendente") # pendente, pago, atrasado
    parcela = Column(String) # Ex: "1/12" ou "Recorrente"
    criado_em = Column(DateTime(timezone=True), server_default=func.now())