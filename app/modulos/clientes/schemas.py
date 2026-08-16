from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# --- SCHEMAS DE PLANOS ---
class PlanoCreate(BaseModel):
    nome: str
    valor: float
    ciclo: str = "mensal"

class PlanoResponse(PlanoCreate):
    id: int
    class Config:
        from_attributes = True

# --- SCHEMAS DE CLIENTES ---
class ClienteBase(BaseModel):
    nome: str
    tipo_documento: str = "CPF"
    documento: Optional[str] = None
    email: Optional[str] = None
    telefone: Optional[str] = None
    
    # Endereço
    cep: Optional[str] = None
    logradouro: Optional[str] = None
    numero: Optional[str] = None
    complemento: Optional[str] = None
    bairro: Optional[str] = None
    cidade: Optional[str] = None
    estado: Optional[str] = None
    
    plano_id: Optional[int] = None
    status: Optional[bool] = True

class ClienteCreate(ClienteBase):
    # Campos extras que não vão para a tabela de cliente, 
    # mas servem para gerar o Contas a Receber no ato do cadastro
    gerar_cobranca: bool = False
    valor_cobranca: Optional[float] = 0.0
    qtd_parcelas: Optional[int] = 1
    data_primeiro_vencimento: Optional[datetime] = None

class ClienteResponse(ClienteBase):
    id: int
    criado_em: datetime
    class Config:
        from_attributes = True

class ClienteUpdate(BaseModel):
    nome: Optional[str] = None
    tipo_documento: Optional[str] = None
    documento: Optional[str] = None
    email: Optional[str] = None
    telefone: Optional[str] = None
    cep: Optional[str] = None
    logradouro: Optional[str] = None
    numero: Optional[str] = None
    complemento: Optional[str] = None
    bairro: Optional[str] = None
    cidade: Optional[str] = None
    estado: Optional[str] = None
    plano_id: Optional[int] = None
    status: Optional[bool] = None