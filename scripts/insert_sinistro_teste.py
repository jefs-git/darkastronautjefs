import os
import datetime
import decimal
import pyodbc

TABLE = "Sinistros"

# Status padrao obrigatorio para todo registro gerado
DEFAULT_STATUS = "new"
# Quantidade de registros a inserir
NUM_REGISTROS = 3


def get_connection():
    server = os.getenv("AZURE_SQL_SERVER")
    database = os.getenv("AZURE_SQL_DATABASE")
    username = os.getenv("AZURE_SQL_USER")
    password = os.getenv("AZURE_SQL_PASSWORD")
    driver = "{ODBC Driver 17 for SQL Server}"

    connection_string = (
        f"DRIVER={driver};SERVER={server};DATABASE={database};"
        f"UID={username};PWD={password};"
        "Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
    )
    return pyodbc.connect(connection_string)


def get_columns(cursor):
    """Descobre as colunas da tabela e quais devem ser preenchidas no INSERT."""
    cursor.execute(
        """
        SELECT
            c.COLUMN_NAME,
            c.DATA_TYPE,
            c.IS_NULLABLE,
            c.CHARACTER_MAXIMUM_LENGTH,
            COLUMNPROPERTY(OBJECT_ID(QUOTENAME(c.TABLE_SCHEMA) + '.' + QUOTENAME(c.TABLE_NAME)),
                           c.COLUMN_NAME, 'IsIdentity')   AS is_identity,
            COLUMNPROPERTY(OBJECT_ID(QUOTENAME(c.TABLE_SCHEMA) + '.' + QUOTENAME(c.TABLE_NAME)),
                           c.COLUMN_NAME, 'IsComputed')    AS is_computed
        FROM INFORMATION_SCHEMA.COLUMNS c
        WHERE c.TABLE_NAME = ?
        ORDER BY c.ORDINAL_POSITION
        """,
        TABLE,
    )
    cols = []
    for row in cursor.fetchall():
        cols.append(
            {
                "name": row.COLUMN_NAME,
                "type": row.DATA_TYPE.lower(),
                "nullable": row.IS_NULLABLE == "YES",
                "max_len": row.CHARACTER_MAXIMUM_LENGTH,
                "identity": bool(row.is_identity),
                "computed": bool(row.is_computed),
            }
        )
    return cols


def test_value(col, idx):
    """Gera um valor de teste apropriado ao tipo da coluna.

    idx identifica o registro (1, 2, 3...) para diferenciar os valores.
    A coluna Status_Processamento e sempre forcada para DEFAULT_STATUS.
    """
    t = col["type"]
    now = datetime.datetime(2026, 6, 14, 10, 30, 0)

    # Regra de negocio: Status_Processamento sempre "new" por padrao
    if col["name"].lower() == "status_processamento":
        val = DEFAULT_STATUS
        max_len = col["max_len"]
        return val[:max_len] if (max_len and max_len > 0) else val

    if t in ("int", "smallint", "tinyint", "bigint"):
        return 999
    if t in ("bit",):
        return 1
    if t in ("decimal", "numeric", "money", "smallmoney", "float", "real"):
        return decimal.Decimal("1234.56")
    if t in ("date",):
        return now.date()
    if t in ("datetime", "datetime2", "smalldatetime", "datetimeoffset"):
        return now
    if t in ("time",):
        return now.time()
    if t in ("uniqueidentifier",):
        return "00000000-0000-0000-0000-000000000001"
    # tipos texto (varchar, nvarchar, char, nchar, text, ...)
    base = f"TESTE_{col['name']}_{idx}"
    max_len = col["max_len"]
    if max_len and max_len > 0:
        return base[:max_len]
    return base


def main():
    conn = get_connection()
    conn.autocommit = False
    cursor = conn.cursor()

    cols = get_columns(cursor)
    if not cols:
        print(f"Tabela '{TABLE}' nao encontrada ou sem colunas.")
        conn.close()
        return

    print(f"Colunas detectadas em '{TABLE}':")
    for c in cols:
        flags = []
        if c["identity"]:
            flags.append("IDENTITY")
        if c["computed"]:
            flags.append("COMPUTED")
        if not c["nullable"]:
            flags.append("NOT NULL")
        print(f"  - {c['name']} ({c['type']}) {' '.join(flags)}")

    # Colunas que receberao valor: ignora IDENTITY e COMPUTED
    insert_cols = [c for c in cols if not c["identity"] and not c["computed"]]
    col_names = ", ".join(f"[{c['name']}]" for c in insert_cols)
    placeholders = ", ".join("?" for _ in insert_cols)
    sql = f"INSERT INTO [{TABLE}] ({col_names}) VALUES ({placeholders});"

    print(f"\nInserindo {NUM_REGISTROS} registros (Status_Processamento = '{DEFAULT_STATUS}')...")
    print(sql)
    for idx in range(1, NUM_REGISTROS + 1):
        values = [test_value(c, idx) for c in insert_cols]
        cursor.execute(sql, values)
    conn.commit()
    print(f"{NUM_REGISTROS} registros inseridos com sucesso.\n")

    # SELECT para mostrar o resultado
    print(f"Resultado do SELECT TOP 10 em '{TABLE}':\n")
    cursor.execute(f"SELECT TOP 10 * FROM [{TABLE}] ORDER BY 1 DESC;")
    headers = [d[0] for d in cursor.description]
    rows = cursor.fetchall()

    print(" | ".join(headers))
    print("-" * 80)
    for r in rows:
        print(" | ".join("NULL" if v is None else str(v) for v in r))

    print(f"\nTotal de linhas retornadas: {len(rows)}")
    conn.close()


if __name__ == "__main__":
    main()
