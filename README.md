# Sistema de Atendimento ao Cliente com IA

Projeto de Bloco de Análise e Segurança de Agentes de IA

## Objetivo do projeto

Desenvolver um sistema capaz de classificar a intenção de chamados de suporte a partir dos dados enviados pelo cliente. `Ticket Type` e `Ticket Subject` serão as variáveis-alvo da classificação, e o sistema será disponibilizado por uma API FastAPI modular e protegida por autenticação JWT.

## Escopo do projeto

- Análise exploratória: compreensão do problema e do dataset, inspeção inicial, verificação da qualidade, limpeza, preparação e análise univariada.
- Formulação de hipóteses sobre as intenções dos usuários a partir das distribuições observadas.
- API FastAPI modular com as rotas `GET /health`, `POST /auth/token` e `POST /predict`.
- Autenticação JWT com `OAuth2PasswordBearer` e proteção da rota de predição.
- Diagrama de fluxo de dados com entradas, saídas e limites de confiança, acompanhado da análise de confidencialidade, integridade e disponibilidade.

## Dataset

- **Nome:** Customer Support Ticket Dataset
- **Fonte:** [Customer Support Ticket Dataset no Kaggle](https://www.kaggle.com/datasets/suraj520/customer-support-ticket-dataset/data), publicado por `suraj520`
- **Conteúdo:** 8.469 chamados de suporte e 17 colunas com informações sobre clientes, produtos, chamados e atendimento.

A fonte, as principais características e o motivo da escolha do dataset estão detalhados no início do notebook [`eda/eda.ipynb`](eda/eda.ipynb).

## Estrutura de pastas

```
.
├── data/
│   └── customer_support_tickets.csv     # dataset usado no EDA e na API
├── eda/
│   └── eda.ipynb                        # análise exploratória completa
├── fastapi/
│   ├── main.py                          # ponto de entrada da aplicação
│   ├── database.py                      # engine SQLModel e sessão (get_session)
│   ├── database.db                      # banco SQLite (usuários e predictions)
│   ├── sqlite_database.py               # criação e população inicial do banco (sqlite3)
│   ├── requirements.txt                 # dependências da API
│   ├── .env.example                     # modelo de variáveis de ambiente
│   ├── Dockerfile                       # imagem da API
│   ├── compose.yml                      # orquestração via Docker Compose
│   ├── models/
│   │   ├── schemas.py                   # modelos Pydantic (request/response)
│   │   └── tables.py                    # tabelas SQLModel (User, Prediction)
│   ├── routes/
│   │   ├── health.py                    # GET /health
│   │   ├── auth.py                      # POST /auth/token
│   │   └── predict.py                   # POST /predict, GET /predict e GET /predict/{id} (protegidas)
│   └── security/
│       └── auth.py                      # JWT, OAuth2PasswordBearer, autenticação via banco
├── others/
│   ├── dfd.png                          # diagrama de fluxo de dados
│   └── dfd.dot                          # fonte do diagrama (Graphviz)
├── .gitignore
└── README.md
```

## Instalação

```bash
# Clonar o repositório
git clone https://github.com/Phoenix7290/Caua_Guilherme_Gustavo_Marcos.git
cd Caua_Guilherme_Gustavo_Marcos/fastapi

# Criar e ativar o ambiente virtual
python3 -m venv .venv
source .venv/bin/activate        # Linux/macOS
# .venv\Scripts\activate         # Windows

# Instalar as dependências
pip install -r requirements.txt

cp .env.example .env
# Edite o .env e defina um valor para SECRET_KEY
```

## Execução

### EDA (notebook)

Abra o notebook no Jupyter ou no VS Code e execute as células em ordem:

```bash
jupyter notebook eda/eda.ipynb
```

O notebook lê o dataset de `data/customer_support_tickets.csv` por caminho relativo, então execute-o a partir da pasta `eda/`, como o Jupyter já faz por padrão.

### API

A partir do diretório `fastapi/`:

```bash
uvicorn main:app --reload
```

A API sobe em `http://localhost:8000`. A documentação interativa (Swagger) fica em `http://localhost:8000/docs`.

## Ambiente publicado

A API também está disponível publicamente (hospedada em um Raspberry Pi 5, exposta via Cloudflare Tunnel):

**URL base:** https://supportdesk-api.marcosryan.com

Documentação interativa (Swagger): https://supportdesk-api.marcosryan.com/docs

### Testando

```bash
# Health check
curl https://supportdesk-api.marcosryan.com/health

# Autenticação (retorna um token JWT válido por 15 minutos)
curl -X POST https://supportdesk-api.marcosryan.com/auth/token \
  -d "username=admin&password=admin123"

# Predição (substitua <TOKEN> pelo access_token retornado acima)
curl -X POST https://supportdesk-api.marcosryan.com/predict \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"text": "meu produto parou de funcionar"}'
```

## Self Hosting

Requer Docker e Docker Compose instalados.

A partir do diretório `fastapi/`:

```bash
cp .env.example .env
# edite o .env e defina o SECRET_KEY

docker compose up -d --build
```

A API sobe em `http://localhost:8000`.

## Autenticação

Os usuários ficam na tabela `user` do SQLite (`fastapi/database.db`), com senha armazenada como hash (`bcrypt`). O banco é criado e populado por `fastapi/sqlite_database.py` (`python sqlite_database.py`, a partir de `fastapi/`; recria o arquivo do zero) com dois usuários:

| usuário | senha |
|---|---|
| `admin` | `admin123` |
| `alice` | `alice123` |

Cada predição salva na tabela `prediction` possui um `owner_id` (chave estrangeira para `user.id`). Todas as consultas da API usam SQLModel, sem SQL raw.

Fluxo:

1. `POST /auth/token` com `username` e `password` (form-data) → retorna um `access_token` (JWT).
2. Use esse token como `Bearer <token>` no header `Authorization` para acessar rotas protegidas.

## Rotas

| Método | Rota | Autenticação | Descrição |
|---|---|---|---|
| GET | `/health` | Não | Verifica se a API está ativa |
| POST | `/auth/token` | Não | Autentica um usuário do banco e retorna um JWT |
| POST | `/predict` | Sim (Bearer JWT) | Recebe o texto de um chamado e retorna uma intenção classificada (regra fixa; modelo de ML será implementado em etapa futura) e salva a predição para o usuário autenticado |
| GET | `/predict` | Sim (Bearer JWT) | Lista somente as predições do usuário autenticado |
| GET | `/predict/{id}` | Sim (Bearer JWT) | Retorna uma predição do usuário autenticado (`404` se não existir ou pertencer a outro usuário) |

## Segurança

- Autenticação via JWT com `OAuth2PasswordBearer`.
- Senhas dos usuários armazenadas com hash `bcrypt` (nunca em texto puro).
- Chave de assinatura do token (`SECRET_KEY`) carregada de variável de ambiente (`.env`, fora do controle de versão) — nunca hardcoded no código-fonte.
- Cada predição pertence a um `owner_id`; um usuário nunca lê predições de outro (acesso a predição alheia retorna `404`).
- As rotas `/predict` exigem token JWT válido; tentativas sem token ou com token expirado/inválido retornam `401 Unauthorized`.
- O diagrama de fluxo de dados (`others/dfd.png`) detalha as trust boundaries do sistema (internet pública ↔ borda, borda ↔ dispositivo, rotas públicas ↔ rotas autenticadas) e a análise de confidencialidade, integridade e disponibilidade por componente.

## Hospedagem

A API é hospedada localmente em um Raspberry Pi 5 (Ubuntu Server), exposta publicamente via Cloudflare Tunnel.

## Integrantes da Equipe

- Cauã Henrique
- Guilherme Reis
- Gustavo Gaudereto
- Marcos Ryan
