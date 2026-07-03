"""Conexao com o SQL Azure via pyodbc (mesmas variaveis de ambiente do projeto)."""
import os
import time

import pyodbc

# Driver ODBC configuravel por ambiente:
#   - Local (Windows): "ODBC Driver 17 for SQL Server" (default)
#   - Azure App Service (Linux): defina AZURE_SQL_DRIVER="ODBC Driver 18 for SQL Server"
DRIVER = os.getenv("AZURE_SQL_DRIVER", "ODBC Driver 17 for SQL Server")

# Timeout de conexao (s). O banco free/serverless auto-pausa por inatividade e
# leva ~25-60s para retomar, entao o default precisa ser folgado.
CONNECT_TIMEOUT = int(os.getenv("AZURE_SQL_CONNECT_TIMEOUT", "60"))

# Retry para o cold-start do serverless: a 1a conexao com o banco pausado
# falha com "HYT00 Login timeout expired" enquanto ele acorda.
CONNECT_RETRIES = int(os.getenv("AZURE_SQL_CONNECT_RETRIES", "3"))
RETRY_BACKOFF_SECONDS = float(os.getenv("AZURE_SQL_RETRY_BACKOFF", "5"))

# SQLSTATEs transientes que justificam retry (timeout/indisponibilidade);
# erros como senha invalida (28000) NAO entram aqui para nao insistir a toa.
_TRANSIENT_SQLSTATES = {"HYT00", "HYT01", "08001", "08S01", "40197", "40501", "40613"}


def get_connection_string() -> str:
    server = os.getenv("AZURE_SQL_SERVER")
    database = os.getenv("AZURE_SQL_DATABASE")
    username = os.getenv("AZURE_SQL_USER")
    password = os.getenv("AZURE_SQL_PASSWORD")

    missing = [
        name
        for name, val in {
            "AZURE_SQL_SERVER": server,
            "AZURE_SQL_DATABASE": database,
            "AZURE_SQL_USER": username,
            "AZURE_SQL_PASSWORD": password,
        }.items()
        if not val
    ]
    if missing:
        raise RuntimeError(
            "Variaveis de ambiente faltando: " + ", ".join(missing)
        )

    return (
        f"DRIVER={{{DRIVER}}};SERVER={server};DATABASE={database};"
        f"UID={username};PWD={password};"
        f"Encrypt=yes;TrustServerCertificate=no;Connection Timeout={CONNECT_TIMEOUT};"
    )


def get_connection() -> pyodbc.Connection:
    """Abre a conexao, com retry para o cold-start do SQL serverless.

    O banco free/serverless auto-pausa apos inatividade; a 1a conexao pode
    falhar com "HYT00 Login timeout expired" enquanto o banco retoma. Tentamos
    de novo (com backoff) apenas para erros transientes.
    """
    conn_str = get_connection_string()
    last_error = None
    for attempt in range(1, CONNECT_RETRIES + 1):
        try:
            return pyodbc.connect(conn_str, timeout=CONNECT_TIMEOUT)
        except pyodbc.Error as exc:
            sqlstate = exc.args[0] if exc.args else None
            if sqlstate not in _TRANSIENT_SQLSTATES or attempt == CONNECT_RETRIES:
                raise
            last_error = exc
            time.sleep(RETRY_BACKOFF_SECONDS * attempt)
    # Inalcancavel (o loop ou retorna ou re-levanta), mas mantem o tipo coerente.
    raise last_error


def get_db():
    """Dependency do FastAPI: abre e fecha a conexao por requisicao."""
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()
