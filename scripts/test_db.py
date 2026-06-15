import os
import pyodbc

def test_azure_sql_connection():
    server = os.getenv('AZURE_SQL_SERVER')
    database = os.getenv('AZURE_SQL_DATABASE')
    username = os.getenv('AZURE_SQL_USER')
    password = os.getenv('AZURE_SQL_PASSWORD')
    driver = '{ODBC Driver 17 for SQL Server}'

    connection_string = f'DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;'

    try:
        conn = pyodbc.connect(connection_string)
        print('Conexão bem-sucedida!')
        conn.close()
    except Exception as e:
        print(f'Erro ao conectar: {e}')

if __name__ == '__main__':
    test_azure_sql_connection()