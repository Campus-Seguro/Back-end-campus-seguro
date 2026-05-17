from datetime import date, datetime
import re
from uuid import UUID
from typing import Optional, List
from pydantic import BaseModel, EmailStr, field_validator
from models import StatusOcorrencia, TipoMidia, TipoPerfil

# --- AUTENTICAÇÃO ---
class Token(BaseModel):
    access_token: str
    token_type: str

# --- USUÁRIOS ---
class UsuarioCreate(BaseModel):
    nome: str
    data_nascimento: Optional[date] = None 
    email: Optional[EmailStr] = None 
    cpf: Optional[str] = None
    senha: Optional[str] = None
    tipo_perfil: Optional[TipoPerfil] = TipoPerfil.ALUNO
    genero: Optional[str] = None

    @field_validator('senha')
    @classmethod
    def validar_forca_senha(cls, senha_digitada: Optional[str]) -> Optional[str]:
        if senha_digitada is None:
            return senha_digitada

        if len(senha_digitada) < 8:
            raise ValueError("A senha deve ter no mínimo 8 caracteres.")
        if not re.search(r"[A-Z]", senha_digitada):
            raise ValueError("A senha deve conter pelo menos uma letra maiúscula.")
        if not re.search(r"[0-9]", senha_digitada):
            raise ValueError("A senha deve conter pelo menos um número.")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", senha_digitada):
            raise ValueError("A senha deve conter pelo menos um caractere especial (ex: @, #, $).")

        return senha_digitada

class UsuarioResponse(BaseModel):
    id: UUID
    nome: str
    data_nascimento: Optional[date] = None 
    email: Optional[str] = None            
    cpf: Optional[str] = None              
    tipo_perfil: TipoPerfil
    cadastro_completo: bool
    
    class Config:
        from_attributes = True

# --- REQUISÇÃO DA IA (FRONT-END -> BACK-END) ---
class RelatoRequest(BaseModel):
    descricao: str

# --- OCORRÊNCIAS ---
class OcorrenciaCreate(BaseModel):
    tipo_incidente: str = "Emergência Geral"
    descricao: str = "Acionamento rápido via botão de emergência."
    localizacao: str
    anonimo: bool = False
    
    # 🌟 ESSES CAMPOS AGORA SÃO ENVIADOS PELA IA APÓS O PROCESSAMENTO 🌟
    descricao_resumida: Optional[str] = "Acionamento rápido"
    horario_ocorrencia: Optional[datetime] = None

class OcorrenciaUpdate(BaseModel):
    status: Optional[StatusOcorrencia] = None
    responsavel_id: Optional[UUID] = None

# --- EVIDÊNCIAS ---
class EvidenciaCreate(BaseModel):
    # Sincronizado: o model chama 'caminho_salvo', o schema precisa refletir isso
    caminho_salvo: str  
    tipo_midia: TipoMidia

# --- ATUALIZAÇÕES ---
class AtualizacaoCreate(BaseModel):
    mensagem_acao: str
    # Adicionado para que a rota receba quem está atualizando o status do chamado
    autor_id: UUID