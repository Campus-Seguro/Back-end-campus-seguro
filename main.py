from fastapi import FastAPI, Depends, HTTPException
from sqlmodel import Session, SQLModel, create_engine, select
from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID

# Importando os modelos que definimos
# (Certifique-se de que os modelos estão definidos em um arquivo models.py)
from models import Ocorrencia, StatusOcorrencia, Usuario, AtualizacaoOcorrencia, Evidencia

# --- 1. Configuração do banco de dados ---
sqlite_file_name = "campus_seguro.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

# echo=True faz o SQLAchemy imprimir as queries SQL no terminal, útil para debug
engine = create_engine(sqlite_url, echo=True)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

#Injeção de dependência para pegar a sessão do banco em cada requisição
def get_session():
    with Session(engine) as session:
        yield session

# --- 2. Inicialização do FastAPI ---
app = FastAPI(
    title = "API Campus Seguro",
    description = "Backend do MVP para o sistema de segurança do campus universitário",
    version = "0.1.0"
)

# Cria as tabelas assim que a API iniciar
@app.on_event("startup")
def on_startup():
    create_db_and_tables()

# --- 3. SCHEMAS(DTOs) de Entrada ---
# O schema define o que a API *espera* receber. É diferente do modelo do banco.
class OcorrenciaCreate(BaseModel):
    usuario_id: Optional[UUID] = None  # Pode ser denúncia anônima
    tipo_incidente: str = "Emergência Geral"
    descricao: str = "Acionamento rápido via botão de emergência."
    localizacao: str # Ex: "Bloco C, Andar 2" ou "Lat: -23.5505, Lon: -46.6333"

# --- 4. ROTAS (ENDOPOINTS) ---
@app.post("/ocorrencias/", response_model=Ocorrencia, status_code=201)
def acionar_botao_emergencia(
    ocorrencia_in: OcorrenciaCreate,  # <-- O nome da variável aqui
    session: Session = Depends(get_session)
):
    """
    Simula o acionamento do Botão de Emergência.
    Registra o incidente no banco com baixa latência.
    """
    # <-- Deve ser exatamente igual aos nomes usados aqui embaixo
    nova_ocorrencia = Ocorrencia(
        usuario_id=ocorrencia_in.usuario_id,
        tipo_incidente=ocorrencia_in.tipo_incidente,
        descricao=ocorrencia_in.descricao,
        localizacao=ocorrencia_in.localizacao,
        status=StatusOcorrencia.ABERTO
    )
    
    session.add(nova_ocorrencia)
    session.commit()
    session.refresh(nova_ocorrencia)
    
    return nova_ocorrencia 

@app.get("/ocorrencias/", response_model=List[Ocorrencia])
def listar_ocorrencias(session: Session = Depends(get_session)):
    """
    Retorna a lista de todas as ocorrências registradas para o painel de equipe de segurança.
    """
    ocorrencias = session.exec(select(Ocorrencia)).all()
    return ocorrencias

# --- # --- # --- # --- # --- # --- # --- # --- #

# Adicione este schema logo abaixo do OcorrenciaCreate (linha 43 mais ou menos)
class OcorrenciaUpdate(BaseModel):
    status: Optional[StatusOcorrencia] = None
    responsavel_id: Optional[UUID] = None

# Adicione esta rota no final do arquivo, logo após o listar_ocorrencias
@app.patch("/ocorrencias/{ocorrencia_id}", response_model=Ocorrencia)
def atualizar_status_ocorrencia(
    ocorrencia_id: UUID,
    ocorrencia_in: OcorrenciaUpdate,
    session: Session = Depends(get_session)
):
    """
    Atualiza uma ocorrência existente (Ex: Segurança assumindo o chamado).
    """
    # Busca a ocorrência no banco de dados pelo ID
    ocorrencia_db = session.get(Ocorrencia, ocorrencia_id)
    
    if not ocorrencia_db:
        raise HTTPException(status_code=404, detail="Ocorrência não encontrada")
    
    # Atualiza apenas os campos que foram enviados
    if ocorrencia_in.status is not None:
        ocorrencia_db.status = ocorrencia_in.status
    if ocorrencia_in.responsavel_id is not None:
        ocorrencia_db.responsavel_id = ocorrencia_in.responsavel_id
        
    session.add(ocorrencia_db)
    session.commit()
    session.refresh(ocorrencia_db)
    
    return ocorrencia_db