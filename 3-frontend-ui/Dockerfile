# Usar una imagen oficial de Python ligera
FROM python:3.10-slim

# Definir el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiar primero el archivo de requerimientos para aprovechar la caché de Docker
COPY requirements.txt .

# Instalar las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código de la aplicación
COPY . .

# Exponer puerto 8501 (puerto por defecto de Streamlit)
EXPOSE 8501

# Configurar Streamlit para producción
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0

# Usamos el módulo de Python directamente, es más seguro y evita errores de PATH
CMD ["python3", "-m", "streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]