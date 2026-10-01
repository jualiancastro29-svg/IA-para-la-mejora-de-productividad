"""
api/auth_routes.py
---------------------
Rutas de autenticación: registro (auto-registro, siempre como usuario
normal), login (devuelve JWT) y "quién soy".
"""

from fastapi import APIRouter, Depends, HTTPException

from ..schemas.user_schemas import LoginRequest, TokenRespuesta, UsuarioRegistro, UsuarioRespuesta
from ..domain.entities import Usuario
from .deps import get_auth_service, obtener_usuario_actual
from ..services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["autenticación"])


@router.post("/register", response_model=UsuarioRespuesta, status_code=201)
def registrar(datos: UsuarioRegistro, auth_service: AuthService = Depends(get_auth_service)):
    try:
        usuario = auth_service.registrar(datos.username, datos.password, datos.nombre_completo)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return usuario


@router.post("/login", response_model=TokenRespuesta)
def login(datos: LoginRequest, auth_service: AuthService = Depends(get_auth_service)):
    token = auth_service.autenticar(datos.username, datos.password)
    if not token:
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos, o cuenta inactiva")
    return TokenRespuesta(access_token=token)


@router.get("/me", response_model=UsuarioRespuesta)
def quien_soy(usuario: Usuario = Depends(obtener_usuario_actual)):
    return usuario
