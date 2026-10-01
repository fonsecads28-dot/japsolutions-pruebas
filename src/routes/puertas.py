#Endpoints de autenticacion de puertas y control de acceso
import os
from importlib import import_module

try:
    from fastapi import APIRouter, HTTPException, Depends  # type: ignore[import-not-found, reportMissingImports]
except ImportError:  # pragma: no cover - fallback para entornos sin FastAPI instalado
    class APIRouter:
        def __init__(self, *args, **kwargs):
            pass

        def post(self, *args, **kwargs):
            def decorator(func):
                return func

            return decorator

    class HTTPException(Exception):
        def __init__(self, status_code: int, detail: str = None):
            self.status_code = status_code
            self.detail = detail

    def Depends(*args, **kwargs):
        return None

try:
    from sqlalchemy.ext.asyncio import AsyncSession  # type: ignore[import-not-found, reportMissingImports]
except ImportError:  # pragma: no cover - fallback para entornos sin SQLAlchemy instalado
    class AsyncSession:  # type: ignore[no-redef]
        pass

try:
    from sqlalchemy import select  # type: ignore[import-not-found, reportMissingImports]
except ImportError:  # pragma: no cover - fallback para entornos sin SQLAlchemy instalado
    def select(*args, **kwargs):
        raise RuntimeError("SQLAlchemy no está instalado en este entorno")

from src.config.database import get_db
from src.models.db_models import Edificio
from src.schemas.api_schemas import AperturaRequest

router = APIRouter(prefix="/api/v1/puertas", tags=["Puertas / Domótica"])

# Inicializar cliente MQTT global de forma eficiente
MQTT_BROKER = os.getenv("MQTT_BROKER", "broker.hivemq.com")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))

try:
    mqtt = import_module("paho.mqtt.client")
    mqtt_client = mqtt.Client()
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
    mqtt_client.loop_start()
except Exception:
    mqtt_client = None
    print("⚠️ error informativo MQTT: No se pudo conectar al broker")

@router.post("/abrir")
async def abrir_puerta(payload: AperturaRequest, db: AsyncSession = Depends(get_db)):
    """Envía un comando MQTT estructurado al relé IoT asignado al edificio específico."""
    
    # Validar la existencia del edificio y extraer el canal MQTT exclusivo
    stmt = select(Edificio).where(Edificio.id == payload.edificio_id)
    result = await db.execute(stmt)
    edificio = result.scalar_one_or_none()

    if not edificio:
        raise HTTPException(status_code=404, detail="Edificio no registrado en el sistema")

    # Tópico estructurado según la consonancia del diseño base
    topic = f"portero/edificios/{edificio.token_mqtt}/comando"
    
    try:
        if mqtt_client is None:
            raise HTTPException(
                status_code=503,
                detail="El servicio MQTT no está disponible en este entorno",
            )

        # Mensaje estandarizado para hardware domótico (Shelly, ESP32)
        mensaje_rele = '{"action": "OPEN", "duration_sec": 3}'
        
        # Publicación mediante la biblioteca de red Paho-MQTT
        info_publicacion = mqtt_client.publish(topic, mensaje_rele, qos=1)
        info_publicacion.wait_for_publish() # Asegura la entrega antes de responder al cliente móvil
        
        return {
            "status": "success", 
            "message": f"Comando de apertura transmitido con éxito al canal del edificio: {edificio.nombre}"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Fallo crítico en la infraestructura de comunicación IoT: {str(e)}"
        )