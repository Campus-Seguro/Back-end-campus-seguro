# Documentação Técnica e Manual de Execução - MVP Campus Seguro

Este documento contém todas as instruções necessárias para configurar, executar e testar o back-end do projeto **Campus Seguro**. A API foi desenvolvida em **Python** utilizando o framework **FastAPI** e a biblioteca **SQLModel** (com base de dados SQLite para o MVP).

---

## 1. Manual de Configuração (Como executar o projeto)

Para que qualquer membro da equipa consiga correr a API no seu próprio computador, siga estes passos:

### Pré-requisitos
1. Ter o **Python 3.8+** instalado no computador.
2. Ter os ficheiros `main.py` e `models.py` na mesma pasta.

### Passo 1: Instalar as dependências
Abra o terminal (ou linha de comandos) na pasta do projeto e execute:
```bash
pip install fastapi "uvicorn[standard]" sqlmodel python-multipart
```
> Nota: a biblioteca `python-multipart` é necessária para que o formulário de Login do OAuth2 funcione corretamente.

### Passo 2: Iniciar o Servidor
Na mesma pasta, execute o comando:
```bash
uvicorn main:app --reload
```
A API estará online! O ficheiro da base de dados `campus_seguro.db` será criado automaticamente na pasta.

### Passo 3: Aceder à Interface de Testes (Swagger)
Abra o navegador e aceda a:
- `http://localhost:8000/docs` (Swagger)
- `http://localhost:8000/redoc` (ReDoc)

---

## 2. Guia de Uso: Como testar o Fluxo Completo

A nossa API possui rotas protegidas por autenticação. Siga este fluxo exato no Swagger para simular a jornada de um utilizador:

### 1º Passo: Criar um Utilizador
1. Vá à rota `POST /usuarios/`.
2. Clique em **Try it out**.
3. Preencha o JSON com os dados (ex: email `aluno@teste.com` e senha `123`).
4. Clique em **Execute**.

### 2º Passo: Fazer Login (Gerar o Token / Crachá)
1. Vá à rota `POST /login` (ou clique no botão verde **Authorize** com o cadeado no topo do ecrã).
2. No campo `username`, coloque o email do utilizador recém-criado.
3. No campo `password`, coloque a senha.
4. Clique em **Authorize** (ou **Execute**).
5. O sistema reconhecerá o utilizador e todas as rotas com cadeado ficarão destrancadas para si.

### 3º Passo: Acionar a Emergência
1. Com o login feito, vá ao `POST /ocorrencias/`.
2. Altere o campo `localizacao` (ex: "Bloco C") e clique em **Execute**.
3. Guarde o `id` (UUID) gerado na resposta.

### 4º Passo: Anexar Evidências e Linha do Tempo
1. Use o `id` da ocorrência guardado para testar a rota `POST /ocorrencias/{ocorrencia_id}/evidencias` (simulando o envio de uma foto).
2. Teste também `POST /ocorrencias/{ocorrencia_id}/atualizacoes` (simulando uma mensagem no chat com a segurança).

---

## 3. Modelagem e Estrutura de Base de Dados (`models.py`)

O ficheiro `models.py` contém a definição das tabelas da base de dados relacional e as regras de negócio intrínsecas (Enums).

### Enums (Domínios de Dados)

- **TipoPerfil**: Define as permissões de sistema (ALUNO, COLABORADOR, SEGURANCA).
- **StatusOcorrencia**: Controla o ciclo de vida do chamado (ABERTO, EM_ATENDIMENTO, RESOLVIDO).
- **TipoMidia**: Classifica os anexos de evidências (FOTO, VIDEO, AUDIO).

### Entidades (Tabelas)

- **Usuario**: Armazena os dados de autenticação e perfil de quem usa o sistema. Responsável por garantir quem abre e quem atende os chamados.
- **Ocorrencia**: Tabela central do sistema. Regista os chamados de emergência. O campo `usuario_id` é opcional (nullable=True), permitindo anonimato no registo.
- **AtualizacaoOcorrencia**: Garante a trilha de auditoria e a comunicação. Regista cada mudança de estado ou mensagem trocada no chamado.
- **Evidencia**: Armazena as URLs de mídias (fotos, vídeos) anexadas a uma ocorrência específica.

---

## 4. Endpoints Disponíveis (`main.py`)

### Autenticação & Gestão de Utilizadores

| Método | Rota | Descrição | Protegida |
|---|---|---|---|
| POST | `/login` | Valida email/senha e devolve o Token de acesso (OAuth2) | Não |
| POST | `/usuarios/` | Regista um novo utilizador no sistema | Não |
| GET | `/usuarios/` | Lista todos os utilizadores registados | Não |

### Jornada de Ocorrências (Botão de Emergência)

| Método | Rota | Descrição | Protegida |
|---|---|---|---|
| POST | `/ocorrencias/` | Aciona o Botão SOS. Cria o alerta inicial na base de dados | Sim 🔒 |
| GET | `/ocorrencias/` | Lista todas as ocorrências (Para o Painel da equipa de Segurança) | Não |
| GET | `/ocorrencias/{id}` | Busca os detalhes de um chamado específico (Acompanhamento) | Não |
| PATCH | `/ocorrencias/{id}` | Segurança assume o chamado e altera o estado | Não |

### Detalhamento e Linha do Tempo

| Método | Rota | Descrição | Protegida |
|---|---|---|---|
| POST | `/ocorrencias/{id}/evidencias` | Anexa uma mídia (foto/vídeo) ao chamado existente | Não |
| POST | `/ocorrencias/{id}/atualizacoes` | Adiciona uma mensagem no chat/linha do tempo do chamado | Não |

---

## 5. Observações Técnicas

- O projeto usa tokens simulados (`fake-jwt-token-<id>`) e não faz validação JWT de verdade no MVP.
- As senhas são armazenadas como `hash_falso_<senha>` para fins de MVP.
- O SQLite cria o arquivo `campus_seguro.db` automaticamente na primeira execução.
- Para implementação em produção, considere usar hashing de senha seguro (bcrypt) e JWT real.       