# Usar una imagen oficial de Python ligera
FROM python:3.10-slim

# Definir el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiar primero el archivo de requerimientos para aprovechar la caché de Docker
COPY requirements.txt .

# Instalar las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código fuente del backend
COPY . .

# Exponer el puerto interno en el que correrá FastAPI
EXPOSE 8000

# Comando para iniciar la aplicación usando Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]