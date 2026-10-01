"""
config.py
----------
Configuración centralizada, leída de variables de entorno (archivo .env).
Ningún otro módulo del backend debe leer os.environ directamente: todos
importan `settings` desde aquí. Así hay un solo lugar que cambiar si se
agrega una nueva variable de configuración.
"""

import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    SECRET_KEY: str = os.getenv("SECRET_KEY", "cambia-esta-clave-en-produccion")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "480"))

    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./app.db")

    # Usados solo por seed_admin.py para crear el primer usuario administrador
    ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "admin1234")
    ADMIN_NOMBRE: str = os.getenv("ADMIN_NOMBRE", "Administrador")

    # Orígenes permitidos para CORS (el frontend plano puede correr desde
    # file:// o desde un servidor estático local; se deja abierto en
    # desarrollo y se debe restringir en producción)
    CORS_ORIGINS: list = ["*"]


settings = Settings()
