"""
repositories/user_repository.py
----------------------------------
Implementación concreta de IUserRepository usando SQLAlchemy. El resto
de la aplicación (services/) depende de la interfaz IUserRepository, no
de esta clase directamente — esto es lo que permite, por ejemplo,
reemplazarla en pruebas unitarias por una versión en memoria sin tocar
ni una línea de services/.
"""

from typing import List, Optional

from sqlalchemy.orm import Session

from ..domain.entities import Usuario
from ..domain.interfaces import IUserRepository
from ..models.orm_models import UsuarioORM


class SQLAlchemyUserRepository(IUserRepository):

    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _a_entidad(orm: UsuarioORM) -> Usuario:
        return Usuario(
            id=orm.id,
            username=orm.username,
            nombre_completo=orm.nombre_completo,
            password_hash=orm.password_hash,
            rol=orm.rol,
            activo=orm.activo,
            creado_en=orm.creado_en,
        )

    def obtener_por_id(self, user_id: int) -> Optional[Usuario]:
        orm = self.db.query(UsuarioORM).filter(UsuarioORM.id == user_id).first()
        return self._a_entidad(orm) if orm else None

    def obtener_por_username(self, username: str) -> Optional[Usuario]:
        orm = self.db.query(UsuarioORM).filter(UsuarioORM.username == username).first()
        return self._a_entidad(orm) if orm else None

    def listar(self) -> List[Usuario]:
        return [self._a_entidad(o) for o in self.db.query(UsuarioORM).order_by(UsuarioORM.id).all()]

    def crear(self, usuario: Usuario) -> Usuario:
        orm = UsuarioORM(
            username=usuario.username,
            nombre_completo=usuario.nombre_completo,
            password_hash=usuario.password_hash,
            rol=usuario.rol,
            activo=usuario.activo,
        )
        self.db.add(orm)
        self.db.commit()
        self.db.refresh(orm)
        return self._a_entidad(orm)

    def actualizar(self, usuario: Usuario) -> Usuario:
        orm = self.db.query(UsuarioORM).filter(UsuarioORM.id == usuario.id).first()
        if not orm:
            raise ValueError("Usuario no encontrado")

        orm.nombre_completo = usuario.nombre_completo
        orm.rol = usuario.rol
        orm.activo = usuario.activo
        if usuario.password_hash:
            orm.password_hash = usuario.password_hash

        self.db.commit()
        self.db.refresh(orm)
        return self._a_entidad(orm)
