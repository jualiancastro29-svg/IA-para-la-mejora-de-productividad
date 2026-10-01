"""
api/deps.py
-------------
Dependencias de FastAPI reutilizables en todas las rutas:
  - get_db: sesión de base de datos por request.
  - obtener_usuario_actual: decodifica el JWT y devuelve el usuario.
  - requerir_admin: igual que la anterior, pero además exige rol admin.
  - fábricas de servicios (get_auth_service, get_user_service, etc.) que
    arman cada servicio con sus dependencias concretas (repositorios),
    cumpliendo Inversión de Dependencias: las rutas piden "un AuthService"
    sin saber qué repositorio hay detrás.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from ..database import get_db
from ..domain.entities import RolUsuario, Usuario
from ..repositories.session_repository import SQLAlchemySessionRepository
from ..repositories.user_repository import SQLAlchemyUserRepository
from ..security import decodificar_token
from ..services.auth_service import AuthService
from ..services.recommendation_service import RecommendationService
from ..services.session_service import SessionService
from ..services.user_service import UserService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(SQLAlchemyUserRepository(db))


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    return UserService(SQLAlchemyUserRepository(db))


def get_session_service(db: Session = Depends(get_db)) -> SessionService:
    return SessionService(SQLAlchemySessionRepository(db), RecommendationService())


def obtener_usuario_actual(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Usuario:
    credenciales_invalidas = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar la sesión",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decodificar_token(token)
    if payload is None:
        raise credenciales_invalidas

    username = payload.get("sub")
    if username is None:
        raise credenciales_invalidas

    repo = SQLAlchemyUserRepository(db)
    usuario = repo.obtener_por_username(username)
    if usuario is None or not usuario.activo:
        raise credenciales_invalidas

    return usuario


def requerir_admin(usuario: Usuario = Depends(obtener_usuario_actual)) -> Usuario:
    if usuario.rol != RolUsuario.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Se requiere rol de administrador")
    return usuario
