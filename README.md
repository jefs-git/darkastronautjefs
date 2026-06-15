# API de Sinistros — FastAPI + Azure SQL

API CRUD para gerenciar a tabela `Sinistros`, construída com **FastAPI** e conectada ao **Azure SQL Database** via **pyodbc**.

## Estrutura

```
Project_darkastronautjefs/
├─ main.py            # Aplicação FastAPI (endpoints CRUD)
├─ db.py              # Conexão pyodbc (driver configurável por env)
├─ requirements.txt   # Dependências
├─ startup.sh         # Startup do Azure App Service (instala ODBC 18 + gunicorn)
├─ .env.example       # Modelo das variáveis de ambiente
├─ .gitignore
└─ scripts/
   ├─ test_db.py                # Testa a conexão com o SQL Azure
   └─ insert_sinistro_teste.py  # Insere registros de teste e faz SELECT
```

## Tabela `Sinistros`

| Coluna | Tipo | Observação |
|---|---|---|
| `ID_Sinistro` | int | IDENTITY (PK) |
| `Numero_Apolice` | varchar | NOT NULL |
| `Data_Ocorrencia` | date | NOT NULL |
| `Valor_Estimado` | decimal | nullable |
| `Status_Processamento` | varchar | default `"new"` |
| `Data_Registro` | datetime | preenchido no INSERT |

## Endpoints

| Método | Rota | Função |
|---|---|---|
| `POST` | `/sinistros` | Criar sinistro (status default `new`) |
| `GET` | `/sinistros` | Listar todos |
| `GET` | `/sinistros/{id}` | Consultar por ID |
| `PATCH` | `/sinistros/{id}` | Atualizar o status |
| `DELETE` | `/sinistros/{id}` | Deletar |
| `GET` | `/health` | Checar conexão com o banco |

## Rodar localmente

1. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
2. Configure as variáveis de ambiente (copie `.env.example` para `.env` e preencha),
   ou exporte-as na sessão. Os nomes esperados:
   `AZURE_SQL_SERVER`, `AZURE_SQL_DATABASE`, `AZURE_SQL_USER`, `AZURE_SQL_PASSWORD`, `AZURE_SQL_DRIVER`.
3. Suba o servidor:
   ```bash
   uvicorn main:app --reload --port 8000
   ```
4. Acesse a documentação interativa: http://127.0.0.1:8000/docs

## Deploy no Azure App Service (Plano F1 Free)

1. Crie um Web App **Linux / Python 3.12**, tier **F1**.
2. Faça o deploy desta pasta (extensão Azure App Service do VS Code).
3. **Startup Command:** `bash startup.sh`
4. **Application Settings:** configure `AZURE_SQL_SERVER`, `AZURE_SQL_DATABASE`,
   `AZURE_SQL_USER`, `AZURE_SQL_PASSWORD`, `AZURE_SQL_DRIVER=ODBC Driver 18 for SQL Server`
   e `SCM_DO_BUILD_DURING_DEPLOYMENT=true`.
5. No SQL Server, habilite **"Allow Azure services to access this server"**.
