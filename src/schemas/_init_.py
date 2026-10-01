#validacion de la estructura de datos de entrada y salida de la API
from .api_schemas import (
    DepartamentoInList,
    ConfigurarQRResponse,
    IniciarLlamadaQRRequest,
    IniciarLlamadaQRResponse,
    AperturaRequest
)

_all_ = [
    "DepartamentoInList",
    "ConfigurarQRResponse",
    "IniciarLlamadaQRRequest",
    "IniciarLlamadaQRResponse",
    "AperturaRequest"
)