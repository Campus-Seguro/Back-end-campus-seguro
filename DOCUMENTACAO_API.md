# 🛡️ Documentação Técnica e Manual de Execução - Back-end Campus Seguro

Este documento contém todas as instruções necessárias para configurar, executar e testar o back-end do projeto Campus Seguro, bem como o detalhe da arquitetura de dados (Base de Dados) e a listagem de endpoints. A API foi desenvolvida em Python utilizando o framework FastAPI e a biblioteca SQLModel (com base de dados SQLite para o MVP).

---

## ⚙️ 1. Manual de Configuração (Como executar o projeto)

Para que qualquer membro da equipa consiga correr a API no seu próprio computador, siga estes passos:

### Pré-requisitos

- Ter o Python 3.8+ instalado no computador.
- Ter os ficheiros `main.py` e `models.py` na mesma pasta.

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

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 💾 2. Modelagem da Base de Dados (Esquema Relacional)

O banco de dados foi desenhado para suportar o controlo de acessos baseado em perfis (RBAC) e garantir a rastreabilidade (auditoria) de todo o ciclo de vida de uma ocorrência.

### Diagrama ER (Entity-Relationship)

![Diagrama ER - Campus Seguro](diagrama_er.png)

*Visualização completa do esquema relacional com todas as entidades, atributos e relacionamentos.*

### 2.1 Tabelas de Controlo de Acesso (RBAC)

**Perfil**: Gere os papéis do sistema (ex: Denunciante, Agente, Administrador).
- `id` (INT, PK)
- `nome` (VARCHAR)
- `descricao` (VARCHAR)

**Permissao**: Ações específicas permitidas dentro do sistema.
- `id` (INT, PK)
- `nome` (VARCHAR)
- `descricao` (VARCHAR)

**Perfil_Permissao**: Tabela associativa (N:M).
- `perfil_id` (FK → Perfil.id)
- `permissao_id` (FK → Permissao.id)

**Usuario**: Autenticação e dados dos utilizadores.
- `id` (UUID, PK)
- `nome` (VARCHAR)
- `email` (VARCHAR, UNIQUE)
- `senha_hash` (VARCHAR)
- `perfil_id` (INT, FK → Perfil.id)
- `data_criacao` (TIMESTAMP)

### 2.2 Tabelas de Negócio (Ocorrências)

**Status**: Domínio dos estados de uma ocorrência (ex: Aberto, Em Análise, Resolvido).
- `id` (INT, PK)
- `nome` (VARCHAR)

**Ocorrencia** (ou Denuncia): Entidade central de registo de incidentes.
- `id` (INT, PK)
- `denunciante_id` (UUID, FK → Usuario.id)
- `agente_id` (UUID, NULLABLE, FK → Usuario.id)
- `titulo` (VARCHAR)
- `descricao` (TEXT)
- `localizacao` (VARCHAR)
- `data_hora_incidente` (TIMESTAMP)
- `prioridade` (VARCHAR)
- `anonima` (BOOLEAN)
- `status_id` (INT, FK → Status.id)

**Evidencia**: Ficheiros multimédia (fotos, vídeos) anexados.
- `id` (INT, PK)
- `ocorrencia_id` (INT, FK → Ocorrencia.id)
- `arquivo_url` (VARCHAR)
- `tipo_arquivo` (VARCHAR)
- `data_upload` (TIMESTAMP)

**Historico_Auditoria**: Trilha de ações para segurança institucional.
- `id` (INT, PK)
- `ocorrencia_id` (INT, FK → Ocorrencia.id)
- `usuario_acao_id` (UUID, FK → Usuario.id)
- `acao_realizada` (VARCHAR)
- `observacao_interna` (TEXT)
- `data_registro` (TIMESTAMP)

---

## 🌐 3. Documentação da API (Endpoints)

A API segue os padrões RESTful. Abaixo encontra-se o mapeamento das rotas principais.

### 🧑‍💻 Autenticação e Gestão de Utilizadores

| Método | Rota | Descrição | Protegida |
|---|---|---|---|
| POST | `/login` | Valida email/senha e devolve o Token de acesso (OAuth2) | Não |
| POST | `/usuarios/` | Regista um novo utilizador no sistema (Denunciante ou Agente) | Não |
| GET | `/usuarios/` | Lista todos os utilizadores registados (Requer perfil Admin) | Sim 🔒 |

#### Exemplo de Payload (POST /usuarios/):

```json
{
  "nome": "João Silva",
  "email": "joao@email.com",
  "senha": "senha_forte_123",
  "perfil_id": 1
}
```

### 🚨 Jornada de Ocorrências (Botão de Emergência e Relatos)

| Método | Rota | Descrição | Protegida |
|---|---|---|---|
| POST | `/ocorrencias/` | Cria o alerta/denúncia na base de dados (Suporta flag anonima) | Sim 🔒 |
| GET | `/ocorrencias/` | Lista todas as ocorrências (Filtros: ?status=Aberto, ?prioridade=ALTA) | Sim 🔒 |
| GET | `/ocorrencias/{id}` | Busca os detalhes de um chamado específico | Sim 🔒 |
| PATCH | `/ocorrencias/{id}` | Atualiza o estado da ocorrência (ex: Agente assume o chamado) | Sim 🔒 |

#### Exemplo de Payload (POST /ocorrencias/):

```json
{
  "denunciante_id": "uuid-do-utilizador",
  "titulo": "Assédio no Bloco B",
  "descricao": "Fui abordado de forma inadequada no corredor...",
  "localizacao": "Bloco B - 2º Andar",
  "prioridade": "ALTA",
  "anonima": true
}
```

> Nota: Se `anonima` for `true`, a API mascara o `denunciante_id` nas respostas GET para Agentes.

### 📁 Detalhamento e Linha do Tempo

| Método | Rota | Descrição | Protegida |
|---|---|---|---|
| POST | `/ocorrencias/{id}/evidencias` | Anexa uma multimédia (foto/vídeo) ao chamado existente | Sim 🔒 |
| POST | `/ocorrencias/{id}/atualizacoes` | Adiciona uma mensagem/ação no histórico de auditoria | Sim 🔒 |

---

## 🛠️ 4. Observações Técnicas e Estrutura

- **models.py**: Contém as definições declarativas das tabelas utilizando o SQLModel. As chaves estrangeiras e os relacionamentos garantem a integridade referencial detalhada na Secção 2.

- **main.py**: Ficheiro principal onde os routers do FastAPI estão configurados, bem como a inicialização do motor SQLite (`campus_seguro.db`).

- **Segurança do MVP**: O projeto atualmente utiliza tokens simulados (`fake-jwt-token-<id>`) para facilitar os testes iniciais de integração com o Front-end. No entanto, as senhas já devem transitar em formato de hash na base de dados por questões de boas práticas.

- **Auditoria Automática**: Qualquer chamada à rota PATCH `/ocorrencias/{id}` deve desencadear automaticamente um INSERT na tabela `Historico_Auditoria` para manter o rastreio exigido pelos requisitos institucionais.       