"""API CRUD de Sinistros (FastAPI + SQL Azure via pyodbc).

Tabela Sinistros:
    ID_Sinistro          int IDENTITY (PK)
    Numero_Apolice       varchar  NOT NULL
    Data_Ocorrencia      date     NOT NULL
    Valor_Estimado       decimal  NULL
    Status_Processamento varchar  NULL  (default "new")
    Data_Registro        datetime NULL
"""
import datetime
from decimal import Decimal
from typing import Optional

import pyodbc
from fastapi import Depends, FastAPI, HTTPException, status
from pydantic import BaseModel, Field

from db import get_db

app = FastAPI(
    title="API de Sinistros",
    description="CRUD de sinistros sobre SQL Azure.",
    version="1.0.0",
)

# Status padrao para novos registros
DEFAULT_STATUS = "new"


# ----------------------- Schemas (Pydantic) -----------------------
class SinistroBase(BaseModel):
    Numero_Apolice: str = Field(..., max_length=255, examples=["APOL-2026-001"])
    Data_Ocorrencia: datetime.date = Field(..., examples=["2026-06-14"])
    Valor_Estimado: Optional[Decimal] = Field(None, examples=[1234.56])


class SinistroCreate(SinistroBase):
    # Opcional na entrada; se omitido assume DEFAULT_STATUS ("new")
    Status_Processamento: Optional[str] = Field(None, max_length=50)


class StatusUpdate(BaseModel):
    Status_Processamento: str = Field(..., max_length=50, examples=["processing"])


class Sinistro(SinistroBase):
    ID_Sinistro: int
    Status_Processamento: Optional[str] = None
    Data_Registro: Optional[datetime.datetime] = None


# ----------------------- Helpers -----------------------
def row_to_sinistro(row) -> Sinistro:
    return Sinistro(
        ID_Sinistro=row.ID_Sinistro,
        Numero_Apolice=row.Numero_Apolice,
        Data_Ocorrencia=row.Data_Ocorrencia,
        Valor_Estimado=row.Valor_Estimado,
        Status_Processamento=row.Status_Processamento,
        Data_Registro=row.Data_Registro,
    )


SELECT_FIELDS = (
    "ID_Sinistro, Numero_Apolice, Data_Ocorrencia, "
    "Valor_Estimado, Status_Processamento, Data_Registro"
)


def fetch_one(conn, sinistro_id: int):
    cur = conn.cursor()
    cur.execute(
        f"SELECT {SELECT_FIELDS} FROM Sinistros WHERE ID_Sinistro = ?",
        sinistro_id,
    )
    return cur.fetchone()


# ----------------------- Endpoints -----------------------
@app.get("/health", tags=["infra"])
def health(conn: pyodbc.Connection = Depends(get_db)):
    conn.cursor().execute("SELECT 1")
    return {"status": "ok"}


@app.post(
    "/sinistros",
    response_model=Sinistro,
    status_code=status.HTTP_201_CREATED,
    tags=["sinistros"],
)
def criar_sinistro(
    payload: SinistroCreate, conn: pyodbc.Connection = Depends(get_db)
):
    status_proc = payload.Status_Processamento or DEFAULT_STATUS
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO Sinistros
            (Numero_Apolice, Data_Ocorrencia, Valor_Estimado,
             Status_Processamento, Data_Registro)
        OUTPUT INSERTED.ID_Sinistro
        VALUES (?, ?, ?, ?, ?)
        """,
        payload.Numero_Apolice,
        payload.Data_Ocorrencia,
        payload.Valor_Estimado,
        status_proc,
        datetime.datetime.now(),
    )
    new_id = cur.fetchone()[0]
    conn.commit()
    return row_to_sinistro(fetch_one(conn, new_id))


@app.get("/sinistros", response_model=list[Sinistro], tags=["sinistros"])
def listar_sinistros(conn: pyodbc.Connection = Depends(get_db)):
    cur = conn.cursor()
    cur.execute(f"SELECT {SELECT_FIELDS} FROM Sinistros ORDER BY ID_Sinistro DESC")
    return [row_to_sinistro(r) for r in cur.fetchall()]


@app.get("/sinistros/{sinistro_id}", response_model=Sinistro, tags=["sinistros"])
def obter_sinistro(
    sinistro_id: int, conn: pyodbc.Connection = Depends(get_db)
):
    row = fetch_one(conn, sinistro_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Sinistro nao encontrado")
    return row_to_sinistro(row)


@app.patch(
    "/sinistros/{sinistro_id}", response_model=Sinistro, tags=["sinistros"]
)
def atualizar_status(
    sinistro_id: int,
    payload: StatusUpdate,
    conn: pyodbc.Connection = Depends(get_db),
):
    cur = conn.cursor()
    cur.execute(
        "UPDATE Sinistros SET Status_Processamento = ? WHERE ID_Sinistro = ?",
        payload.Status_Processamento,
        sinistro_id,
    )
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="Sinistro nao encontrado")
    conn.commit()
    return row_to_sinistro(fetch_one(conn, sinistro_id))


@app.delete(
    "/sinistros/{sinistro_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["sinistros"],
)
def deletar_sinistro(
    sinistro_id: int, conn: pyodbc.Connection = Depends(get_db)
):
    cur = conn.cursor()
    cur.execute("DELETE FROM Sinistros WHERE ID_Sinistro = ?", sinistro_id)
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="Sinistro nao encontrado")
    conn.commit()
    return None
