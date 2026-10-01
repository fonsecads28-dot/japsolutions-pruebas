# simulador_rele.py
import os
import json
import time

try:
    from dotenv import load_dotenv  # type: ignore[import-not-found]
except ImportError:
    def load_dotenv(*args, **kwargs):
        return False

try:
    import paho.mqtt.client as mqtt  # type: ignore[import-not-found]
except ImportError:
    mqtt = None


class Client:
    """Wrapper útil para expone la API mínima que usa el simulador."""

    def __init__(self, client_id: str | None = None):
        self._client = mqtt.Client(client_id=client_id) if mqtt is not None else None
        self.on_connect = None
        self.on_message = None

    def _wrap_on_connect(self, client, userdata, flags, rc):
        if self.on_connect is not None:
            self.on_connect(self, userdata, flags, rc)

    def _wrap_on_message(self, client, userdata, msg):
        if self.on_message is not None:
            self.on_message(self, userdata, msg)

    def connect(self, host, port=1883, keepalive=60):
        if self._client is None:
            raise RuntimeError("paho-mqtt no está instalado o no está disponible.")
        self._client.on_connect = self._wrap_on_connect
        self._client.on_message = self._wrap_on_message
        return self._client.connect(host, port, keepalive)

    def subscribe(self, topic, qos=0):
        if self._client is None:
            raise RuntimeError("paho-mqtt no está instalado o no está disponible.")
        return self._client.subscribe(topic, qos=qos)

    def publish(self, topic, payload, qos=0, retain=False):
        if self._client is None:
            raise RuntimeError("paho-mqtt no está instalado o no está disponible.")
        return self._client.publish(topic, payload, qos=qos, retain=retain)

    def loop_forever(self, timeout=1.0, max_packets=10, retry_first_connection=False):
        if self._client is None:
            while True:
                time.sleep(timeout)
        return self._client.loop_forever(
            timeout=timeout,
            retry_first_connection=retry_first_connection,
        )

    def disconnect(self):
        if self._client is not None:
            self._client.disconnect()

    def __getattr__(self, name):
        if self._client is not None:
            return getattr(self._client, name)
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

# 1. Cargar las variables locales del archivo .env
load_dotenv()

MQTT_BROKER = os.getenv("MQTT_BROKER", "MQTT_BROKER=localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))

# Usamos el token MQTT exacto que inyectamos en la base de datos con el seed.py
TOKEN_MQTT_EDIFICIO = "madero_secret_mqtt_99" 
TOPICO_COMANDO = f"portero/edificios/{TOKEN_MQTT_EDIFICIO}/comando"

# 2. Configurar los callbacks de eventos de MQTT
def on_connect(client, userdata, flags, rc):
    """Se ejecuta automáticamente cuando el simulador se conecta al Broker."""
    if rc == 0:
        print("⚡ [RELÉ LOCAL] Conectado exitosamente al Broker MQTT.")
        # Nos suscribimos al canal de este edificio para escuchar órdenes
        client.subscribe(TOPICO_COMANDO, qos=1)
        print(f"👂 [RELÉ LOCAL] Escuchando en el canal: '{TOPICO_COMANDO}'")
        print("----------------------------------------------------------------")
    else:
        print(f"❌ Error de conexión al Broker MQTT. Código: {rc}")

def on_message(client, userdata, msg):
    """Se ejecuta automáticamente cuando llega una orden desde FastAPI."""
    try:
        # Decodificar el mensaje JSON enviado por tu backend en Python
        payload = json.loads(msg.payload.decode())
        print(f"📥 [NUEVA ORDEN RECIBIDA]: {payload}")
        
        # Validar que la acción sea "OPEN"
        if payload.get("action") == "OPEN":
            duracion = payload.get("duration_sec", 3)
            
            print("\n==================================================")
            print("🔓 [HARDWARE VIRTUAL]: ¡CLICK! Cerradura eléctrica LIBERADA.")
            print(f"⏱️ Manteniendo puerta abierta por {duracion} segundos...")
            print("==================================================")
            
            # Simulamos el tiempo que la puerta se queda abierta físicamente
            time.sleep(duracion)
            
            print("🔒 [HARDWARE VIRTUAL]: ¡CLACK! Pestillo cerrado nuevamente.\n")
            print("----------------------------------------------------------------")
            
    except Exception as e:
        print(f"⚠️ Error al procesar el mensaje MQTT: {str(e)}")

# 3. Inicializar el cliente del hardware virtual
def iniciar_simulador():
    print("🤖 Iniciando Simulador de Relé Físico (VP I AM HERE)...")
    
    # Configurar cliente MQTT con la API mínima del simulador
    client = Client()
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        # Conectarse al Broker de red local de pruebas
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        
        # Iniciar el bucle de escucha infinito (bloqueante para mantener el script vivo)
        client.loop_forever()
        
    except KeyboardInterrupt:
        print("\n👋 Simulador apagado correctamente.")
    except Exception as e:
        print(f"❌ Fallo crítico en el simulador: {str(e)}")

if __name__ == "__main__":
    iniciar_simulador()