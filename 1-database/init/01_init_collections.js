db.createCollection("ordenes", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["mesa", "turno", "mesero", "estado", "timestamp", "platos"],
      properties: {
        mesa: {
          bsonType: "int",
          description: "Número de mesa, requerido"
        },
        turno: {
          bsonType: "string",
          enum: ["almuerzo", "cena"],
          description: "Solo valores permitidos: almuerzo, cena"
        },
        mesero: {
          bsonType: "string",
          description: "Nombre del mesero, requerido"
        },
        estado: {
          bsonType: "string",
          enum: ["En cola", "Preparando", "Listo"],
          description: "Estados válidos definidos por la API"
        },
        timestamp: {
          bsonType: "string",
          description: "Fecha ISO 8601, generado por la API"
        },
        platos: {
          bsonType: "array",
          minItems: 1,
          description: "Debe tener al menos un plato",
          items: {
            bsonType: "object",
            required: ["nombre", "categoria", "precio", "cantidad"],
            properties: {
              nombre: {
                bsonType: "string"
              },
              categoria: {
                bsonType: "string",
                enum: ["entrada", "principal", "postre", "bebida"]
              },
              precio: {
                bsonType: "number",
                minimum: 0
              },
              cantidad: {
                bsonType: "int",
                minimum: 1
              },
              nota: {
                bsonType: "string",
                description: "Opcional"
              }
            }
          }
        }
      }
    }
  },
  validationAction: "error"
})


db.createCollection("menu_del_dia", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["fecha", "turno", "platos"],
      properties: {
        fecha: {
          bsonType: "string",
          description: "Formato YYYY-MM-DD"
        },
        turno: {
          bsonType: "string",
          enum: ["almuerzo", "cena"]
        },
        platos: {
          bsonType: "array",
          minItems: 1,
          items: {
            bsonType: "object",
            required: ["nombre", "categoria", "precio_base", "disponible", "tiempo_prep_min"],
            properties: {
              nombre: {
                bsonType: "string"
              },
              categoria: {
                bsonType: "string",
                enum: ["entrada", "principal", "postre", "bebida"]
              },
              precio_base: {
                bsonType: "number",
                minimum: 0
              },
              precio_especial: {
                bsonType: ["number", "null"],
                minimum: 0
              },
              disponible: {
                bsonType: "bool"
              },
              tiempo_prep_min: {
                bsonType: "int",
                minimum: 1
              }
            }
          }
        }
      }
    }
  },
  validationAction: "error"
})

db.ordenes.createIndex(
  { estado: 1, timestamp: 1 },
  { name: "idx_estado_timestamp" }
)

db.menu_del_dia.createIndex(
  { fecha: 1, turno: 1 },
  { unique: true, name: "idx_fecha_turno" }
)