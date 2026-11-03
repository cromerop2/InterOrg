"""Confirma cada operación completa y revierte también errores de validación."""
from functools import wraps
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError


def transaccion(funcion):
    @wraps(funcion)
    def ejecutar(self, *args, **kwargs):
        try:
            resultado = funcion(self, *args, **kwargs)
            self.repository.db.commit()
            return resultado
        except IntegrityError as error:
            self.repository.db.rollback()
            raise HTTPException(409, "La operación entra en conflicto con datos ya registrados.") from error
        except Exception:
            self.repository.db.rollback()
            raise
    return ejecutar
