import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# 2. Crear el motor de SQLAlchemy (Engine)
engine = create_engine(DATABASE_URL)

# 3. Crear la fábrica de sesiones de base de datos
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. Clase base de la que heredarán todos los modelos de SQLAlchemy
Base = declarative_base()


# 5. Generador de sesiones para la inyección de dependencias en FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()