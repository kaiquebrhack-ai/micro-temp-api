import os
from datetime import datetime, timezone
from typing import List, Optional

import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

app = FastAPI(title="Micro Temperatura API")

# ----- CONFIG DB via VARIÁVEIS DE AMBIENTE -----
DB_HOST = os.environ.get("PGHOST")
DB_PORT = os.environ.get("PGPORT", "5432")
DB_NAME = os.environ.get("PGDATABASE")
DB_USER = os.environ.get("PGUSER")
DB_PASS = os.environ.get("PGPASSWORD")


def get_conn():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
    )


def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS leituras (
            id SERIAL PRIMARY KEY,
            device_id VARCHAR(50) NOT NULL,
            temperatura NUMERIC(6,2) NOT NULL,
            criado_em TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """
    )
    conn.commit()
    cur.close()
    conn.close()


@app.on_event("startup")
def startup_event():
    # cria a tabela se não existir
    init_db()


class LeituraIn(BaseModel):
    device_id: str
    temperatura: float


class LeituraOut(BaseModel):
    device_id: str
    temperatura: float
    criado_em: datetime


@app.get("/")
def health():
    return {"status": "ok", "msg": "API micro-temperatura ativa"}


@app.post("/temperatura")
def receber_temperatura(dados: LeituraIn):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO leituras (device_id, temperatura, criado_em)
        VALUES (%s, %s, %s)
        """,
        (dados.device_id, dados.temperatura, datetime.now(timezone.utc)),
    )
    conn.commit()
    cur.close()
    conn.close()
    return {"status": "ok"}


@app.get("/ultima", response_model=LeituraOut)
def ultima(device_id: str = Query(...)):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute(
        """
        SELECT device_id, temperatura, criado_em
        FROM leituras
        WHERE device_id = %s
        ORDER BY criado_em DESC
        LIMIT 1
        """,
        (device_id,),
    )
    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Sem dados para esse device_id")

    return row


@app.get("/historico", response_model=List[LeituraOut])
def historico(
    device_id: str = Query(...),
    limite: int = Query(100, ge=1, le=1000),
):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute(
        """
        SELECT device_id, temperatura, criado_em
        FROM leituras
        WHERE device_id = %s
        ORDER BY criado_em DESC
        LIMIT %s
        """,
        (device_id, limite),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

