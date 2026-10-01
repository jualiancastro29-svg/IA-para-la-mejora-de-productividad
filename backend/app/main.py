"""
main.py
---------
Punto de entrada de la API. Crea la app de FastAPI, configura CORS
(para que el frontend plano pueda llamar a la API desde otro origen),
crea las tablas de la base de datos si no existen, y conecta todas las
rutas.

CÓMO EJECUTAR (desde la carpeta backend/):
    uvicorn app.main:app --reload --port 8000

Documentación interactiva automática una vez corriendo:
    http://localhost:8000/docs
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import auth_routes, session_routes, user_routes
from .config import settings
from .database import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="API - Monitoreo de Sesiones de Estudio",
    description="Backend para registro de usuarios y seguimiento de "
                "estados de atención durante sesiones de estudio.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_routes.router)
app.include_router(user_routes.router)
app.include_router(session_routes.router)


@app.get("/salud", tags=["sistema"])
def salud():
    return {"estado": "ok"}
