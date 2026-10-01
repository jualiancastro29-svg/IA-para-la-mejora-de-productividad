"""
api/session_routes.py
-------------------------
Rutas de sesiones de estudio: iniciar, registrar un evento de detección
(esta es la ruta que llama el script de IA en tiempo real), finalizar y
consultar resumen/activa/historial.

Todas requieren un usuario autenticado (no necesariamente admin).
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException

from ..domain.entities import Usuario
from ..schemas.session_schemas import (
    EventoDeteccionCrear,
    ResumenSesionRespuesta,
    SesionRespuesta,
)
from .deps import get_session_service, obtener_usuario_actual
from ..services.session_service import SessionService

router = APIRouter(prefix="/sesiones", tags=["sesiones de estudio"])


@router.post("/iniciar", response_model=SesionRespuesta, status_code=201)
def iniciar_sesion(
    usuario: Usuario = Depends(obtener_usuario_actual),
    session_service: SessionService = Depends(get_session_service),
):
    try:
        return session_service.iniciar_sesion(usuario.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/activa", response_model=SesionRespuesta | None)
def obtener_sesion_activa(
    usuario: Usuario = Depends(obtener_usuario_actual),
    session_service: SessionService = Depends(get_session_service),
):
    return session_service.obtener_sesion_activa(usuario.id)


@router.post("/{sesion_id}/eventos", status_code=201)
def registrar_evento(
    sesion_id: int,
    datos: EventoDeteccionCrear,
    usuario: Usuario = Depends(obtener_usuario_actual),
    session_service: SessionService = Depends(get_session_service),
):
    try:
        evento = session_service.registrar_evento(sesion_id, datos.estado.value, usuario.id)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"ok": True, "evento_id": evento.id}


@router.post("/{sesion_id}/finalizar", response_model=ResumenSesionRespuesta)
def finalizar_sesion(
    sesion_id: int,
    usuario: Usuario = Depends(obtener_usuario_actual),
    session_service: SessionService = Depends(get_session_service),
):
    try:
        return session_service.finalizar_sesion(sesion_id, usuario.id)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{sesion_id}/resumen", response_model=ResumenSesionRespuesta)
def obtener_resumen(
    sesion_id: int,
    usuario: Usuario = Depends(obtener_usuario_actual),
    session_service: SessionService = Depends(get_session_service),
):
    try:
        return session_service.obtener_resumen(sesion_id, usuario.id)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("", response_model=List[SesionRespuesta])
def listar_mis_sesiones(
    usuario: Usuario = Depends(obtener_usuario_actual),
    session_service: SessionService = Depends(get_session_service),
):
    return session_service.listar_sesiones_usuario(usuario.id)
