"""
repositories/session_repository.py
--------------------------------------
Implementación concreta de ISessionRepository usando SQLAlchemy.
Maneja sesiones de estudio y sus eventos de detección.
"""

from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from ..domain.entities import EventoDeteccion, EstadoDeteccion, SesionEstudio
from ..domain.interfaces import ISessionRepository
from ..models.orm_models import EventoDeteccionORM, SesionEstudioORM


class SQLAlchemySessionRepository(ISessionRepository):

    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _sesion_a_entidad(orm: SesionEstudioORM) -> SesionEstudio:
        return SesionEstudio(
            id=orm.id,
            usuario_id=orm.usuario_id,
            iniciada_en=orm.iniciada_en,
            finalizada_en=orm.finalizada_en,
            activa=orm.activa,
        )

    @staticmethod
    def _evento_a_entidad(orm: EventoDeteccionORM) -> EventoDeteccion:
        return EventoDeteccion(
            id=orm.id, sesion_id=orm.sesion_id, estado=orm.estado, detectado_en=orm.detectado_en,
        )

    def crear_sesion(self, usuario_id: int) -> SesionEstudio:
        orm = SesionEstudioORM(usuario_id=usuario_id, iniciada_en=datetime.utcnow(), activa=True)
        self.db.add(orm)
        self.db.commit()
        self.db.refresh(orm)
        return self._sesion_a_entidad(orm)

    def obtener_sesion(self, sesion_id: int) -> Optional[SesionEstudio]:
        orm = self.db.query(SesionEstudioORM).filter(SesionEstudioORM.id == sesion_id).first()
        return self._sesion_a_entidad(orm) if orm else None

    def obtener_sesion_activa(self, usuario_id: int) -> Optional[SesionEstudio]:
        orm = (
            self.db.query(SesionEstudioORM)
            .filter(SesionEstudioORM.usuario_id == usuario_id, SesionEstudioORM.activa.is_(True))
            .first()
        )
        return self._sesion_a_entidad(orm) if orm else None

    def finalizar_sesion(self, sesion_id: int) -> Optional[SesionEstudio]:
        orm = self.db.query(SesionEstudioORM).filter(SesionEstudioORM.id == sesion_id).first()
        if not orm:
            return None
        orm.activa = False
        orm.finalizada_en = datetime.utcnow()
        self.db.commit()
        self.db.refresh(orm)
        return self._sesion_a_entidad(orm)

    def listar_sesiones_usuario(self, usuario_id: int) -> List[SesionEstudio]:
        orms = (
            self.db.query(SesionEstudioORM)
            .filter(SesionEstudioORM.usuario_id == usuario_id)
            .order_by(SesionEstudioORM.iniciada_en.desc())
            .all()
        )
        return [self._sesion_a_entidad(o) for o in orms]

    def registrar_evento(self, sesion_id: int, estado: str) -> EventoDeteccion:
        orm = EventoDeteccionORM(sesion_id=sesion_id, estado=EstadoDeteccion(estado), detectado_en=datetime.utcnow())
        self.db.add(orm)
        self.db.commit()
        self.db.refresh(orm)
        return self._evento_a_entidad(orm)

    def contar_eventos_por_estado(self, sesion_id: int) -> Dict[str, int]:
        eventos = self.db.query(EventoDeteccionORM).filter(EventoDeteccionORM.sesion_id == sesion_id).all()
        conteo = {estado.value: 0 for estado in EstadoDeteccion}
        for ev in eventos:
            conteo[ev.estado.value] += 1
        return conteo
