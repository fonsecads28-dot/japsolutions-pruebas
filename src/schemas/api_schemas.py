from importlib import import_module
from typing import Any, List

try:
    _pydantic = import_module("pydantic")
    BaseModel = _pydantic.BaseModel
    ConfigDict = getattr(_pydantic, "ConfigDict", None)
except ImportError:  # pragma: no cover
    class BaseModel:
        def _init_(self, **data: Any) -> None:
            self._dict_.update(data)

    def ConfigDict(**kwargs: Any) -> dict[str, Any]:
        return kwargs

# 1. Esquema interno para listar departamentos
class DepartamentoInList(BaseModel):
    id: int
    unidad: str

    if ConfigDict is not None:
        model_config = ConfigDict(from_attributes=True)
    else:
        class Config:
            from_attributes = True
            orm_mode = True

# 2. Esquema para la carga inicial del código QR
class ConfigurarQRResponse(BaseModel):
    edificio_nombre: str
    edificio_id: int
    directorios: List[DepartamentoInList]


# 🔥 3. CORREGIDO: Lo que ENVÍA la página web del visitante (Petición de Entrada)
class IniciarLlamadaQRRequest(BaseModel):
    departamento_id: int
    nombre_visitante: str


# 🔥 4. CORREGIDO: Lo que DEVUELVE Python al navegador (Respuesta de Salida)
class IniciarLlamadaQRResponse(BaseModel):
    room_name: str
    token_visitante: str
    token_residente_local: str  # Campo habilitado para que JavaScript lo pueda leer
    residente_notificado: bool


# 5. Esquemas para la Apertura Domótica (MQTT)
class AperturaRequest(BaseModel):
    edificio_id: int
    usuario_id: int