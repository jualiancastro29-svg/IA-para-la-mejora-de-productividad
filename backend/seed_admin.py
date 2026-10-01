"""
seed_admin.py
---------------
Script de un solo uso: crea el usuario administrador inicial a partir de
las variables ADMIN_USERNAME / ADMIN_PASSWORD / ADMIN_NOMBRE del .env (o
sus valores por defecto si no se configuran). Si el usuario ya existe,
no hace nada (seguro de ejecutar más de una vez).

CÓMO EJECUTARLO (desde la carpeta backend/, una sola vez al preparar el
proyecto):
    python seed_admin.py
"""

from app.config import settings
from app.database import Base, SessionLocal, engine
from app.domain.entities import RolUsuario
from app.repositories.user_repository import SQLAlchemyUserRepository
from app.security import hash_password

Base.metadata.create_all(bind=engine)


def main():
    db = SessionLocal()
    try:
        repo = SQLAlchemyUserRepository(db)
        existente = repo.obtener_por_username(settings.ADMIN_USERNAME)
        if existente:
            print(f"El usuario administrador '{settings.ADMIN_USERNAME}' ya existe. No se hizo nada.")
            return

        from app.domain.entities import Usuario
        admin = Usuario(
            id=None,
            username=settings.ADMIN_USERNAME,
            nombre_completo=settings.ADMIN_NOMBRE,
            password_hash=hash_password(settings.ADMIN_PASSWORD),
            rol=RolUsuario.ADMIN,
            activo=True,
        )
        repo.crear(admin)
        print(f"Usuario administrador '{settings.ADMIN_USERNAME}' creado correctamente.")
        print("IMPORTANTE: cambia ADMIN_PASSWORD en tu .env antes de desplegar en producción.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
