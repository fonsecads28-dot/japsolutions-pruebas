import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.config.firebase import inicializar_firebase
from src.routes.visitante import router as visitante_router
from src.routes.puertas import router as puertas_router

app = FastAPI(
    title="Smart Doorbell API",
    description="Backend asíncrono en Python para el control de videoporteros en línea mediante Códigos QR.",
    version="1.0.0"
)

# Configuración de CORS para permitir peticiones desde la Web App del visitante
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # En producción, restringe esto a los dominios autorizados de tu Frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar servicios externos en el arranque
#inicializar_firebase()

# Inclusión de módulos de enrutamiento distribuidos
app.include_router(visitante_router)
app.include_router(puertas_router)

@app.get("/")
async def root():
    return {
        "proyecto": "SMART DOORBELL API",
        "estado": "Operativo",
        "documentacion": "/docs"
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
    