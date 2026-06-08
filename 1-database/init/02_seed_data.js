// 02_seed_data.js
// Seed data para restaurante_fusion
// Datos de prueba para desarrollo y testing

const hoy = new Date().toISOString().split("T")[0]

// ─── MENU DEL DIA ────────────────────────────────────────────────
db.menu_del_dia.insertMany([
  {
    fecha: hoy,
    turno: "almuerzo",
    platos: [
      {
        nombre: "Arroz Chaufa",
        categoria: "principal",
        precio_base: 35,
        precio_especial: null,
        disponible: true,
        tiempo_prep_min: 15
      },
      {
        nombre: "Ceviche de Temporada",
        categoria: "entrada",
        precio_base: 28,
        precio_especial: 24,
        disponible: true,
        tiempo_prep_min: 10
      },
      {
        nombre: "Lomo Saltado",
        categoria: "principal",
        precio_base: 42,
        precio_especial: null,
        disponible: true,
        tiempo_prep_min: 20
      },
      {
        nombre: "Creme Brulee",
        categoria: "postre",
        precio_base: 18,
        precio_especial: null,
        disponible: false,
        tiempo_prep_min: 25
      },
      {
        nombre: "Chicha Morada",
        categoria: "bebida",
        precio_base: 8,
        precio_especial: null,
        disponible: true,
        tiempo_prep_min: 2
      }
    ]
  },
  {
    fecha: hoy,
    turno: "cena",
    platos: [
      {
        nombre: "Souffle de Quinua",
        categoria: "entrada",
        precio_base: 32,
        precio_especial: 28,
        disponible: true,
        tiempo_prep_min: 20
      },
      {
        nombre: "Confit de Pato con Tacu Tacu",
        categoria: "principal",
        precio_base: 58,
        precio_especial: null,
        disponible: true,
        tiempo_prep_min: 30
      },
      {
        nombre: "Tiradito Estilo Provenzal",
        categoria: "entrada",
        precio_base: 35,
        precio_especial: null,
        disponible: true,
        tiempo_prep_min: 12
      },
      {
        nombre: "Mousse de Lucuma",
        categoria: "postre",
        precio_base: 22,
        precio_especial: null,
        disponible: true,
        tiempo_prep_min: 5
      },
      {
        nombre: "Limonada de Maracuya",
        categoria: "bebida",
        precio_base: 10,
        precio_especial: null,
        disponible: true,
        tiempo_prep_min: 3
      }
    ]
  }
])

// ─── ORDENES DE PRUEBA ───────────────────────────────────────────
db.ordenes.insertMany([
  {
    mesa: NumberInt(3),
    turno: "almuerzo",
    mesero: "Ana Torres",
    estado: "En cola",
    timestamp: new Date().toISOString(),
    platos: [
      {
        nombre: "Arroz Chaufa",
        categoria: "principal",
        precio: 35,
        cantidad: NumberInt(2),
        nota: "sin cebolla"
      },
      {
        nombre: "Chicha Morada",
        categoria: "bebida",
        precio: 8,
        cantidad: NumberInt(2),
        nota: null
      }
    ]
  },
  {
    mesa: NumberInt(7),
    turno: "almuerzo",
    mesero: "Carlos Diaz",
    estado: "Preparando",
    timestamp: new Date().toISOString(),
    platos: [
      {
        nombre: "Ceviche de Temporada",
        categoria: "entrada",
        precio: 24,
        cantidad: NumberInt(1),
        nota: null
      },
      {
        nombre: "Lomo Saltado",
        categoria: "principal",
        precio: 42,
        cantidad: NumberInt(1),
        nota: "termino medio"
      }
    ]
  },
  {
    mesa: NumberInt(1),
    turno: "almuerzo",
    mesero: "Ana Torres",
    estado: "Listo",
    timestamp: new Date().toISOString(),
    platos: [
      {
        nombre: "Lomo Saltado",
        categoria: "principal",
        precio: 42,
        cantidad: NumberInt(3),
        nota: null
      }
    ]
  }
])