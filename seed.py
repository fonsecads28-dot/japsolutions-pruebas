# seed.py
import asyncio
import os
from dotenv import load_dotenv
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Importamos la configuración y los modelos exactos del proyecto
from src.config.database import Base
from src.models.db_models import Edificio, Departamento, Usuario

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("La variable de entorno DATABASE_URL no está configurada en el .env")

# Creamos el motor asíncrono temporal para la siembra
engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def sembrar_datos():
    print("⏳ Iniciando la siembra de datos de prueba...")
    
    async with AsyncSessionLocal() as session:
        async with session.begin():
            # 1. Verificar si ya existen datos para no duplicar en las pruebas
            stmt = select(Edificio).where(Edificio.token_url == "edf-Maipu-863")
            resultado = await session.execute(stmt)
            edificio_existente = resultado.scalar_one_or_none()
            
            if edificio_existente:
                print("⚠️ El edificio de prueba 'edf-Maipu-863' ya existe. Omitiendo siembra.")
                return

            print("🏢 Creando Edificio de prueba...")
            nuevo_edificio = Edificio(
                nombre="Edificio Maipú",
                direccion="Calle Maipu 863, CABA",
                token_url="edf-Maipu-863",          # Este es el token que irá en el QR del visitante
                token_mqtt="madero_secret_mqtt_99"   # El canal IoT para activar el relé físico
            )
            session.add(nuevo_edificio)
            # Hacemos un flush para que SQLAlchemy obtenga el ID autogenerado del edificio
            await session.flush()

            print("🚪 Creando Departamentos asociados...")
            unidades = ["1A", "1B", "2A", "2B", "3A", "3B", "4A", "4B","10A", "10B", "20A", "20B", "30A", "30B", "40A", "40B"]
            departamentos_creados = []
            
            for unidad in unidades:
                depto = Departamento(
                    edificio_id=nuevo_edificio.id,
                    nombre_unidad=unidad
                )
                session.add(depto)
                departamentos_creados.append(depto)
            
            await session.flush()

            print("👤 Creando Usuario Residente de prueba...")
            # Buscamos el departamento 40B en la lista que acabamos de pre-guardar
            depto_40b = next(d for d in departamentos_creados if d.nombre_unidad == "40B")
            
            usuario_residente = Usuario(
                nombre="David Fonseca",
                departamento_id=depto_40b.id,
                # Deja este token de prueba por ahora. Luego lo actualizarás con el token real de tu teléfono
                fcm_token="TOKEN_FCM_MOCK_CELULAR_PRUEBA2", 
                es_administrador=False
            )
            session.add(usuario_residente)

        # Al salir del bloque async with session.begin(), se hace el COMMIT automático en la BD
        print("🎉 ¡Base de datos poblada con éxito!")

async def main():
    # Opcional: Aseguramos que las tablas estén creadas antes de sembrar
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    await sembrar_datos()
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())