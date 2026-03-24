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
pip install -r requirements.txt
```

Ou manualmente (para adicionar mais dependências):

```bash
pip install fastapi uvicorn sqlmodel PyJWT "python-multipart"
```

> Nota: o ficheiro `requirements.txt` contém todas as dependências necessárias. A biblioteca `python-multipart` é necessária para o formulário de Login do OAuth2, e `PyJWT` é essencial para a geração e validação de tokens JWT.

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

O banco de dados foi desenhado com uma abordagem simplificada para o MVP, focando nos componentes essenciais do controlo de acessos e gestão de ocorrências.

### 2.1 Enumerados (Tipos/Dominios do Sistema)

**TipoPerfil**: Categorias de utilizadores.
- `ALUNO` - Aluno do campus
- `COLABORADOR` - Colaborador/Staff
- `SEGURANCA` - Agente de Segurança (Responsável pelo atendimento)

**StatusOcorrencia**: Estados de uma ocorrência.
- `ABERTO` - Ocorrência foi criada mas ainda não atendida
- `EM_ATENDIMENTO` - Agente de Segurança assumiu o chamado
- `RESOLVIDO` - Ocorrência foi resolvida

**TipoMidia**: Tipos de evidências que podem ser anexadas.
- `FOTO`
- `VIDEO`
- `AUDIO`

### 2.2 Tabelas Principais

**Usuario**: Autenticação e dados dos utilizadores.
- `id` (UUID, PK) - Identificador único
- `nome` (VARCHAR) - Nome completo
- `email` (VARCHAR, UNIQUE) - Email único para login
- `senha_hash` (VARCHAR) - Senha com hash de segurança
- `tipo_perfil` (ENUM) - Tipo de perfil (ALUNO, COLABORADOR, SEGURANCA)

### 2.3 Tabelas de Negócio

**Ocorrencia**: Entidade central de registo de incidentes.
- `id` (UUID, PK) - Identificador único
- `usuario_id` (UUID, FK → Usuario.id, NULLABLE) - Criador da ocorrência (NULL se anónima)
- `tipo_incidente` (VARCHAR) - Tipo de incidente registado
- `descricao` (TEXT) - Descrição detalhada do incidente
- `localizacao` (VARCHAR) - Local onde o incidente ocorreu
- `status` (ENUM) - Estado atual (ABERTO, EM_ATENDIMENTO, RESOLVIDO)
- `data_criacao` (TIMESTAMP) - Data/hora de criação
- `responsavel_id` (UUID, FK → Usuario.id, NULLABLE) - Agente de Segurança responsável

**Evidencia**: Ficheiros multimédia (fotos, vídeos, áudio) anexados.
- `id` (UUID, PK) - Identificador único
- `ocorrencia_id` (UUID, FK → Ocorrencia.id) - Referência à ocorrência
- `url_anexo` (VARCHAR) - URL ou caminho do ficheiro
- `tipo_midia` (ENUM) - Tipo de media (FOTO, VIDEO, AUDIO)

**AtualizacaoOcorrencia**: Linha do tempo / Chat da ocorrência (Auditoria).
- `id` (UUID, PK) - Identificador único
- `ocorrencia_id` (UUID, FK → Ocorrencia.id) - Referência à ocorrência
- `autor_id` (UUID, FK → Usuario.id) - Quem registou a atualização
- `mensagem_acao` (TEXT) - Conteúdo da mensagem/ação
- `data_atualizado` (TIMESTAMP) - Data/hora da atualização

---

## 🌐 3. Documentação da API (Endpoints)

A API segue os padrões RESTful e implementa controlo de acesso baseado em perfis (RBAC). Abaixo encontra-se o mapeamento das rotas principais.

### 🧑‍💻 Autenticação e Gestão de Utilizadores

| Método | Rota | Descrição | Protegida |
|---|---|---|---|
| POST | `/login` | Valida email/senha e devolve o Token de acesso (OAuth2) | Não |
| POST | `/usuarios/` | Regista um novo utilizador no sistema | Não |
| GET | `/usuarios/` | Lista todos os utilizadores registados | Sim 🔒 |

#### Exemplo de Login (POST /login) - Form Data:

```
POST /login HTTP/1.1
Content-Type: application/x-www-form-urlencoded

username=joao@email.com&password=senha_forte_123
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### Exemplo de Payload (POST /usuarios/):

```json
{
  "nome": "João Silva",
  "email": "joao@email.com",
  "senha": "senha_forte_123",
  "tipo_perfil": "ALUNO"
}
```

**Valores válidos para `tipo_perfil`:**
- `ALUNO` - Aluno do campus
- `COLABORADOR` - Colaborador/Staff
- `SEGURANCA` - Agente de Segurança

### 🚨 Jornada de Ocorrências (Botão de Emergência e Relatos)

| Método | Rota | Descrição | Protegida |
|---|---|---|---|
| POST | `/ocorrencias/` | Cria o alerta/denúncia na base de dados (Suporta flag anonimo) | Sim 🔒 |
| GET | `/ocorrencias/` | Lista ocorrências (RBAC: Segurança vê todas, outros veem só suas) | Sim 🔒 |
| GET | `/ocorrencias/{id}` | Busca os detalhes de uma ocorrência específica | Sim 🔒 |
| PATCH | `/ocorrencias/{id}` | Atualiza o estado da ocorrência (Apenas Segurança) | Sim 🔒 |

#### Exemplo de Payload (POST /ocorrencias/):

```json
{
  "anonimo": true,
  "tipo_incidente": "Assédio",
  "descricao": "Fui abordado de forma inadequada no corredor principal.",
  "localizacao": "Bloco B - 2º Andar"
}
```

**Observações:**
- Se `anonimo` for `true`, o campo `usuario_id` será NULL na DB
- O utilizador é automaticamente atribuído como criador (a menos que seja anónimo)
- O status inicial é automaticamente `ABERTO`

#### Exemplo de Payload (PATCH /ocorrencias/{id}):

```json
{
  "status": "EM_ATENDIMENTO",
  "responsavel_id": "uuid-agente-seguranca"
}
```

**Valores válidos para `status`:**
- `ABERTO` - Ocorrência foi criada mas ainda não atendida
- `EM_ATENDIMENTO` - Agente assumiu o chamado
- `RESOLVIDO` - Ocorrência foi resolvida

**Permissões:**
- Apenas agentes com perfil `SEGURANCA` podem atualizar ocorrências
- Se `responsavel_id` não for fornecido, o agente atual é atribuído automaticamente

### 📁 Evidências e Linha do Tempo

| Método | Rota | Descrição | Protegida |
|---|---|---|---|
| POST | `/ocorrencias/{id}/evidencias` | Anexa uma mídia (foto/vídeo/áudio) ao chamado | Sim 🔒 |
| POST | `/ocorrencias/{id}/atualizacoes` | Adiciona uma mensagem/atualização na linha do tempo | Sim 🔒 |

#### Exemplo de Payload (POST /ocorrencias/{id}/evidencias):

```json
{
  "url_anexo": "https://example.com/files/foto_incidente.jpg",
  "tipo_midia": "FOTO"
}
```

**Valores válidos para `tipo_midia`:**
- `FOTO` - Ficheiro de imagem
- `VIDEO` - Ficheiro de vídeo
- `AUDIO` - Ficheiro de áudio

**Permissões:**
- O criador da ocorrência pode anexar evidências nas suas
- Agentes de Segurança podem anexar evidências em qualquer ocorrência

#### Exemplo de Payload (POST /ocorrencias/{id}/atualizacoes):

```json
{
  "mensagem_acao": "Incidente foi investigado. Não foi encontrada evidência de má conduta."
}
```

**Permissões:**
- O criador da ocorrência pode adicionar atualizações
- Agentes de Segurança podem adicionar atualizações em qualquer ocorrência

---

## 🛠️ 4. Observações Técnicas e Estrutura

### Arquivos do Projeto

- **models.py**: Contém as definições dos modelos SQLModel (tabelas) e enumerados (Enums):
  - `Usuario` - Gestão de utilizadores e autenticação
  - `Ocorrencia` - Entidade central de incidentes
  - `Evidencia` - Anexos multimédia
  - `AtualizacaoOcorrencia` - Linha do tempo / auditoria
  - Enums: `TipoPerfil`, `StatusOcorrencia`, `TipoMidia`

- **main.py**: Ficheiro principal com:
  - Configuração do FastAPI e SQLite
  - Inicialização do motor de banco de dados
  - Implementação do OAuth2 com JWT
  - Todos os routers (endpoints) da API
  - Lógica de RBAC (Controlo de Acesso Baseado em Perfis)

- **requirements.txt**: Lista de dependências Python do projeto

### Segurança e Autenticação (MVP)

- **JWT (JSON Web Tokens)**: Tokens JWT reais são gerados com validade de 24 horas
- **OAuth2**: Implementação OAuth2 com bearer tokens
- **Hashing de Senhas**: No MVP, as senhas utilizam um sistema de hash simplificado (`hash_falso_<senha>`). Para produção, **utilizar bibliotecas como `bcrypt` ou `passlib`**
- **RBAC**: O sistema valida o tipo de perfil (`TipoPerfil`) para determinar permissões:
  - `ALUNO` / `COLABORADOR`: Podem criar ocorrências, ver apenas as suas
  - `SEGURANCA`: Acesso total para atender ocorrências

### Controlo de Acesso (RBAC)

| Ação | ALUNO | COLABORADOR | SEGURANCA |
|---|---|---|---|
| Criar ocorrência | ✅ | ✅ | ✅ |
| Listar ocorrências | Apenas suas | Apenas suas | Todas |
| Ver detalhes | Suas | Suas | Qualquer |
| Atualizar status | ❌ | ❌ | ✅ |
| Assumir chamado | ❌ | ❌ | ✅ |
| Anexar evidências | Suas | Suas | Qualquer |
| Adicionar atualizações | Suas | Suas | Qualquer |

### Fluxo de Autenticação

1. **Registo**: Novo utilizador POST `/usuarios/` → Criado na BD
2. **Login**: POST `/login` com (email, senha) → Retorna JWT token
3. **Requisição Autenticada**: Cliente inclui `Authorization: Bearer <token>` no header
4. **Validação**: FastAPI extrai e valida JWT → Retorna `Usuario` ou erro 401

### Anonimato em Ocorrências

- Se `anonimo: true` ao criar ocorrência, `usuario_id` é definido como NULL
- A API cumpre a solicitação preservando a identidade do criador
- **Nota**: A linha do tempo (AtualizacaoOcorrencia) registra sempre tempo/autor para auditoria

### Ciclo de Vida de uma Ocorrência

```
ABERTO → EM_ATENDIMENTO → RESOLVIDO
```

**Estados:**
- `ABERTO`: Recém-criada, aguardando atendimento
- `EM_ATENDIMENTO`: Agente de Segurança está a investigar/responder
- `RESOLVIDO`: Ocorrência foi encerrada

### Comunicações e Linha do Tempo

- Cada POST em `/ocorrencias/{id}/atualizacoes` cria um novo registo em `AtualizacaoOcorrencia`
- Permite rastreio completo de todas as ações e comentários
- Preserva `autor_id` para auditoria (quem escreveu, quando)

---

## 📊 5. Códigos de Status HTTP

| Código | Significado |
|---|---|
| 200 | OK - Requisição bem-sucedida |
| 201 | Created - Recurso criado com sucesso |
| 400 | Bad Request - Dados inválidos no pedido |
| 401 | Unauthorized - Token inválido ou expirado |
| 403 | Forbidden - Acesso negado (permissão insuficiente) |
| 404 | Not Found - Recurso não encontrado |

### Exemplo de Erro (401 - Não Autenticado):

```json
{
  "detail": "Não foi possível validar as credenciais"
}
```

### Exemplo de Erro (403 - Acesso Negado):

```json
{
  "detail": "Acesso negado. Esta ação requer perfil de Segurança."
}
```

---

## 🔧 6. Configurações e Variáveis Importantes

| Variável | Valor | Descrição |
|---|---|---|
| `SECRET_KEY` | `chave-super-secreta-campus-seguro-mvp` | Chave para assinar JWT (⚠️ Mudar em produção) |
| `ALGORITHM` | `HS256` | Algoritmo de encriptação JWT |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` (24h) | Tempo de expiração do token |
| `sqlite_url` | `sqlite:///campus_seguro.db` | Base de dados SQLite |

---

## 🎯 7. Plano de Melhorias Futuras

- Implementar hash seguro de senhas (`bcrypt` / `passlib`)
- Adicionar campo `prioridade` na tabela `Ocorrencia`
- Implementar filtros avançados (por data, prioridade, status)
- Autenticação multi-factor (MFA)
- Integração com sistema de notificações (SMS/Email)
- Dashboard de estatísticas para administradores
- Suporte a documentos (PDF, Word) como evidências

---

## 🧪 8. Exemplos de Teste (cURL / POSTMAN)

### 1. Registar um novo utilizador

```bash
curl -X POST "http://localhost:8000/usuarios/" \
  -H "Content-Type: application/json" \
  -d '{
    "nome": "João Silva",
    "email": "joao@email.com",
    "senha": "senha_forte_123",
    "tipo_perfil": "ALUNO"
  }'
```

**Response (201 Created):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "nome": "João Silva",
  "email": "joao@email.com",
  "tipo_perfil": "ALUNO"
}
```

### 2. Fazer Login

```bash
curl -X POST "http://localhost:8000/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=joao@email.com&password=senha_forte_123"
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJqb2FvQGVtYWlsLmNvbSIsImV4cCI6MTcxNjU0NDAwMH0.abc123...",
  "token_type": "bearer"
}
```

### 3. Criar uma Ocorrência

```bash
curl -X POST "http://localhost:8000/ocorrencias/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "anonimo": false,
    "tipo_incidente": "Assédio",
    "descricao": "Fui abordado de forma inadequada no corredor.",
    "localizacao": "Bloco B - 2º Andar"
  }'
```

**Response (201 Created):**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "usuario_id": "550e8400-e29b-41d4-a716-446655440000",
  "tipo_incidente": "Assédio",
  "descricao": "Fui abordado de forma inadequada no corredor.",
  "localizacao": "Bloco B - 2º Andar",
  "status": "ABERTO",
  "data_criacao": "2024-03-24T15:30:00"
}
```

### 4. Listar Minhas Ocorrências

```bash
curl -X GET "http://localhost:8000/ocorrencias/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**Response (200 OK):**
```json
[
  {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "usuario_id": "550e8400-e29b-41d4-a716-446655440000",
    "tipo_incidente": "Assédio",
    ...
  }
]
```

### 5. Anexar uma Evidência

```bash
curl -X POST "http://localhost:8000/ocorrencias/123e4567-e89b-12d3-a456-426614174000/evidencias" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "url_anexo": "https://example.com/files/foto-incidente.jpg",
    "tipo_midia": "FOTO"
  }'
```

### 6. Adicionar Atualização (Chat)

```bash
curl -X POST "http://localhost:8000/ocorrencias/123e4567-e89b-12d3-a456-426614174000/atualizacoes" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "mensagem_acao": "Estou à espera de resposta da segurança."
  }'
```

---

## 📝 9. Notas Importantes

- **Expiração do Token**: Os tokens JWT expiram após 24 horas. É necessário fazer login novamente.
- **Ambiente de Produção**: 
  - ⚠️ Mudar `SECRET_KEY` para uma chave segura e aleatória
  - ⚠️ Implementar hash robusto de senhas (`bcrypt`)
  - ⚠️ Usar HTTPS em vez de HTTP
  - ⚠️ Implementar CORS adequadamente
- **Base de Dados**: O SQLite é adquado para MVP, mas considerar PostgreSQL para produção