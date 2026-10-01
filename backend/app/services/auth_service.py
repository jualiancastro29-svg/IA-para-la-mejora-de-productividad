"""
services/auth_service.py
---------------------------
Responsable ÚNICAMENTE de autenticar usuarios y registrar nuevas cuentas
(Principio de Responsabilidad Única). No sabe nada de HTTP ni de rutas:
eso vive en api/auth_routes.py, que solo llama a este servicio.

Depende de IUserRepository (la interfaz), no de una implementación
concreta -> se le puede inyectar cualquier repositorio que cumpla el
contrato (Inversión de Dependencias).
"""

from typing import Optional

from ..domain.entities import RolUsuario, Usuario
from ..domain.interfaces import IUserRepository
from ..security import crear_token_acceso, hash_password, verificar_password


class AuthService:

    def __init__(self, user_repo: IUserRepository):
        self.user_repo = user_repo

    def registrar(self, username: str, password: str, nombre_completo: str) -> Usuario:
        if self.user_repo.obtener_por_username(username):
            raise ValueError("Ese nombre de usuario ya está en uso")

        nuevo_usuario = Usuario(
            id=None,
            username=username,
            nombre_completo=nombre_completo,
            password_hash=hash_password(password),
            rol=RolUsuario.USUARIO,  # el auto-registro SIEMPRE crea usuarios normales,
            activo=True,             # nunca administradores (ver user_service.py para eso)
        )
        return self.user_repo.crear(nuevo_usuario)

    def autenticar(self, username: str, password: str) -> Optional[str]:
        """Devuelve un token JWT si las credenciales son correctas y la
        cuenta está activa, o None si no."""
        usuario = self.user_repo.obtener_por_username(username)
        if not usuario or not usuario.activo:
            return None
        if not verificar_password(password, usuario.password_hash):
            return None

        return crear_token_acceso({"sub": usuario.username, "rol": usuario.rol.value, "uid": usuario.id})
