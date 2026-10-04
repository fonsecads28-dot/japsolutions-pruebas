# Usa una imagen oficial de Python ligera
FROM python:3.11-slim

# Evita que Python escriba archivos .pyc y almacene en caché logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Establece el directorio de trabajo dentro del contenedor en la nube
WORKDIR /app

# Instala dependencias del sistema necesarias para compilar librerías en Linux
RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev && rm -rf /var/lib/apt/lists/*

# Copia e instala los requerimientos de tu proyecto
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo el código de tu proyecto al contenedor
COPY . .

# Expone el puerto estándar que exige Google Cloud Run
EXPOSE 8080

# 🔥 ESTA ES LA LÍNEA CRÍTICA: Configura el puerto 8080 para la nube de Google
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]