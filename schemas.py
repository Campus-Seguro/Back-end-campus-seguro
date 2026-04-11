from uuid import UUID
from typing import Optional
from pydantic import BaseModel
from models import StatusOcorrencia, TipoMidia, TipoPerfil

class Token(BaseModel):
    access_token: str
    token_type: str

class UsuarioCreate(BaseModel):
    nome: str
    email: str
    cpf: str
    senha: str 
    tipo_perfil: TipoPerfil

class UsuarioResponse(BaseModel):
    id: UUID
    nome: str
    email: str
    tipo_perfil: TipoPerfil

class OcorrenciaCreate(BaseModel):
    anonimo: bool = False 
    tipo_incidente: str = "Emergência Geral"
    descricao: str = "Acionamento rápido via botão de emergência."
    localizacao: str

class OcorrenciaUpdate(BaseModel):
    status: Optional[StatusOcorrencia] = None
    responsavel_id: Optional[UUID] = None

class EvidenciaCreate(BaseModel):
    url_anexo: str  
    tipo_midia: TipoMidia

class AtualizacaoCreate(BaseModel):
    mensagem_acao: str