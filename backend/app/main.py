from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi import Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
# Importa los grupos de endpoints que se registran en la aplicación.
from app.database import Base, engine
# Importar app.models registra todas las tablas en Base.metadata.
from app import models  # noqa: F401
from app.routers import (
    auth_router,
    cancha_router,
    colegio_router,
    fase_router,
    torneo_router,
    usuario_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Al arrancar el servidor crea las tablas que aún no existan (no modifica las existentes)."""
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="API Torneo Colegial",
    description="Backend en FastAPI para la gestión del Torneo Colegial",
    version="1.0.0",
    lifespan=lifespan,
)


# Configuración de CORS para conectar con el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Habilita cualquier origen durante desarrollo
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(usuario_router.router)
# Registra /colegios antes del frontend para que FastAPI atienda estas rutas.
app.include_router(colegio_router.router)
app.include_router(cancha_router.router)
app.include_router(torneo_router.router)
app.include_router(fase_router.router)

@app.get("/diagrama")
def ver_diagrama():
  return FileResponse("../frontend/diagrama.html")

app.mount("/", StaticFiles(directory="../frontend", html=True), name="frontend")
