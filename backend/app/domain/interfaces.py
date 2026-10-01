"""
domain/interfaces.py
----------------------
"Puertos" del dominio (Principio de Inversión de Dependencias - la "D" de
SOLID): son contratos abstractos que la capa de servicios usa para hablar
con la base de datos, SIN saber si por debajo hay SQLAlchemy, otro ORM, o
incluso archivos planos.

Gracias a esto:
  - Los servicios (services/) son fáciles de probar (se les puede pasar
    una implementación falsa/en memoria en los tests).
  - Si en el futuro cambian de SQLite a PostgreSQL, o de SQLAlchemy a
    otra librería, solo se reescribe la implementación en repositories/,
    sin tocar services/ ni api/.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from .entities import EventoDeteccion, SesionEstudio, Usuario


class IUserRepository(ABC):

    @abstractmethod
    def obtener_por_id(self, user_id: int) -> Optional[Usuario]:
        ...

    @abstractmethod
    def obtener_por_username(self, username: str) -> Optional[Usuario]:
        ...

    @abstractmethod
    def listar(self) -> List[Usuario]:
        ...

    @abstractmethod
    def crear(self, usuario: Usuario) -> Usuario:
        ...

    @abstractmethod
    def actualizar(self, usuario: Usuario) -> Usuario:
        ...


class ISessionRepository(ABC):

    @abstractmethod
    def crear_sesion(self, usuario_id: int) -> SesionEstudio:
        ...

    @abstractmethod
    def obtener_sesion(self, sesion_id: int) -> Optional[SesionEstudio]:
        ...

    @abstractmethod
    def obtener_sesion_activa(self, usuario_id: int) -> Optional[SesionEstudio]:
        ...

    @abstractmethod
    def finalizar_sesion(self, sesion_id: int) -> Optional[SesionEstudio]:
        ...

    @abstractmethod
    def listar_sesiones_usuario(self, usuario_id: int) -> List[SesionEstudio]:
        ...

    @abstractmethod
    def registrar_evento(self, sesion_id: int, estado: str) -> EventoDeteccion:
        ...

    @abstractmethod
    def contar_eventos_por_estado(self, sesion_id: int) -> Dict[str, int]:
        ...
