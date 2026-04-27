from enum import Enum
from uuid import UUID, uuid4
from datetime import datetime, date
from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship

# --- ENUMS ---
class TipoPerfil(str, Enum):
    ALUNO = "ALUNO"
    ADMINISTRADOR = "ADMINISTRADOR"
    SEGURANCA = "SEGURANCA"

class StatusOcorrencia(str, Enum):
    ABERTO = "ABERTO"
    EM_ATENDIMENTO = "EM_ATENDIMENTO"
    RESOLVIDO = "RESOLVIDO"

class TipoMidia(str, Enum):
    FOTO = "Foto"
    VIDEO = "Vídeo"
    AUDIO = "Áudio"

# --- MODELOS ---

class Usuario(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    # --- CAMPOS PARA O CADASTRO RÁPIDO ---
    nome: str
    data_nascimento: Optional[date] = None 
    
    
    # --- CAMPOS PARA O CADASTRO completo ---
    email: Optional[str] = Field(default=None, unique=True, index=True)
    senha_hash: Optional[str] = None
    
    tipo_perfil: TipoPerfil = Field(default=TipoPerfil.ALUNO)
    
    genero: Optional[str] = None
    cpf: Optional[str] = Field(default=None, unique=True, index=True)
    # Se o cadastro for completo ou não (para permitir que o usuário finalize depois, se quiser)
    cadastro_completo: bool = Field(default=False)

    # Relacionamentos
    ocorrencias_registradas: List["Ocorrencia"] = Relationship(
        back_populates="autor", sa_relationship_kwargs={"foreign_keys": "Ocorrencia.usuario_id"}
    )
    ocorrencias_atendidas: List["Ocorrencia"] = Relationship(
        back_populates="responsavel", sa_relationship_kwargs={"foreign_keys": "Ocorrencia.responsavel_id"}
    )

class Ocorrencia(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    
    # FK para Usuario (Opcional para garantir anonimato)
    usuario_id: Optional[UUID] = Field(default=None, foreign_key="usuario.id")

    descricao_resumida: str
    horario_ocorrencia: datetime
    
    tipo_incidente: str
    descricao: str
    localizacao: str # Coordenadas ou ponto do campus
    status: StatusOcorrencia = Field(default=StatusOcorrencia.ABERTO)
    data_criacao: datetime = Field(default_factory=datetime.utcnow)
    
    # FK para o perfil de Segurança responsável pelo atendimento
    responsavel_id: Optional[UUID] = Field(default=None, foreign_key="usuario.id")

    # Relacionamentos
    autor: Optional[Usuario] = Relationship(
        back_populates="ocorrencias_registradas", sa_relationship_kwargs={"foreign_keys": "[Ocorrencia.usuario_id]"}
    )
    responsavel: Optional[Usuario] = Relationship(
        back_populates="ocorrencias_atendidas", sa_relationship_kwargs={"foreign_keys": "[Ocorrencia.responsavel_id]"}
    )
    atualizacoes: List["AtualizacaoOcorrencia"] = Relationship(back_populates="ocorrencia")
    evidencias: List["Evidencia"] = Relationship(back_populates="ocorrencia")

class AtualizacaoOcorrencia(SQLModel, table=True):
    __tablename__ = "atualizacao_ocorrencia"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    ocorrencia_id: UUID = Field(foreign_key="ocorrencia.id")
    autor_id: UUID = Field(foreign_key="usuario.id")
    mensagem_acao: str
    data_atualizado: datetime = Field(default_factory=datetime.utcnow)

    # Relacionamento
    ocorrencia: Ocorrencia = Relationship(back_populates="atualizacoes")

class Evidencia(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    ocorrencia_id: UUID = Field(foreign_key="ocorrencia.id")
    caminho_salvo: str
    tipo_midia: TipoMidia

    # Relacionamento
    ocorrencia: Ocorrencia = Relationship(back_populates="evidencias")