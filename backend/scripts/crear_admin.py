"""Crea el primer Administrador (necesario para iniciar sesión y crear las demás cuentas).

Uso, desde la carpeta backend con el entorno virtual activado:
    python scripts/crear_admin.py
"""
import sys
from getpass import getpass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi import HTTPException
from pydantic import ValidationError

from app import models  # noqa: F401  (registra las tablas)
from app.database import Base, SessionLocal, engine
from app.repositories.colegio_repository import ColegioRepository
from app.repositories.usuario_repository import UsuarioRepository
from app.schemas.usuario_schema import AdministradorCreate
from app.services.usuario_service import UsuarioService


def main() -> None:
    Base.metadata.create_all(bind=engine)

    nombre = input("Nombre completo: ").strip()
    email = input("Correo: ").strip()
    telefono = input("Teléfono de contacto: ").strip()
    password = getpass("Contraseña (8 a 72 caracteres): ")
    if password != getpass("Repite la contraseña: "):
        sys.exit("Las contraseñas no coinciden.")

    try:
        datos = AdministradorCreate(
            rol="Administrador",
            nombre_completo=nombre,
            email=email,
            telefono_contacto=telefono,
            password=password,
        )
    except ValidationError as error:
        sys.exit(f"Datos inválidos:\n{error}")

    with SessionLocal() as db:
        servicio = UsuarioService(UsuarioRepository(db), ColegioRepository(db))
        try:
            admin = servicio.registrar_usuario(datos)
        except HTTPException as error:
            sys.exit(f"No se pudo crear: {error.detail}")
    print(f"Administrador creado: id={admin.id}, correo={admin.email}")


if __name__ == "__main__":
    main()
