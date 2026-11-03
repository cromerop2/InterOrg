"""Servidor de integración visual con BD temporal; no utiliza la BD del usuario."""
import os
from pathlib import Path
import sys
import threading
import time

os.environ["DATABASE_URL"] = "sqlite:///" + Path(sys.argv[1]).resolve().as_posix()
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from app.database import Base, engine, SessionLocal
from app.main import app
from app.core.enums import RolEnum
from app.core.security import hash_password
from app.models.usuario_model import AdministradorModel
import uvicorn

Base.metadata.create_all(engine)
with SessionLocal() as db:
    db.add(AdministradorModel(nombre_completo="Admin de prueba visual", email="admin@example.com",
        telefono_contacto="3001234567", rol=RolEnum.ADMINISTRADOR,
        password_hash=hash_password("PruebaNavegador123!")))
    db.commit()
server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=int(sys.argv[2]), log_level="warning"))
def observar_cierre():
    while not Path(sys.argv[3]).exists():
        time.sleep(0.1)
    server.should_exit = True
threading.Thread(target=observar_cierre, daemon=True).start()
try:
    server.run()
finally:
    engine.dispose()
