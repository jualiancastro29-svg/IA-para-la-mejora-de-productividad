"""
schemas/user_schemas.py
---------------------------
Esquemas Pydantic: definen la forma exacta de los JSON que entran y
salen de la API relacionada a usuarios. Son distintos de domain/entities.py
a propósito: las entidades son el modelo interno del negocio, los
schemas son el "contrato público" de la API (por ejemplo, nunca se
devuelve password_hash en una respuesta).
"""

from datetime import datetime

from pydantic import BaseModel, Field

from ..domain.entities import RolUsuario


class UsuarioRegistro(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6)
    nombre_completo: str = Field(min_length=1, max_length=150)


class UsuarioCrearAdmin(UsuarioRegistro):
    rol: RolUsuario = RolUsuario.USUARIO


class UsuarioActualizarEstado(BaseModel):
    activo: bool


class UsuarioActualizarRol(BaseModel):
    rol: RolUsuario


class UsuarioRespuesta(BaseModel):
    id: int
    username: str
    nombre_completo: str
    rol: RolUsuario
    activo: bool
    creado_en: datetime

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenRespuesta(BaseModel):
    access_token: str
    token_type: str = "bearer"
