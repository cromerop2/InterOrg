"""Crea el primer administrador localmente: python -m app.bootstrap_admin.

No existe registro público de administradores. La contraseña se pide sin eco.
Configurar DATABASE_URL y crear antes las tablas con python -m app.create_tables.
"""
from getpass import getpass
from pydantic import ValidationError
from app.database import SessionLocal
from app.models.usuario_model import AdministradorModel
from app.core.enums import RolEnum
from app.core.security import hash_password
from app.schemas.usuario_schema import UsuarioCreate


def main():
    with SessionLocal() as db:
        if db.query(AdministradorModel).first() is not None:
            raise SystemExit("Ya existe un administrador. Use su sesión para crear otros usuarios.")
        try:
            datos = UsuarioCreate(nombre_completo=input("Nombre: "), email=input("Correo: "),
                                  telefono_contacto=input("Teléfono: "), rol=RolEnum.ADMINISTRADOR,
                                  password=getpass("Contraseña (mínimo 8 caracteres): "))
        except ValidationError:
            raise SystemExit("Datos inválidos. Revise nombre, correo, teléfono y contraseña.")
        db.add(AdministradorModel(nombre_completo=datos.nombre_completo, email=datos.email,
                                  telefono_contacto=datos.telefono_contacto, rol=RolEnum.ADMINISTRADOR,
                                  password_hash=hash_password(datos.password), nivel_acceso="Total"))
        db.commit()
        print("Administrador creado.")


if __name__ == "__main__":
    main()
