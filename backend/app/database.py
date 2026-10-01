"""
database.py
-------------
Configura el motor de base de datos y la fábrica de sesiones de
SQLAlchemy. Usa SQLite por defecto (un solo archivo app.db, sin
necesidad de instalar un servidor de base de datos aparte), pero basta
con cambiar DATABASE_URL en .env para apuntar a PostgreSQL/MySQL el día
que el proyecto lo necesite.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from .config import settings

connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependencia de FastAPI: abre una sesión de BD por request y la
    cierra siempre al terminar, incluso si hubo una excepción."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
