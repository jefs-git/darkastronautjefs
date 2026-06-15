"""Conexao com o SQL Azure via pyodbc (mesmas variaveis de ambiente do projeto)."""
import os
import pyodbc

# Driver ODBC configuravel por ambiente:
#   - Local (Windows): "ODBC Driver 17 for SQL Server" (default)
#   - Azure App Service (Linux): defina AZURE_SQL_DRIVER="ODBC Driver 18 for SQL Server"
DRIVER = os.getenv("AZURE_SQL_DRIVER", "ODBC Driver 17 for SQL Server")


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
        "Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
    )


def get_connection() -> pyodbc.Connection:
    return pyodbc.connect(get_connection_string())


def get_db():
    """Dependency do FastAPI: abre e fecha a conexao por requisicao."""
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()
