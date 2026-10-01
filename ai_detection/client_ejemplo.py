"""
client_ejemplo.py
---------------------
Script de ejemplo que conecta el detector de IA con el backend: inicia
sesión en la API, arranca una sesión de estudio, corre el detector en
bucle y va enviando eventos al backend cada vez que el estado detectado
cambia (con un pequeño "debounce" para no inundar la API con un POST por
cada frame). Al presionar ESC, finaliza la sesión y muestra el resumen
con las recomendaciones.

Esto es solo un EJEMPLO de integración — en la versión final, lo normal
es que el frontend (JS, corriendo en el navegador) sea quien orqueste
esto llamando a un pequeño servicio local de IA, o que este script corra
como un proceso aparte en la máquina del estudiante. Ajusten esta parte
según cómo decidan conectar cámara + navegador.

Requiere:
    pip install requests opencv-python mediapipe scikit-learn joblib

CÓMO EJECUTARLO:
    python client_ejemplo.py
"""

import time

import requests

from detector_interface import ESTADOS_VALIDOS
from mediapipe_detector import MediapipeStateDetector

API_URL = "http://localhost:8000"
USERNAME = "persona01"       # cambia por un usuario ya registrado
PASSWORD = "contraseña123"   # cambia por su contraseña

INTERVALO_MIN_ENTRE_EVENTOS_SEG = 2.0  # no más de un evento cada 2s por estado repetido


def login() -> str:
    resp = requests.post(f"{API_URL}/auth/login", json={"username": USERNAME, "password": PASSWORD})
    resp.raise_for_status()
    return resp.json()["access_token"]


def iniciar_sesion(token: str) -> int:
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.post(f"{API_URL}/sesiones/iniciar", headers=headers)
    resp.raise_for_status()
    return resp.json()["id"]


def registrar_evento(token: str, sesion_id: int, estado: str) -> None:
    headers = {"Authorization": f"Bearer {token}"}
    requests.post(f"{API_URL}/sesiones/{sesion_id}/eventos", headers=headers, json={"estado": estado})


def finalizar_sesion(token: str, sesion_id: int) -> dict:
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.post(f"{API_URL}/sesiones/{sesion_id}/finalizar", headers=headers)
    resp.raise_for_status()
    return resp.json()


def main():
    print("Iniciando sesión en la API...")
    token = login()

    print("Creando sesión de estudio...")
    sesion_id = iniciar_sesion(token)
    print(f"Sesión #{sesion_id} iniciada. Presiona Ctrl+C para finalizar.")

    detector = MediapipeStateDetector()
    detector.iniciar()

    ultimo_estado_enviado = None
    ultimo_envio_ts = 0.0

    try:
        while True:
            estado, confianza = detector.detectar_estado()

            ahora = time.time()
            debe_enviar = (
                estado != ultimo_estado_enviado
                or (ahora - ultimo_envio_ts) >= INTERVALO_MIN_ENTRE_EVENTOS_SEG
            )

            if debe_enviar and estado in ESTADOS_VALIDOS:
                registrar_evento(token, sesion_id, estado)
                ultimo_estado_enviado = estado
                ultimo_envio_ts = ahora
                print(f"Estado: {estado} ({confianza*100:.0f}%) -> evento enviado")

            time.sleep(0.1)  # ~10 detecciones por segundo es suficiente

    except KeyboardInterrupt:
        print("\nFinalizando sesión...")
    finally:
        detector.detener()
        resumen = finalizar_sesion(token, sesion_id)
        print("\n=== RESUMEN DE LA SESIÓN ===")
        print(f"Duración: {resumen['duracion_segundos']} segundos")
        print("Conteo por estado:")
        for estado, cantidad in resumen["conteo_por_estado"].items():
            print(f"  {estado}: {cantidad}")
        print("\nRecomendaciones:")
        for r in resumen["recomendaciones"]:
            print(f"  - {r}")


if __name__ == "__main__":
    main()
