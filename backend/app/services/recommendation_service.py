"""
services/recommendation_service.py
--------------------------------------
Responsable ÚNICAMENTE de convertir un conteo de estados detectados en
recomendaciones de texto para el estudiante. Se separó de session_service
a propósito (Responsabilidad Única): las reglas de recomendación van a
cambiar y ajustarse con el tiempo (sobre todo por quien trabaje en la
parte de IA/UX), y así se pueden editar sin tocar la lógica de sesiones.

Para agregar o ajustar una recomendación, basta con editar las reglas de
UMBRALES_RECOMENDACIONES o la lógica de generar_recomendaciones.
"""

from typing import Dict, List

# Proporción mínima (sobre el total de detecciones) a partir de la cual
# se dispara cada recomendación. Son valores de partida: ajústalos según
# lo que observen en sesiones reales.
UMBRALES_RECOMENDACIONES = {
    "Dormido": 0.15,
    "Somnoliento": 0.20,
    "Distraido": 0.25,
    "RevisandoTelefono": 0.15,
    "HablandoConOtraPersona": 0.15,
    "Ausente": 0.20,
}

MENSAJES_RECOMENDACIONES = {
    "Dormido": "Se detectaron varios momentos dormido/a. Considera tomar un descanso "
               "o dormir mejor antes de tu próxima sesión de estudio.",
    "Somnoliento": "Mostraste signos de somnolencia con frecuencia. Prueba estudiar en "
                   "bloques más cortos con pausas activas cada 25-30 minutos.",
    "Distraido": "Hubo bastantes momentos de distracción. Intenta estudiar en un "
                 "espacio con menos estímulos visuales o sonoros.",
    "RevisandoTelefono": "Revisaste el teléfono con frecuencia. Prueba activar el modo "
                         "'No molestar' o dejar el teléfono fuera de alcance durante la sesión.",
    "HablandoConOtraPersona": "Hubo varias conversaciones durante la sesión. Si puedes, "
                              "busca un espacio más silencioso o avisa que no te interrumpan.",
    "Ausente": "Estuviste ausente del puesto de estudio una parte importante del "
               "tiempo. Considera sesiones más cortas pero con mayor compromiso de "
               "permanecer en el lugar de estudio.",
}

MENSAJE_POR_DEFECTO = "¡Buen trabajo! Mantuviste un nivel de concentración adecuado durante la sesión."


class RecommendationService:

    def generar_recomendaciones(self, conteo_por_estado: Dict[str, int]) -> List[str]:
        total = sum(conteo_por_estado.values())
        if total == 0:
            return ["No se registraron suficientes detecciones durante la sesión."]

        recomendaciones = []
        for estado, umbral in UMBRALES_RECOMENDACIONES.items():
            proporcion = conteo_por_estado.get(estado, 0) / total
            if proporcion >= umbral:
                recomendaciones.append(MENSAJES_RECOMENDACIONES[estado])

        if not recomendaciones:
            recomendaciones.append(MENSAJE_POR_DEFECTO)

        return recomendaciones
