"""
api/user_routes.py
---------------------
Rutas de administración de usuarios. TODAS protegidas con requerir_admin:
solo un usuario con rol "admin" puede listar, crear, activar/desactivar
o cambiar el rol de otros usuarios.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import List

from ..domain.entities import Usuario
from ..schemas.user_schemas import (
    UsuarioActualizarEstado,
    UsuarioActualizarRol,
    UsuarioCrearAdmin,
    UsuarioRespuesta,
)
from .deps import get_user_service, requerir_admin
from ..services.user_service import UserService

router = APIRouter(prefix="/admin/usuarios", tags=["administración de usuarios"])


@router.get("", response_model=List[UsuarioRespuesta])
def listar_usuarios(
    _admin: Usuario = Depends(requerir_admin),
    user_service: UserService = Depends(get_user_service),
):
    return user_service.listar_usuarios()


@router.post("", response_model=UsuarioRespuesta, status_code=201)
def crear_usuario(
    datos: UsuarioCrearAdmin,
    _admin: Usuario = Depends(requerir_admin),
    user_service: UserService = Depends(get_user_service),
):
    try:
        return user_service.crear_usuario(datos.username, datos.password, datos.nombre_completo, datos.rol)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{usuario_id}/estado", response_model=UsuarioRespuesta)
def cambiar_estado_activo(
    usuario_id: int,
    datos: UsuarioActualizarEstado,
    _admin: Usuario = Depends(requerir_admin),
    user_service: UserService = Depends(get_user_service),
):
    try:
        return user_service.cambiar_estado_activo(usuario_id, datos.activo)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/{usuario_id}/rol", response_model=UsuarioRespuesta)
def cambiar_rol(
    usuario_id: int,
    datos: UsuarioActualizarRol,
    _admin: Usuario = Depends(requerir_admin),
    user_service: UserService = Depends(get_user_service),
):
    try:
        return user_service.cambiar_rol(usuario_id, datos.rol)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
