"""
detector_interface.py
------------------------
CONTRATO (puerto) entre el módulo de IA y el resto del proyecto.

Esta es la pieza clave para que ustedes dos trabajen en paralelo sin
pisarse: quien hace IA puede reescribir por completo cómo se detecta el
estado (cambiar de modelo, agregar más reglas, usar otra librería,
etc.), siempre que su clase siga cumpliendo esta interfaz. Quien hace
web/backend nunca necesita tocar este archivo ni saber cómo funciona el
modelo por dentro — solo le importa que devuelva (estado, confianza).

Principio Abierto/Cerrado: se puede EXTENDER (nuevas implementaciones de
DetectorDeEstado) sin MODIFICAR el código que ya las usa (client_ejemplo.py).
"""

from abc import ABC, abstractmethod
from typing import Tuple

# Debe coincidir EXACTAMENTE con backend/app/domain/entities.py -> EstadoDeteccion
ESTADOS_VALIDOS = [
    "Concentrado",
    "Distraido",
    "Dormido",
    "Somnoliento",
    "RevisandoTelefono",
    "Escribiendo",
    "Leyendo",
    "HablandoConOtraPersona",
    "Ausente",
]


class DetectorDeEstado(ABC):

    @abstractmethod
    def iniciar(self) -> None:
        """Prepara el detector: carga el/los modelo(s), abre la cámara,
        inicializa buffers, etc. Se llama una sola vez al empezar."""

    @abstractmethod
    def detectar_estado(self) -> Tuple[str, float]:
        """Captura el frame actual y devuelve (estado, confianza), donde
        'estado' es uno de los valores de ESTADOS_VALIDOS y 'confianza'
        es un número entre 0 y 1. Se llama repetidamente en un bucle."""

    @abstractmethod
    def detener(self) -> None:
        """Libera recursos (cámara, modelos, ventanas de OpenCV, etc.).
        Se llama una sola vez al terminar."""
