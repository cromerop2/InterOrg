from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import settings

# 1. Crear el motor de SQLAlchemy (Engine)
# pool_pre_ping descarta conexiones caídas (útil con bases remotas como Supabase).
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)

# 2. Crear la fábrica de sesiones de base de datos
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 3. Clase base de la que heredarán todos los modelos de SQLAlchemy
Base = declarative_base()


# 4. Generador de sesiones para la inyección de dependencias en FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
