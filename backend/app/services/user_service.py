"""
services/user_service.py
---------------------------
Casos de uso de administración de usuarios: listar, crear (con rol
elegido por el admin), activar/desactivar y cambiar de rol. Solo debe
invocarse desde rutas protegidas para administradores
(ver api/deps.py -> requerir_admin).
"""

from typing import List

from ..domain.entities import RolUsuario, Usuario
from ..domain.interfaces import IUserRepository
from ..security import hash_password


class UserService:

    def __init__(self, user_repo: IUserRepository):
        self.user_repo = user_repo

    def listar_usuarios(self) -> List[Usuario]:
        return self.user_repo.listar()

    def crear_usuario(self, username: str, password: str, nombre_completo: str, rol: RolUsuario) -> Usuario:
        if self.user_repo.obtener_por_username(username):
            raise ValueError("Ese nombre de usuario ya está en uso")

        usuario = Usuario(
            id=None,
            username=username,
            nombre_completo=nombre_completo,
            password_hash=hash_password(password),
            rol=rol,
            activo=True,
        )
        return self.user_repo.crear(usuario)

    def cambiar_estado_activo(self, user_id: int, activo: bool) -> Usuario:
        usuario = self.user_repo.obtener_por_id(user_id)
        if not usuario:
            raise ValueError("Usuario no encontrado")
        usuario.activo = activo
        return self.user_repo.actualizar(usuario)

    def cambiar_rol(self, user_id: int, rol: RolUsuario) -> Usuario:
        usuario = self.user_repo.obtener_por_id(user_id)
        if not usuario:
            raise ValueError("Usuario no encontrado")
        usuario.rol = rol
        return self.user_repo.actualizar(usuario)
