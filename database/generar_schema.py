"""Genera database/schema.sql (DDL de PostgreSQL) a partir de los modelos.

Uso, desde la carpeta backend con el entorno virtual activado:
    python ../database/generar_schema.py
"""
import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "backend"))
# Solo se necesita metadata; no se abre ninguna conexión real.
os.environ.setdefault("DATABASE_URL", "postgresql+pg8000://u:p@localhost/db")
os.environ.setdefault("SECRET_KEY", "solo-para-generar-sql")

from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateIndex, CreateTable

import app.models  # noqa: F401  (registra los modelos)
from app.database import Base

dialecto = postgresql.dialect()
bloques = ["-- Generado desde los modelos con database/generar_schema.py. No editar a mano.\n"]
for tabla in Base.metadata.sorted_tables:
    bloques.append(str(CreateTable(tabla).compile(dialect=dialecto)).strip() + ";")
    for indice in sorted(tabla.indexes, key=lambda i: i.name or ""):
        bloques.append(str(CreateIndex(indice).compile(dialect=dialecto)).strip() + ";")

salida = RAIZ / "database" / "schema.sql"
salida.write_text("\n\n".join(bloques) + "\n", encoding="utf-8")
print(f"Escrito {salida}")
