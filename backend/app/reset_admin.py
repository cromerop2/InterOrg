"""Recuperación local: desde backend, ejecutar python -m app.reset_admin.

Usa la DATABASE_URL de la terminal, igual que el servidor. No publica ninguna
ruta HTTP para restablecer cuentas y nunca muestra ni recupera la contraseña vieja.
"""
from getpass import getpass

from app.database import SessionLocal
from app.core.security import hash_password
from app.models.usuario_model import AdministradorModel
from app.models.sesion_model import SesionModel


def restablecer_password(db, id_admin: int, nueva_password: str) -> str:
    """Cambia el hash y revoca las sesiones del administrador en una transacción."""
    if not 8 <= len(nueva_password) <= 1024:
        raise ValueError("La contraseña debe tener entre 8 y 1024 caracteres.")
    try:
        admin = db.query(AdministradorModel).filter_by(id=id_admin).with_for_update().first()
        if admin is None:
            raise ValueError("El administrador seleccionado no existe.")
        if not admin.estado_activo:
            raise ValueError("Esta cuenta está inactiva. Requiere reactivación antes de iniciar sesión.")
        admin.password_hash = hash_password(nueva_password)
        db.query(SesionModel).filter_by(usuario_id=admin.id).delete(synchronize_session=False)
        correo = admin.email
        db.commit()
        return correo
    except Exception:
        db.rollback()
        raise


def main():
    """Permite identificar la cuenta por su correo y elegir una nueva contraseña."""
    with SessionLocal() as db:
        administradores = db.query(AdministradorModel).order_by(AdministradorModel.id).all()
        if not administradores:
            raise SystemExit("No hay administradores en esta base. Revise DATABASE_URL o use app.bootstrap_admin.")
        print("Administradores de la base seleccionada:")
        for admin in administradores:
            estado = "activa" if admin.estado_activo else "inactiva"
            print(f"ID {admin.id}: {admin.nombre_completo} | {admin.email} | {estado}")
        try:
            id_admin = int(input("ID del administrador a recuperar: "))
            if id_admin not in {admin.id for admin in administradores}:
                raise ValueError("Seleccione uno de los IDs de la lista.")
            nueva = getpass("Nueva contraseña (mínimo 8 caracteres): ")
            if nueva != getpass("Repita la nueva contraseña: "):
                raise ValueError("Las contraseñas no coinciden. No se guardaron cambios.")
            correo = restablecer_password(db, id_admin, nueva)
        except ValueError as error:
            raise SystemExit(str(error))
        print(f"Contraseña actualizada para {correo}. Sus sesiones anteriores fueron cerradas.")
        print("Inicie sesión en /auth/login con ese correo y su nueva contraseña.")


if __name__ == "__main__":
    main()
