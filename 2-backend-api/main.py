from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from pydantic import BaseModel
from typing import List, Optional
import os
from datetime import datetime

app = FastAPI(title="API de Pedidos - Menú Fusión")

# Configuración de CORS para permitir conexiones externas si es necesario
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Conexión a MongoDB usando MONGO_URL
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017/")
client = MongoClient(MONGO_URL)
db = client["restaurante_fusion"]
ordenes_collection = db["ordenes"]
menu_collection = db["menu_del_dia"]


def serializar_documento(doc):
    doc["_id"] = str(doc["_id"])
    return doc

# Modelo de datos para validar la entrada de pedidos
class Plato(BaseModel):
    nombre: str
    categoria: str
    precio: float
    cantidad: int
    nota: Optional[str] = None

class Orden(BaseModel):
    mesa: int
    turno: str
    mesero: str
    platos: List[Plato]
    estado: str = "En cola"  # Estados: En cola, Preparando, Listo

@app.get("/")
def read_root():
    return {"status": "API Operativa", "database_connected": MONGO_URL != ""}

# 1. Endpoint para registrar una nueva orden (Usado por el mesero en Streamlit)
@app.post("/api/ordenes", status_code=201)
def crear_orden(orden: Orden):
    try:
        nueva_orden = orden.model_dump()
        nueva_orden["timestamp"] = datetime.now().isoformat()
        result = ordenes_collection.insert_one(nueva_orden)
        return {"message": "Orden registrada con éxito", "id": str(result.inserted_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 2. Endpoint para listar órdenes activas (Usado por el monitor de cocina)
@app.get("/api/ordenes/activas")
def obtener_ordenes_activas():
    try:
        # Traemos las órdenes que no están en estado "Listo"
        cursor = ordenes_collection.find({"estado": {"$ne": "Listo"}})
        return [serializar_documento(doc) for doc in cursor]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 2.1 Endpoint para listar todas las ordenes (Usado por analitica y cocina)
@app.get("/api/ordenes")
def obtener_ordenes():
    try:
        cursor = ordenes_collection.find().sort("timestamp", 1)
        return [serializar_documento(doc) for doc in cursor]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 3. Endpoint para actualizar el estado de un pedido (Ej. de 'En cola' a 'Preparando')
@app.put("/api/ordenes/{orden_id}/estado")
def actualizar_estado(orden_id: str, nuevo_estado: str = Body(embed=True)):
    from bson import ObjectId
    try:
        result = ordenes_collection.update_one(
            {"_id": ObjectId(orden_id)},
            {"$set": {"estado": nuevo_estado}}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Orden no encontrada")
        return {"message": f"Estado actualizado a {nuevo_estado}"}
    except Exception as e:
        raise HTTPException(status_code=400, detail="ID no válido o error de servidor")

# 4. Endpoint para listar órdenes listas
@app.get("/api/ordenes/listas")
def obtener_ordenes_listas():
    try:
        cursor = ordenes_collection.find({"estado": "Listo"})
        return [serializar_documento(doc) for doc in cursor]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 5. Endpoint para listar el menu del dia
@app.get("/api/menu")
def obtener_menu():
    try:
        cursor = menu_collection.find()
        return [serializar_documento(doc) for doc in cursor]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
