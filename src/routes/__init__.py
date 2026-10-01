# src/routes/_init_.py
from src.config.firebase import inicializar_firebase

# Forzamos la inicialización del SDK de Google antes de cargar las rutas de la API
inicializar_firebase()

from .visitante import router as visitante_router
from .puertas import router as puertas_router

_all_ = [
    "visitante_router",
    "puertas_router"
]