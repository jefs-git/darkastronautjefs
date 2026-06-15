#!/usr/bin/env bash
set -e

# 1) Garante o Microsoft ODBC Driver 18 no container.
#    O blessed image Python do App Service Linux NAO inclui o driver,
#    entao instalamos de forma idempotente no boot do container.
if ! odbcinst -q -d 2>/dev/null | grep -q "ODBC Driver 18 for SQL Server"; then
  echo ">> Instalando msodbcsql18..."
  . /etc/os-release
  curl -fsSL https://packages.microsoft.com/keys/microsoft.asc \
       -o /etc/apt/trusted.gpg.d/microsoft.asc
  curl -fsSL "https://packages.microsoft.com/config/debian/${VERSION_ID}/prod.list" \
       -o /etc/apt/sources.list.d/mssql-release.list
  apt-get update -y
  ACCEPT_EULA=Y apt-get install -y msodbcsql18 unixodbc-dev
fi

# 2) Sobe a API. F1 (Free) tem pouca CPU/RAM -> poucos workers.
#    O App Service espera a aplicacao na porta 8000.
exec gunicorn -w 2 -k uvicorn.workers.UvicornWorker \
     --bind=0.0.0.0:8000 --timeout 120 main:app
