"""Desde backend: python -m app.create_tables. No borra ni altera tablas existentes."""
from app.database import Base, engine
import app.models


def crear_tablas():
    Base.metadata.create_all(engine, checkfirst=True)


if __name__ == "__main__":
    crear_tablas()
    print("Se crearon las tablas que faltaban.")
