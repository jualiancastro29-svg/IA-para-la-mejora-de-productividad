"""
models/orm_models.py
-----------------------
Modelos de SQLAlchemy (ORM): cómo se ven las tablas en la base de datos.
Esta es la ÚNICA capa que sabe de SQLAlchemy; el dominio (domain/entities.py)
no la conoce. Los repositorios (repositories/) convierten entre estos
modelos ORM y las entidades de dominio.
"""

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Enum as SAEnum, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from ..database import Base
from ..domain.entities import EstadoDeteccion, RolUsuario


class UsuarioORM(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    nombre_completo = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    rol = Column(SAEnum(RolUsuario), nullable=False, default=RolUsuario.USUARIO)
    activo = Column(Boolean, default=True, nullable=False)
    creado_en = Column(DateTime, default=datetime.utcnow)

    sesiones = relationship("SesionEstudioORM", back_populates="usuario")


class SesionEstudioORM(Base):
    __tablename__ = "sesiones_estudio"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    iniciada_en = Column(DateTime, default=datetime.utcnow)
    finalizada_en = Column(DateTime, nullable=True)
    activa = Column(Boolean, default=True, nullable=False)

    usuario = relationship("UsuarioORM", back_populates="sesiones")
    eventos = relationship("EventoDeteccionORM", back_populates="sesion", cascade="all, delete-orphan")


class EventoDeteccionORM(Base):
    __tablename__ = "eventos_deteccion"

    id = Column(Integer, primary_key=True, index=True)
    sesion_id = Column(Integer, ForeignKey("sesiones_estudio.id"), nullable=False)
    estado = Column(SAEnum(EstadoDeteccion), nullable=False)
    detectado_en = Column(DateTime, default=datetime.utcnow)

    sesion = relationship("SesionEstudioORM", back_populates="eventos")
