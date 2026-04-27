from datetime import date
import re
from uuid import UUID
from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator
from models import StatusOcorrencia, TipoMidia, TipoPerfil

class Token(BaseModel):
    access_token: str
    token_type: str

class UsuarioCreate(BaseModel):
    nome: str
    data_nascimento: Optional[date] = None 
    
    # O Pydantic agora vai garantir automaticamente que isso tenha formato de e-mail (ex: teste@teste.com)
    email: Optional[EmailStr] = None 
    
    cpf: Optional[str] = None
    senha: Optional[str] = None
    tipo_perfil: Optional[TipoPerfil] = TipoPerfil.ALUNO
    genero: Optional[str] = None

    # --- VALIDADOR CUSTOMIZADO DE SENHA ---
    @field_validator('senha')
    @classmethod
    def validar_forca_senha(cls, senha_digitada: Optional[str]) -> Optional[str]:
        # Se for cadastro rápido (senha é None), deixa passar
        if senha_digitada is None:
            return senha_digitada

        # Regras de segurança da senha
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
        from_attributes = True # Necessário para o Pydantic ler os dados do SQLModel

class OcorrenciaCreate(BaseModel):
    anonimo: bool = False 
    tipo_incidente: str = "Emergência Geral"
    descricao: str = "Acionamento rápido via botão de emergência."
    localizacao: str

class RelatoRequest(BaseModel):
    descricao: str

class OcorrenciaUpdate(BaseModel):
    status: Optional[StatusOcorrencia] = None
    responsavel_id: Optional[UUID] = None

class EvidenciaCreate(BaseModel):
    url_anexo: str  
    tipo_midia: TipoMidia

class AtualizacaoCreate(BaseModel):
    mensagem_acao: str