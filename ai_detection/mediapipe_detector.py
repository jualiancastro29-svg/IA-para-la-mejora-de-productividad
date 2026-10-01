"""
mediapipe_detector.py
------------------------
Implementación concreta de DetectorDeEstado usando el pipeline de
MediaPipe + RandomForest ya construido (captura de landmarks de rostro y
manos, clasificador entrenado, y las reglas de Ausente / conversación /
desempate teléfono-escribiendo-leyendo).

Este archivo asume que ya tienes entrenado el modelo con el pipeline de
captura/entrenamiento (carpeta separada del proyecto de entrenamiento:
1_captura_datos.py, 2_extraccion_landmarks.py, 3_entrenamiento_clasificador.py)
y que modeloClasificador.joblib / escalador.joblib existen en MODELS_PATH.

Si el encargado de IA cambia de enfoque (otro modelo, otra librería),
este archivo es el que se reemplaza — el resto del proyecto no se entera.
"""

import os
from collections import deque
from typing import Optional, Tuple

import cv2
import joblib
import mediapipe as mp
import numpy as np

from detector_interface import DetectorDeEstado

# --- Ajusta esta ruta a donde estén tus modelos entrenados ---
MODELS_PATH = os.getenv("MODELS_PATH", "./Modelos")

UMBRAL_FRAMES_AUSENCIA = 45
TAMANO_VENTANA_TEMPORAL = 30
UMBRAL_YAW_MIRADA_LATERAL = 20.0
FRACCION_MIN_MIRADA_LATERAL = 0.6
UMBRAL_VARIANZA_MAR_HABLANDO = 0.0008
ESTADOS_AMBIGUOS_MIRADA_ABAJO = {"RevisandoTelefono", "Escribiendo", "Leyendo"}
CONFIANZA_BAJA_UMBRAL = 0.45

OJO_DER = [33, 160, 158, 133, 153, 144]
OJO_IZQ = [362, 385, 387, 263, 373, 380]
BOCA = {"sup": 13, "inf": 14, "izq": 61, "der": 291}
POSE_IDX = {"nariz": 1, "menton": 152, "ojo_izq_ext": 263, "ojo_der_ext": 33,
            "boca_izq": 61, "boca_der": 291}

MODEL_3D_POINTS = np.array([
    (0.0, 0.0, 0.0), (0.0, -330.0, -65.0),
    (-225.0, 170.0, -135.0), (225.0, 170.0, -135.0),
    (-150.0, -150.0, -125.0), (150.0, -150.0, -125.0),
], dtype=np.float64)


def _dist(a, b):
    return np.linalg.norm(np.array(a) - np.array(b))


def _calcular_ear(landmarks, indices, w, h):
    pts = [(landmarks[i].x * w, landmarks[i].y * h) for i in indices]
    p1, p2, p3, p4, p5, p6 = pts
    return (_dist(p2, p6) + _dist(p3, p5)) / (2.0 * _dist(p1, p4) + 1e-6)


def _calcular_mar(landmarks, w, h):
    sup = (landmarks[BOCA["sup"]].x * w, landmarks[BOCA["sup"]].y * h)
    inf = (landmarks[BOCA["inf"]].x * w, landmarks[BOCA["inf"]].y * h)
    izq = (landmarks[BOCA["izq"]].x * w, landmarks[BOCA["izq"]].y * h)
    der = (landmarks[BOCA["der"]].x * w, landmarks[BOCA["der"]].y * h)
    return _dist(sup, inf) / (_dist(izq, der) + 1e-6)


def _calcular_pose(landmarks, w, h):
    puntos_2d = np.array([
        (landmarks[POSE_IDX["nariz"]].x * w, landmarks[POSE_IDX["nariz"]].y * h),
        (landmarks[POSE_IDX["menton"]].x * w, landmarks[POSE_IDX["menton"]].y * h),
        (landmarks[POSE_IDX["ojo_izq_ext"]].x * w, landmarks[POSE_IDX["ojo_izq_ext"]].y * h),
        (landmarks[POSE_IDX["ojo_der_ext"]].x * w, landmarks[POSE_IDX["ojo_der_ext"]].y * h),
        (landmarks[POSE_IDX["boca_izq"]].x * w, landmarks[POSE_IDX["boca_izq"]].y * h),
        (landmarks[POSE_IDX["boca_der"]].x * w, landmarks[POSE_IDX["boca_der"]].y * h),
    ], dtype=np.float64)

    focal_length = w
    camera_matrix = np.array([[focal_length, 0, w / 2], [0, focal_length, h / 2], [0, 0, 1]], dtype=np.float64)
    ok, rvec, tvec = cv2.solvePnP(MODEL_3D_POINTS, puntos_2d, camera_matrix, np.zeros((4, 1)))
    if not ok:
        return 0.0, 0.0, 0.0
    rmat, _ = cv2.Rodrigues(rvec)
    proj_matrix = np.hstack((rmat, tvec))
    _, _, _, _, _, _, euler_angles = cv2.decomposeProjectionMatrix(proj_matrix)
    pitch, yaw, roll = [float(a[0]) for a in euler_angles]
    return yaw, pitch, roll


def _calcular_features_mano(hands_result, landmarks_rostro, w, h):
    if not hands_result.multi_hand_landmarks:
        return 0, 3.0, 0.0, None

    rostro_x = (landmarks_rostro[POSE_IDX["nariz"]].x + landmarks_rostro[POSE_IDX["menton"]].x) / 2 * w
    rostro_y = (landmarks_rostro[POSE_IDX["nariz"]].y + landmarks_rostro[POSE_IDX["menton"]].y) / 2 * h
    ancho_rostro = _dist(
        (landmarks_rostro[POSE_IDX["ojo_izq_ext"]].x * w, landmarks_rostro[POSE_IDX["ojo_izq_ext"]].y * h),
        (landmarks_rostro[POSE_IDX["ojo_der_ext"]].x * w, landmarks_rostro[POSE_IDX["ojo_der_ext"]].y * h),
    ) + 1e-6

    mejor_dist, mejor_altura, mano_xy = None, None, None
    for hand_landmarks in hands_result.multi_hand_landmarks:
        xs = [lm.x * w for lm in hand_landmarks.landmark]
        ys = [lm.y * h for lm in hand_landmarks.landmark]
        mano_x, mano_y = np.mean(xs), np.mean(ys)
        d = _dist((mano_x, mano_y), (rostro_x, rostro_y)) / ancho_rostro
        altura_rel = (mano_y - rostro_y) / ancho_rostro
        if mejor_dist is None or d < mejor_dist:
            mejor_dist, mejor_altura = d, altura_rel
            mano_xy = (mano_x / ancho_rostro, mano_y / ancho_rostro)

    return 1, mejor_dist, mejor_altura, mano_xy


class MediapipeStateDetector(DetectorDeEstado):
    """Implementación del detector usando MediaPipe + RandomForest.
    Ver docstring del módulo para contexto."""

    def __init__(self, models_path: str = MODELS_PATH, camera_index: int = 0):
        self.models_path = models_path
        self.camera_index = camera_index

        self.clf = None
        self.scaler = None
        self.face_mesh = None
        self.hands = None
        self.cap = None

        self.buffer_mar = deque(maxlen=TAMANO_VENTANA_TEMPORAL)
        self.buffer_yaw = deque(maxlen=TAMANO_VENTANA_TEMPORAL)
        self.buffer_mano_xy = deque(maxlen=TAMANO_VENTANA_TEMPORAL)
        self.frames_sin_rostro_seguidos = 0

    def iniciar(self) -> None:
        self.clf = joblib.load(os.path.join(self.models_path, "modeloClasificador.joblib"))
        self.scaler = joblib.load(os.path.join(self.models_path, "escalador.joblib"))

        self.face_mesh = mp.solutions.face_mesh.FaceMesh(
            static_image_mode=False, max_num_faces=1,
            refine_landmarks=True, min_detection_confidence=0.5, min_tracking_confidence=0.5,
        )
        self.hands = mp.solutions.hands.Hands(
            static_image_mode=False, max_num_hands=2,
            min_detection_confidence=0.4, min_tracking_confidence=0.4,
        )
        self.cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)

    def detectar_estado(self) -> Tuple[str, float]:
        ret, frame = self.cap.read()
        if not ret:
            return "Ausente", 0.0

        h, w = frame.shape[:2]
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        resultado_rostro = self.face_mesh.process(rgb)

        if not resultado_rostro.multi_face_landmarks:
            self.frames_sin_rostro_seguidos += 1
            if self.frames_sin_rostro_seguidos >= UMBRAL_FRAMES_AUSENCIA:
                return "Ausente", 1.0
            return "Ausente", 0.0  # momentáneo: no se reporta como evento confiable todavía

        self.frames_sin_rostro_seguidos = 0
        landmarks = resultado_rostro.multi_face_landmarks[0].landmark
        resultado_manos = self.hands.process(rgb)

        ear_der = _calcular_ear(landmarks, OJO_DER, w, h)
        ear_izq = _calcular_ear(landmarks, OJO_IZQ, w, h)
        mar = _calcular_mar(landmarks, w, h)
        yaw, pitch, roll = _calcular_pose(landmarks, w, h)
        mano_visible, mano_dist, mano_altura, mano_xy = _calcular_features_mano(resultado_manos, landmarks, w, h)

        X = np.array([[ear_izq, ear_der, (ear_izq + ear_der) / 2.0, mar, yaw, pitch, roll,
                       mano_visible, mano_dist, mano_altura]])
        X_s = self.scaler.transform(X)

        pred = self.clf.predict(X_s)[0]
        proba = self.clf.predict_proba(X_s)[0]
        confianza = float(np.max(proba))

        self.buffer_mar.append(mar)
        self.buffer_yaw.append(yaw)
        self.buffer_mano_xy.append(mano_xy)

        etiqueta_final = pred

        if len(self.buffer_mar) == TAMANO_VENTANA_TEMPORAL:
            varianza_mar = float(np.var(self.buffer_mar))
            fraccion_lateral = float(np.mean([abs(y) > UMBRAL_YAW_MIRADA_LATERAL for y in self.buffer_yaw]))
            if varianza_mar > UMBRAL_VARIANZA_MAR_HABLANDO and fraccion_lateral >= FRACCION_MIN_MIRADA_LATERAL:
                etiqueta_final = "HablandoConOtraPersona"

        if (etiqueta_final in ESTADOS_AMBIGUOS_MIRADA_ABAJO and confianza < CONFIANZA_BAJA_UMBRAL
                and len(self.buffer_mano_xy) == TAMANO_VENTANA_TEMPORAL):
            posiciones_validas = [p for p in self.buffer_mano_xy if p is not None]
            if len(posiciones_validas) >= TAMANO_VENTANA_TEMPORAL * 0.5:
                xs = [p[0] for p in posiciones_validas]
                ys = [p[1] for p in posiciones_validas]
                movimiento_mano = float(np.var(xs) + np.var(ys))
                mano_cerca = mano_dist < 1.2
                if movimiento_mano > 0.02:
                    etiqueta_final = "Escribiendo"
                elif mano_cerca:
                    etiqueta_final = "RevisandoTelefono"
                else:
                    etiqueta_final = "Leyendo"
            else:
                etiqueta_final = "Leyendo"

        return etiqueta_final, confianza

    def detener(self) -> None:
        if self.cap:
            self.cap.release()
        if self.face_mesh:
            self.face_mesh.close()
        if self.hands:
            self.hands.close()
        cv2.destroyAllWindows()
