"""
services/session_service.py
-------------------------------
Casos de uso de sesiones de estudio: iniciar, registrar eventos de
detección, finalizar y obtener el resumen con recomendaciones.

Depende de ISessionRepository (interfaz) y de RecommendationService.
No sabe nada de HTTP, ni de cómo llegan los eventos de detección (si
vienen de una webcam local, de una app móvil, etc.) — eso es
responsabilidad de quien llama a este servicio desde api/session_routes.py.
"""

from typing import Dict, List

from ..domain.entities import EstadoDeteccion, EventoDeteccion, SesionEstudio
from ..domain.interfaces import ISessionRepository
from .recommendation_service import RecommendationService


class SessionService:

    def __init__(self, session_repo: ISessionRepository, recommendation_service: RecommendationService):
        self.session_repo = session_repo
        self.recommendation_service = recommendation_service

    def iniciar_sesion(self, usuario_id: int) -> SesionEstudio:
        sesion_activa = self.session_repo.obtener_sesion_activa(usuario_id)
        if sesion_activa:
            raise ValueError("Ya existe una sesión activa para este usuario")
        return self.session_repo.crear_sesion(usuario_id)

    def registrar_evento(self, sesion_id: int, estado: str, usuario_id: int) -> EventoDeteccion:
        sesion = self.session_repo.obtener_sesion(sesion_id)
        if not sesion:
            raise ValueError("Sesión no encontrada")
        if sesion.usuario_id != usuario_id:
            raise PermissionError("Esta sesión no pertenece al usuario autenticado")
        if not sesion.activa:
            raise ValueError("La sesión ya fue finalizada")

        # Valida que el estado recibido sea uno de los definidos en el
        # dominio; si el módulo de IA envía un valor no reconocido, se
        # rechaza aquí con un mensaje claro en vez de guardarse basura.
        try:
            EstadoDeteccion(estado)
        except ValueError:
            raise ValueError(f"Estado de detección no reconocido: {estado}")

        return self.session_repo.registrar_evento(sesion_id, estado)

    def finalizar_sesion(self, sesion_id: int, usuario_id: int) -> dict:
        sesion = self.session_repo.obtener_sesion(sesion_id)
        if not sesion:
            raise ValueError("Sesión no encontrada")
        if sesion.usuario_id != usuario_id:
            raise PermissionError("Esta sesión no pertenece al usuario autenticado")

        sesion_finalizada = self.session_repo.finalizar_sesion(sesion_id)
        return self._construir_resumen(sesion_finalizada)

    def obtener_resumen(self, sesion_id: int, usuario_id: int) -> dict:
        sesion = self.session_repo.obtener_sesion(sesion_id)
        if not sesion:
            raise ValueError("Sesión no encontrada")
        if sesion.usuario_id != usuario_id:
            raise PermissionError("Esta sesión no pertenece al usuario autenticado")
        return self._construir_resumen(sesion)

    def obtener_sesion_activa(self, usuario_id: int) -> SesionEstudio | None:
        return self.session_repo.obtener_sesion_activa(usuario_id)

    def listar_sesiones_usuario(self, usuario_id: int) -> List[SesionEstudio]:
        return self.session_repo.listar_sesiones_usuario(usuario_id)

    def _construir_resumen(self, sesion: SesionEstudio) -> dict:
        conteo = self.session_repo.contar_eventos_por_estado(sesion.id)
        duracion_segundos = None
        if sesion.finalizada_en:
            duracion_segundos = int((sesion.finalizada_en - sesion.iniciada_en).total_seconds())

        recomendaciones = self.recommendation_service.generar_recomendaciones(conteo)

        return {
            "sesion_id": sesion.id,
            "iniciada_en": sesion.iniciada_en,
            "finalizada_en": sesion.finalizada_en,
            "activa": sesion.activa,
            "duracion_segundos": duracion_segundos,
            "conteo_por_estado": conteo,
            "recomendaciones": recomendaciones,
        }
