# 1-database — Restaurante Fusion

Capa de base de datos del sistema de pedidos Menu Fusion.
Gestiona el almacenamiento de ordenes en tiempo real y el menu del dia
mediante MongoDB 7.0 ejecutado en un contenedor Docker.

---

## Tecnologias

- MongoDB 7.0 (imagen oficial Docker)
- Inicializacion automatica via docker-entrypoint-initdb.d
- Validacion de esquema con $jsonSchema (MongoDB Schema Validation)

---

## Estructura

```
1-database/
├── init/
│   ├── 01_init_collections.js   # Crea colecciones e indices
│   └── 02_seed_data.js          # Datos de prueba
└── README.md
```

---

## Colecciones

### ordenes
Almacena cada pedido registrado por la API.
Escrita por: API (Mauricio)
Leida por: Dashboard de cocina (Marisol)

Campos requeridos: mesa, turno, mesero, estado, timestamp, platos

Estados validos:
- "En cola"
- "Preparando"  
- "Listo"

Turnos validos:
- "almuerzo"
- "cena"

### menu_del_dia
Almacena los platos disponibles por fecha y turno.
Leida por: API para validacion, Dashboard para mostrar carta.

Restriccion: combinacion fecha + turno es unica (indice unique).

---

## Decisiones de Diseno

### Por que MongoDB y no SQL

Una orden de restaurante tiene estructura variable por naturaleza:
cantidad de platos, notas personalizadas, variaciones. Modelar esto
en SQL requiere multiples tablas y joins en cada lectura del dashboard.
MongoDB permite leer una orden completa en un solo documento.

Fuente: Fowler, M. & Sadalage, P. (2012). NoSQL Distilled. 
Addison-Wesley. Cap. 2: Aggregate Data Models.

### Embebido vs Referencia

Los platos se embeben dentro de la orden como snapshot al momento
del pedido. Esto preserva el precio historico aunque el menu cambie.

Fuente: MongoDB. (2024). Schema Design Patterns — Subset Pattern.
https://www.mongodb.com/blog/post/building-with-patterns-a-summary

### Validacion de esquema

Se usa $jsonSchema con validationAction: "error" para rechazar
documentos invalidos en tiempo de escritura, no de lectura.

Fuente: MongoDB. (2024). Schema Validation.
https://www.mongodb.com/docs/manual/core/schema-validation

---

## URI de Conexion para la API

La API debe conectarse usando el nombre del servicio Docker,
no localhost:

```
mongodb://admin:secret@mongodb:27017/restaurante_fusion?authSource=admin
```

Donde:
- admin / secret → credenciales definidas en docker-compose.yml
- mongodb        → nombre del servicio en docker-compose.yml
- authSource     → requerido cuando se usa autenticacion

---

## Como levantar solo la base de datos

Desde la raiz del proyecto:

```bash
docker compose up mongodb
```

Para construir la imagen y forzar re-inicializacion completa:

```bash
docker compose down -v
docker compose up mongodb --build
```

Primera vez: MongoDB ejecuta automaticamente los scripts en init/
en orden alfabetico (01 antes que 02).

Para verificar que los datos se cargaron:

```bash
docker exec -it menu_fusion_mongo mongosh \
  -u admin -p secret \
  --authenticationDatabase admin \
  restaurante_fusion \
  --eval "db.ordenes.countDocuments()"
```

---

## Indices creados

| Coleccion | Campos | Tipo | Proposito |
|---|---|---|---|
| ordenes | estado, timestamp | Compuesto | Consultas del dashboard |
| menu_del_dia | fecha, turno | Unico | Un menu por turno por dia |

---

## Datos de prueba incluidos

02_seed_data.js inserta:
- 2 menus del dia (almuerzo y cena) con 5 platos cada uno
- 3 ordenes en distintos estados para probar el dashboard

---

### Dockerfile

Se usa un Dockerfile personalizado en lugar de la imagen oficial directa por dos razones concretas:

1. Los scripts de init se copian dentro de la imagen con `COPY init/`. Esto garantiza que
   los datos de prueba esten disponibles independientemente del estado del volumen, a 
   diferencia del montaje por volumen donde el seed solo corre si el volumen esta vacio.

2. Se agrega un `HEALTHCHECK` que verifica que MongoDB responde antes de que otros
   servicios intenten conectarse. Mauricio puede usar `depends_on: condition: service_healthy`
   en su servicio de API para evitar errores de conexion en el arranque.

> Fuente: Docker, Inc. (2024). *Dockerfile reference — HEALTHCHECK*.
> https://docs.docker.com/reference/dockerfile/#healthcheck

---

## Autor

Ale Veliz
Rol: Base de datos
Rama: feat/database