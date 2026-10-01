"""
domain/entities.py
--------------------
Entidades del dominio del negocio, sin ninguna dependencia de FastAPI,
SQLAlchemy ni nada externo. Son "objetos de Python puros" (dataclasses).

Esto es clave para SOLID: el dominio no sabe cómo se guarda en base de
datos ni cómo se expone por HTTP. Esas son decisiones de infraestructura
que viven en otras capas (models/, repositories/, api/).
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class RolUsuario(str, Enum):
    ADMIN = "admin"
    USUARIO = "usuario"


class EstadoDeteccion(str, Enum):
    """Debe coincidir EXACTAMENTE con las etiquetas que produce el modelo
    de IA (ver ai_detection/detector_interface.py -> ESTADOS_VALIDOS).
    Si el encargado de IA agrega o renombra un estado, este Enum es el
    único lugar del backend que hay que actualizar."""
    CONCENTRADO = "Concentrado"
    DISTRAIDO = "Distraido"
    DORMIDO = "Dormido"
    SOMNOLIENTO = "Somnoliento"
    REVISANDO_TELEFONO = "RevisandoTelefono"
    ESCRIBIENDO = "Escribiendo"
    LEYENDO = "Leyendo"
    HABLANDO_CON_OTRA_PERSONA = "HablandoConOtraPersona"
    AUSENTE = "Ausente"


@dataclass
class Usuario:
    id: Optional[int]
    username: str
    nombre_completo: str
    password_hash: str
    rol: RolUsuario
    activo: bool = True
    creado_en: datetime = field(default_factory=datetime.utcnow)


@dataclass
class SesionEstudio:
    id: Optional[int]
    usuario_id: int
    iniciada_en: datetime
    finalizada_en: Optional[datetime] = None
    activa: bool = True


@dataclass
class EventoDeteccion:
    id: Optional[int]
    sesion_id: int
    estado: EstadoDeteccion
    detectado_en: datetime = field(default_factory=datetime.utcnow)
