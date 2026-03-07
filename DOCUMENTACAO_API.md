# Documentação Técnica - Backend MVP Campus Seguro

Esta documentação descreve a estrutura da camada de dados e da API do projeto **Campus Seguro**, desenvolvidas utilizando **Python**, **FastAPI** e **SQLModel**.

## 1. Modelagem de Dados (`models.py`)

O arquivo `models.py` contém a definição das tabelas do banco de dados relacional e as regras de negócio intrínsecas (Enums). Ele utiliza a biblioteca `SQLModel`, que une o poder do SQLAlchemy (ORM) com o Pydantic (validação de dados).

### Enums (Domínios de Dados)
Definem os valores permitidos para campos específicos, garantindo a integridade dos dados:
* **`TipoPerfil`**: Define as permissões de sistema (`ALUNO`, `COLABORADOR`, `SEGURANCA`).
* **`StatusOcorrencia`**: Controla o ciclo de vida do chamado (`ABERTO`, `EM_ATENDIMENTO`, `RESOLVIDO`).
* **`TipoMidia`**: Classifica os anexos de evidências (`FOTO`, `VIDEO`, `AUDIO`).

### Entidades (Tabelas)
* **`Usuario`**: Armazena os dados de autenticação e perfil de quem usa o sistema.
    * *Relacionamentos:* Pode registrar várias ocorrências e (se for da segurança) pode atender várias ocorrências.
* **`Ocorrencia`**: Tabela central do sistema. Registra os chamados de emergência.
    * *Regra de Privacidade:* O campo `usuario_id` é opcional (`nullable=True`), cumprindo o requisito não-funcional de permitir o anonimato no registro.
* **`AtualizacaoOcorrencia`**: Garante a trilha de auditoria e a comunicação. Registra cada mudança de status ou mensagem trocada no chamado.
* **`Evidencia`**: Armazena as URLs de mídias (fotos, vídeos) anexadas a uma ocorrência específica.

---

## 2. Camada de Aplicação e API (`main.py`)

O arquivo `main.py` é o ponto de entrada da aplicação. Ele inicializa o servidor web usando **FastAPI** e expõe os endpoints (rotas) para comunicação com o aplicativo mobile e o painel web.

### Configuração de Infraestrutura
* **Banco de Dados:** Atualmente configurado para utilizar **SQLite** (`campus_seguro.db`) visando facilitar o desenvolvimento e testes do MVP.
* **Inicialização (`on_startup`):** O sistema verifica e cria as tabelas no banco de dados automaticamente assim que o servidor é iniciado.
* **Injeção de Dependência (`get_session`):** Garante que cada requisição à API abra e feche uma conexão segura e isolada com o banco de dados.

### Schemas (DTOs de Validação)
Diferente dos modelos de banco, os Schemas validam o que a API *recebe* do usuário (o JSON do body da requisição):
* **`OcorrenciaCreate`**: Define os campos obrigatórios e opcionais para criar um chamado. Aceita `usuario_id` nulo para denúncias anônimas.
* **`OcorrenciaUpdate`**: Permite a atualização parcial de um chamado (ex: enviar apenas o novo `status` ou o `responsavel_id`).

### Endpoints (Rotas da API)

| Método | Rota | Descrição | Status Code de Sucesso |
| :--- | :--- | :--- | :--- |
| **POST** | `/ocorrencias/` | Aciona o botão de emergência. Registra um novo chamado no banco de dados com status padrão "ABERTO" e gera um UUID único. | `201 Created` |
| **GET** | `/ocorrencias/` | Lista todas as ocorrências registradas. Rota projetada para alimentar o painel de monitoramento da equipe de segurança. | `200 OK` |
| **PATCH** | `/ocorrencias/{ocorrencia_id}` | Atualiza uma ocorrência específica. Usado pela equipe de segurança para mudar o status (ex: para "EM_ATENDIMENTO") e assumir a responsabilidade pelo chamado. | `200 OK` |