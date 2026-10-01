#iniciacion segura del SDK DE FIREBASE
import os
import firebase_admin
from firebase_admin import credentials
from dotenv import load_dotenv

load_dotenv()

def inicializar_firebase() -> None:
    """Inicializa de manera segura el SDK de administración de Firebase."""
    if not firebase_admin._apps:
        ruta_credenciales = os.getenv("FIREBASE_JSON_PATH", "firebase-credentials.json")
        
        if not os.path.exists(ruta_credenciales):
            print(f"⚠️ Alerta: Archivo de credenciales Firebase '{ruta_credenciales}' no encontrado.")
            print("Las funciones de notificaciones push fallarán hasta que se configure correctamente.")
            return

        try:
            cred = credentials.Certificate(ruta_credenciales)
            firebase_admin.initialize_app(cred)
            print("🚀 SDK de Firebase inicializado correctamente.")
        except Exception as e:
            print(f"❌ Error crítico al inicializar Firebase: {str(e)}")

