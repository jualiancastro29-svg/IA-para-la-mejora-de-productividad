# Monitoreo de Sesiones de Estudio

Plataforma con backend (FastAPI), frontend minimalista (HTML/CSS/JS
puro) y un módulo de IA (detección de estado de atención vía webcam)
desacoplado del resto mediante una interfaz clara.

## Estructura del proyecto

```
proyecto_estudio/
├── backend/            <- API REST (FastAPI + SQLite + JWT)
│   ├── app/
│   │   ├── domain/        entidades e interfaces (el "contrato" interno)
│   │   ├── models/        modelos ORM (SQLAlchemy)
│   │   ├── repositories/  implementación concreta de acceso a datos
│   │   ├── services/      reglas de negocio (casos de uso)
│   │   ├── schemas/       validación de entrada/salida de la API
│   │   ├── api/           rutas HTTP + dependencias (auth, DI)
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── security.py
│   │   └── main.py        punto de entrada
│   ├── seed_admin.py      crea el usuario administrador inicial
│   ├── requirements.txt
│   └── .env.example
├── ai_detection/        <- Módulo de detección de estado (independiente)
│   ├── detector_interface.py   CONTRATO que cualquier detector debe cumplir
│   ├── mediapipe_detector.py   implementación actual (MediaPipe + RandomForest)
│   └── client_ejemplo.py       ejemplo de cómo conectar IA -> backend
└── frontend/            <- HTML/CSS/JS plano, sin frameworks
    ├── index.html          login / registro
    ├── dashboard.html       panel con pestañas (sesión de estudio / admin)
    ├── css/styles.css
    └── js/
        ├── api.js           wrapper de fetch + manejo de token
        ├── auth.js           lógica de login/registro
        └── dashboard.js      sesiones, contadores en vivo, panel admin
```

## Cómo dividirse el trabajo (2 personas)

- **Encargado de IA** trabaja casi exclusivamente en `ai_detection/`.
  El único contrato que debe respetar es `detector_interface.py`: su
  detector debe devolver `(estado, confianza)` donde `estado` es uno de
  los valores de `ESTADOS_VALIDOS`. Puede reemplazar `mediapipe_detector.py`
  por completo (otro modelo, otras reglas) sin que el backend ni el
  frontend se enteren, siempre que respete esos nombres de estado.

- **Encargado de web** trabaja en `backend/` y `frontend/`. No necesita
  entender el modelo de IA: solo necesita saber que va a recibir eventos
  en `POST /sesiones/{id}/eventos` con uno de los estados válidos (eso
  ya está implementado y validado en `session_service.py`).

- **Punto de contacto entre ambos:** la lista de estados. Está duplicada
  intencionalmente en 3 lugares (`backend/app/domain/entities.py` ->
  `EstadoDeteccion`, `ai_detection/detector_interface.py` ->
  `ESTADOS_VALIDOS`, `frontend/js/dashboard.js` -> `ESTADOS`) porque cada
  capa es un proyecto independiente en producción. Si agregan o renombran
  un estado, deben actualizar los 3 lugares. Si prefieren evitar la
  duplicación, pueden exponer `GET /estados-validos` desde el backend y
  que el frontend los pida dinámicamente — queda como mejora futura.

## Cómo correr el proyecto

### 1. Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate      # En Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env          # y edita SECRET_KEY, ADMIN_PASSWORD, etc.
python seed_admin.py          # crea el usuario administrador inicial
uvicorn app.main:app --reload --port 8000
```
Documentación interactiva: http://localhost:8000/docs

### 2. Frontend
No requiere build. Basta con abrir `frontend/index.html` en el navegador,
o servirlo con cualquier servidor estático simple, por ejemplo:
```bash
cd frontend
python -m http.server 5500
```
Y entrar a `http://localhost:5500`. Asegúrate de que el backend esté
corriendo en `http://localhost:8000` (ver `API_URL` en `js/api.js`).

### 3. Módulo de IA
```bash
cd ai_detection
pip install requests opencv-python mediapipe scikit-learn joblib
# Copia aquí (o ajusta MODELS_PATH) los archivos modeloClasificador.joblib
# y escalador.joblib generados por el pipeline de entrenamiento.
python client_ejemplo.py
```

## Flujo de uso

1. Un usuario se registra (`/auth/register`) o el admin lo crea desde el
   panel de administración.
2. El usuario inicia sesión en el frontend (`index.html` -> `dashboard.html`).
3. En la pestaña "Sesión de estudio", presiona "Iniciar sesión de estudio"
   (esto crea una sesión en el backend).
4. En paralelo, corre `ai_detection/client_ejemplo.py` (o la integración
   que desarrollen), que detecta el estado cada cierto tiempo y lo envía
   al backend mientras la sesión está activa.
5. El panel muestra los contadores por estado actualizándose cada pocos
   segundos (polling simple).
6. Al presionar "Terminar sesión", el backend cierra la sesión y calcula
   el resumen + las recomendaciones (ver `services/recommendation_service.py`),
   que se muestran en pantalla.

## Principios SOLID aplicados

- **S (Responsabilidad única):** cada servicio hace una sola cosa
  (`AuthService` solo autentica, `UserService` solo administra usuarios,
  `SessionService` solo orquesta sesiones, `RecommendationService` solo
  genera recomendaciones).
- **O (Abierto/Cerrado):** `DetectorDeEstado` permite agregar nuevas
  implementaciones de detección sin modificar el código que las usa.
- **L (Sustitución de Liskov):** cualquier implementación de
  `IUserRepository` / `ISessionRepository` / `DetectorDeEstado` puede
  sustituir a otra sin romper a quien las usa.
- **I (Segregación de interfaces):** `IUserRepository` e
  `ISessionRepository` están separadas en vez de una sola interfaz
  gigante de "repositorio".
- **D (Inversión de dependencias):** los servicios dependen de
  interfaces del dominio (`domain/interfaces.py`), no de SQLAlchemy
  directamente; `api/deps.py` es quien conecta las implementaciones
  concretas (Inyección de Dependencias de FastAPI).

## Próximos pasos sugeridos

- Agregar pruebas unitarias a los servicios (son fáciles de testear
  gracias a la inversión de dependencias: se les puede inyectar
  repositorios falsos en memoria).
- Mover la integración IA -> backend del script de consola
  (`client_ejemplo.py`) a algo más integrado con el frontend si el
  flujo final lo requiere.
- Persistir refresh tokens o acortar la expiración del JWT si se
  requiere mayor seguridad.
- Agregar paginación a `GET /admin/usuarios` y `GET /sesiones` si crece
  la cantidad de datos.
