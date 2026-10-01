"""
schemas/session_schemas.py
-------------------------------
Esquemas Pydantic para sesiones de estudio y eventos de detección.
"""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel

from ..domain.entities import EstadoDeteccion


class SesionRespuesta(BaseModel):
    id: int
    usuario_id: int
    iniciada_en: datetime
    finalizada_en: Optional[datetime] = None
    activa: bool

    class Config:
        from_attributes = True


class EventoDeteccionCrear(BaseModel):
    estado: EstadoDeteccion


class ResumenSesionRespuesta(BaseModel):
    sesion_id: int
    iniciada_en: datetime
    finalizada_en: Optional[datetime] = None
    activa: bool
    duracion_segundos: Optional[int] = None
    conteo_por_estado: Dict[str, int]
    recomendaciones: List[str]
