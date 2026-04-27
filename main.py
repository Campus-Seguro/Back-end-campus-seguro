import jwt
import httpx
from uuid import UUID
from typing import List
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from sqlmodel import Session, SQLModel, create_engine, or_, select
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from models import Ocorrencia, StatusOcorrencia, Usuario, AtualizacaoOcorrencia, Evidencia, TipoPerfil, TipoMidia
from schemas import (Token, UsuarioCreate, UsuarioResponse, OcorrenciaCreate, OcorrenciaUpdate, EvidenciaCreate, AtualizacaoCreate)

from fastapi import File, UploadFile, Form
from bucket import deletar_arquivo_bucket, fazer_upload_arquivo

# --- 1. CONFIGURAÇÃO DO BANCO DE DADOS ---
sqlite_file_name = "campus_seguro.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

engine = create_engine(sqlite_url, echo=False)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

# --- 2. INICIALIZAÇÃO DO FASTAPI E SEGURANÇA ---
app = FastAPI(
    title = "API Campus Seguro",
    description = "Backend do MVP para o sistema de segurança do campus universitário",
    version = "1.0.0"
)

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Configurações do JWT
SECRET_KEY = "chave-super-secreta-campus-seguro-mvp"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 # 24 horas

# --- FUNÇÕES DE SEGURANÇA (JWT E RBAC) ---
def criar_token_acesso(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_usuario_atual(token: str = Depends(oauth2_scheme), session: Session = Depends(get_session)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Não foi possível validar as credenciais",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado. Faça login novamente.")
    except jwt.InvalidTokenError:
        raise credentials_exception
    
    usuario = session.exec(select(Usuario).where(Usuario.email == email)).first()
    if usuario is None:
        raise credentials_exception
    return usuario

def verificar_perfil_seguranca(usuario: Usuario = Depends(get_usuario_atual)):
    """Trava de RBAC: Garante que apenas Agentes de Segurança acessem a rota."""
    if usuario.tipo_perfil != TipoPerfil.SEGURANCA:
        raise HTTPException(
            status_code=403, 
            detail="Acesso negado. Esta ação requer perfil de Segurança."
        )
    return usuario


# --- INTEGRAÇÃO COM IA (OLLAMA) ---
async def processar_analise_ia(ocorrencia_id: UUID, descricao: str, tipo_incidente: str):
    """
    Roda em background: Envia os dados para o Ollama local e atualiza a ocorrência no banco.
    """
    # Prompt otimizado para o Phi-3: exigindo um formato rígido e sem enrolação
    prompt = (
        "Você é um sistema de IA de segurança universitária. "
        "Sua tarefa é analisar o relato abaixo, classificar o risco e sugerir uma ação. "
        "Seja direto, não use introduções ou saudações. "
        "Responda EXATAMENTE neste formato:\n"
        "RISCO: [Baixo, Médio ou Alto]\n"
        "AÇÃO: [Sua recomendação em apenas uma frase curta]\n\n"
        f"Tipo de Incidente: {tipo_incidente}\n"
        f"Relato da Vítima/Testemunha: {descricao}"
    )

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resposta = await client.post("http://localhost:11434/api/generate", json={
                "model": "phi3", # <-- Alterado para o Phi-3
                "prompt": prompt,
                "stream": False
            })
            resposta.raise_for_status()
            resultado_ia = resposta.json().get("response", "").strip()

        with Session(engine) as session:
            ocorrencia = session.get(Ocorrencia, ocorrencia_id)
            if ocorrencia:
                ocorrencia.analise_ia = resultado_ia
                session.add(ocorrencia)
                session.commit()

    except Exception as e:
        print(f"Erro ao processar IA (Phi-3) para ocorrência {ocorrencia_id}: {e}")


# --- Autenticação e Usuários ---

@app.post("/login", response_model=Token, tags=["Autenticação"])
def login_para_obter_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session)
):
    identificador = form_data.username 
    
    usuario = session.exec(
        select(Usuario).where(
            or_(
                Usuario.email == identificador,
                Usuario.cpf == identificador
            )
        )
    ).first()
    
    senha_hasheada = f"hash_falso_{form_data.password}"
    
    if not usuario or usuario.senha_hash != senha_hasheada:
        raise HTTPException(
            status_code=401, 
            detail="Email/CPF ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = criar_token_acesso(data={"sub": usuario.email})
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/usuarios/", response_model=UsuarioResponse, status_code=201, tags=["Usuários"])
def criar_usuario(usuario_in: UsuarioCreate, session: Session = Depends(get_session)):
    if usuario_in.email:
        usuario_existente = session.exec(select(Usuario).where(Usuario.email == usuario_in.email)).first()
        if usuario_existente:
            raise HTTPException(status_code=400, detail="Email já cadastrado.")

    if usuario_in.cpf:
        cpf_existente = session.exec(select(Usuario).where(Usuario.cpf == usuario_in.cpf)).first()
        if cpf_existente:
            raise HTTPException(status_code=400, detail="CPF já cadastrado.")

    flag_completo = bool(usuario_in.email and usuario_in.senha and usuario_in.cpf)
    senha_hasheada = f"hash_falso_{usuario_in.senha}" if usuario_in.senha else None

    novo_usuario = Usuario(
        nome=usuario_in.nome,
        data_nascimento=usuario_in.data_nascimento,
        email=usuario_in.email,
        genero=usuario_in.genero,
        cpf=usuario_in.cpf,
        senha_hash=senha_hasheada,
        tipo_perfil=usuario_in.tipo_perfil,
        cadastro_completo=flag_completo
    )
    
    session.add(novo_usuario)
    session.commit()
    session.refresh(novo_usuario)
    
    return novo_usuario


@app.get("/usuarios/", response_model=List[UsuarioResponse], tags=["Usuários"])
def listar_usuarios(session: Session = Depends(get_session), usuario_atual: Usuario = Depends(get_usuario_atual)):
    usuarios = session.exec(select(Usuario)).all()
    return usuarios


# --- Ocorrências (Jornada Principal) ---

@app.post("/ocorrencias/", response_model=Ocorrencia, status_code=201, tags=["Ocorrências"])
def acionar_botao_emergencia(
    ocorrencia_in: OcorrenciaCreate,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
    usuario_atual: Usuario = Depends(get_usuario_atual)
):
    """Aciona o Botão de Emergência e enfileira a análise da IA."""
    id_para_salvar = None if ocorrencia_in.anonimo else usuario_atual.id

    nova_ocorrencia = Ocorrencia(
        usuario_id=id_para_salvar,
        tipo_incidente=ocorrencia_in.tipo_incidente,
        descricao=ocorrencia_in.descricao,
        localizacao=ocorrencia_in.localizacao,
        status=StatusOcorrencia.ABERTO
    )
    session.add(nova_ocorrencia)
    session.commit()
    session.refresh(nova_ocorrencia)

    # Dispara a análise no Ollama sem bloquear a resposta do botão de emergência
    if nova_ocorrencia.descricao:
        background_tasks.add_task(
            processar_analise_ia, 
            nova_ocorrencia.id, 
            nova_ocorrencia.descricao,
            nova_ocorrencia.tipo_incidente
        )

    return nova_ocorrencia 


@app.get("/ocorrencias/", response_model=List[Ocorrencia], tags=["Ocorrências"])
def listar_ocorrencias(
    session: Session = Depends(get_session),
    usuario_atual: Usuario = Depends(get_usuario_atual) 
):
    if usuario_atual.tipo_perfil == TipoPerfil.SEGURANCA:
        ocorrencias = session.exec(select(Ocorrencia)).all()
    else:
        ocorrencias = session.exec(select(Ocorrencia).where(Ocorrencia.usuario_id == usuario_atual.id)).all()
    
    return ocorrencias


@app.get("/ocorrencias/{ocorrencia_id}", response_model=Ocorrencia, tags=["Ocorrências"])
def buscar_ocorrencia_por_id(
    ocorrencia_id: UUID, 
    session: Session = Depends(get_session),
    usuario_atual: Usuario = Depends(get_usuario_atual)
):
    ocorrencia = session.get(Ocorrencia, ocorrencia_id)
    if not ocorrencia:
        raise HTTPException(status_code=404, detail="Ocorrência não encontrada")
    
    if usuario_atual.tipo_perfil != TipoPerfil.SEGURANCA and ocorrencia.usuario_id != usuario_atual.id:
        raise HTTPException(status_code=403, detail="Acesso negado. Esta ocorrência pertence a outro usuário.")
        
    return ocorrencia


@app.patch("/ocorrencias/{ocorrencia_id}", response_model=Ocorrencia, tags=["Ocorrências"])
def atualizar_status_ocorrencia(
    ocorrencia_id: UUID,
    ocorrencia_in: OcorrenciaUpdate,
    session: Session = Depends(get_session),
    usuario_seguranca: Usuario = Depends(verificar_perfil_seguranca)
):
    ocorrencia_db = session.get(Ocorrencia, ocorrencia_id)
    if not ocorrencia_db:
        raise HTTPException(status_code=404, detail="Ocorrência não encontrada")
    
    if ocorrencia_in.status is not None:
        ocorrencia_db.status = ocorrencia_in.status
    
    if ocorrencia_in.responsavel_id is not None:
        ocorrencia_db.responsavel_id = ocorrencia_in.responsavel_id
    else:
        ocorrencia_db.responsavel_id = usuario_seguranca.id
        
    session.add(ocorrencia_db)
    session.commit()
    session.refresh(ocorrencia_db)
    return ocorrencia_db


@app.post("/ocorrencias/{ocorrencia_id}/evidencias", status_code=201, tags=["Detalhes Ocorrência"])
def adicionar_evidencia(
    ocorrencia_id: UUID,
    arquivo: UploadFile = File(...), 
    tipo_midia: TipoMidia = Form(...), 
    session: Session = Depends(get_session),
    usuario_atual: Usuario = Depends(get_usuario_atual) 
):
    ocorrencia = session.get(Ocorrencia, ocorrencia_id)
    if not ocorrencia:
        raise HTTPException(status_code=404, detail="Ocorrência não encontrada")
    
    if usuario_atual.tipo_perfil != TipoPerfil.SEGURANCA and ocorrencia.usuario_id != usuario_atual.id:
        raise HTTPException(status_code=403, detail="Acesso negado. Você só pode enviar evidências para as suas próprias ocorrências.")
    
    try:
        caminho_salvo = fazer_upload_arquivo(arquivo)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao salvar arquivo na nuvem: {str(e)}")

    try:
        nova_evidencia = Evidencia(
            ocorrencia_id=ocorrencia_id,
            caminho_salvo=caminho_salvo,
            tipo_midia=tipo_midia
        )
        
        session.add(nova_evidencia)
        session.commit()
        session.refresh(nova_evidencia)
        return nova_evidencia

    except Exception as db_error:
        session.rollback() 
        deletar_arquivo_bucket(caminho_salvo) 
        raise HTTPException(
            status_code=500, 
            detail=f"Erro ao salvar no banco. O arquivo foi removido do storage para manter a integridade. Erro: {str(db_error)}"
        )
    
@app.post("/ocorrencias/{ocorrencia_id}/atualizacoes", status_code=201, tags=["Detalhes Ocorrência"])
def adicionar_atualizacao_linha_do_tempo(
    ocorrencia_id: UUID,
    atualizacao_in: AtualizacaoCreate,
    session: Session = Depends(get_session),
    usuario_atual: Usuario = Depends(get_usuario_atual) 
):
    ocorrencia = session.get(Ocorrencia, ocorrencia_id)
    if not ocorrencia:
        raise HTTPException(status_code=404, detail="Ocorrência não encontrada")
        
    if usuario_atual.tipo_perfil != TipoPerfil.SEGURANCA and ocorrencia.usuario_id != usuario_atual.id:
        raise HTTPException(status_code=403, detail="Acesso negado. Você só pode interagir com as suas próprias ocorrências.")
        
    nova_atualizacao = AtualizacaoOcorrencia(
        ocorrencia_id=ocorrencia_id,
        autor_id=usuario_atual.id, 
        mensagem_acao=atualizacao_in.mensagem_acao
    )
    session.add(nova_atualizacao)
    session.commit()
    session.refresh(nova_atualizacao)
    return nova_atualizacao