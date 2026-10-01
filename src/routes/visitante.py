#endpoints de codigos QR de departamentos e inicio de llamadas de visitantes
import os
from importlib import import_module
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from fastapi import APIRouter, HTTPException, Depends  # type: ignore[import-not-found]
    from sqlalchemy.ext.asyncio import AsyncSession  # type: ignore[import-not-found]
else:
    try:
        from fastapi import APIRouter, HTTPException, Depends  # type: ignore[import-not-found]
    except ImportError as exc:
        raise ImportError(
            "FastAPI is required to load this route. Install it in the active Python environment "
            "(for example: python -m pip install fastapi)."
        ) from exc

    try:
        from sqlalchemy.ext.asyncio import AsyncSession
    except ImportError:  # pragma: no cover - depende del entorno de ejecución
        AsyncSession = Any  # type: ignore[misc, assignment]

from sqlalchemy import select  # type: ignore[import-not-found]

try:
    messaging = import_module("firebase_admin.messaging")
except ImportError:  # pragma: no cover - depende del entorno de ejecución
    messaging = None  # type: ignore[assignment]

try:
    livekit_api = import_module("livekit.api")
except ImportError:  # pragma: no cover - depende del entorno de ejecución
    livekit_api = None

api = livekit_api

from src.config.database import get_db
from src.models.db_models import Edificio, Departamento, Usuario
from src.schemas.api_schemas import ConfigurarQRResponse, IniciarLlamadaQRRequest, IniciarLlamadaQRResponse

router = APIRouter(prefix="/api/v1/visitante", tags=["Visitante"])

LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")

@router.get("/configurar-qr/{token_url}", response_model=ConfigurarQRResponse)
async def cargar_pantalla_qr(token_url: str, db: AsyncSession = Depends(get_db)):
    """Traduce el token público del código QR en los datos del edificio y sus unidades."""
    # Buscar Edificio
    stmt_edificio = select(Edificio).where(Edificio.token_url == token_url)
    result_edificio = await db.execute(stmt_edificio)
    edificio = result_edificio.scalar_one_or_none()

    if not edificio:
        raise HTTPException(status_code=404, detail="Código QR no válido o edificio no registrado")

    # Buscar Departamentos asociados
    stmt_deptos = select(Departamento).where(Departamento.edificio_id == edificio.id).order_by(Departamento.nombre_unidad)
    result_deptos = await db.execute(stmt_deptos)
    departamentos = result_deptos.scalars().all()

    directorios = [
        {"id": depto.id, "unidad": depto.nombre_unidad} for depto in departamentos
    ]

    return {
        "edificio_nombre": edificio.nombre,
        "edificio_id": edificio.id,
        "directorios": directorios
    }

@router.post("/llamar") #response_model=IniciarLlamadaQRResponse)
async def iniciar_llamada_qr(payload: IniciarLlamadaQRRequest, db: AsyncSession = Depends(get_db)):
    """Crea la sala WebRTC en LiveKit y envía la notificación push de alta prioridad al residente."""
    
    # Unificar la consulta para traer departamento, edificio y usuario (token FCM)
    stmt = (
        select(Departamento, Edificio, Usuario)
        .join(Edificio, Departamento.edificio_id == Edificio.id)
        .outerjoin(Usuario, Usuario.departamento_id == Departamento.id)
        .where(Departamento.id == payload.departamento_id)
    )
    result = await db.execute(stmt)
    row = result.first()

    if not row:
        raise HTTPException(status_code=404, detail="Unidad o departamento no encontrado")

    depto, edificio, usuario = row
    room_name = f"room_qr_depto_{depto.id}"

    # 1. Generar Token WebRTC (LiveKit) para el Navegador del Visitante
    try:
        token_visitante = (
            api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
            .with_identity(f"visitante_{payload.nombre_visitante}")
            .with_grants(
                api.VideoGrants(
                    room_join=True,
                    room=room_name,
                    can_publish=True,
                    can_subscribe=True,
                )
            )
        )
        jwt_visitante = token_visitante.to_jwt()
        jwt_residente = token_visitante.to_jwt()  # El residente puede usar el mismo token para unirse a la sala
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar credenciales WebRTC: {str(e)}")

    # 2. Enviar Notificación Push (Firebase) de Alta Prioridad al Residente si tiene Token
    residente_notificado = False
    if usuario and usuario.fcm_token:
        try:
            data_payload = {
                "tipo_evento": "PORTERO_LLAMADA_ENTRANTE",
                "edificio_nombre": edificio.nombre,
                "nombre_unidad": depto.nombre_unidad,
                "room_name": room_name,
            }

            mensaje = messaging.Message(
                data=data_payload,
                token=usuario.fcm_token,
                android=messaging.AndroidConfig(priority="high", ttl=30),
                apns=messaging.APNSConfig(
                    headers={"apns-priority": "10", "apns-expiration": "30", "apns-push-type": "data"},
                    payload=messaging.APNSPayload(aps=messaging.Aps(content_available=True))
                )
            )
            messaging.send(mensaje)
            residente_notificado = True
        except Exception as e:
            # En producción, registramos el log del error pero no bloqueamos la llamada del visitante
            print(f"❌ Error al enviar Push Firebase: {str(e)}")

    
    return {
        "room_name": room_name,
        "token_visitante": jwt_visitante,
        "token_residente": jwt_residente,
        "residente_notificado": True #dato
    }