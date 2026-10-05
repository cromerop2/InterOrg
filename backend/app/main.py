from fastapi import FastAPI
from fastapi import Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from app.routers import usuario_router

app = FastAPI(
    title="API Torneo Colegial",
    description="Backend en FastAPI para la gestión del Torneo Colegial",
    version="1.0.0"
)


# Configuración de CORS para conectar con el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Habilita cualquier origen durante desarrollo
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(usuario_router.router)

@app.get("/diagrama")
def ver_diagrama():
  return FileResponse("../frontend/diagrama.html")

app.mount("/", StaticFiles(directory="../frontend", html=True), name="frontend")
