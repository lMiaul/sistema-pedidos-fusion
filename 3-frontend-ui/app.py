import streamlit as st
from pymongo import MongoClient
from datetime import datetime
import pandas as pd
import plotly.express as px
import os

# CONFIGURACIÓN INICIAL

st.set_page_config(
    page_title="Restaurant Fusion Pro 🍛",
    page_icon="🍛",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
.main { background-color: #0f1117; }
.block-container { padding-top: 1rem; padding-bottom: 1rem; }
h1, h2, h3 { color: white; }
</style>
""", unsafe_allow_html=True)


# CONEXIÓN MONGODB

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017/")
client = MongoClient(MONGO_URL)
db = client["restaurante_fusion"]
ordenes_collection = db["ordenes"]
menu_collection = db["menu_del_dia"]


# funciones 

@st.cache_data(ttl=5)
def obtener_ordenes():
    return list(ordenes_collection.find().sort("timestamp", 1))


@st.cache_data(ttl=30)
def obtener_menu():
    return list(menu_collection.find())


def actualizar_estado(orden_id, nuevo_estado):
    ordenes_collection.update_one(
        {"_id": orden_id},
        {"$set": {"estado": nuevo_estado}}
    )


def calcular_total_orden(platos):
    return sum(p["precio"] * p["cantidad"] for p in platos)


def formatear_fecha(fecha_iso):
    try:
        fecha = datetime.fromisoformat(fecha_iso.replace("Z", ""))
        return fecha.strftime("%H:%M")
    except Exception:
        return str(fecha_iso)


# CONFIGURACIÓN KANBAN

ESTADOS_CONFIG = {
    "En cola":    {"color": "#ef4444", "emoji": "🔴", "next": "Preparando"},
    "Preparando": {"color": "#f59e0b", "emoji": "🟡", "next": "Listo"},
    "Listo":      {"color": "#10b981", "emoji": "🟢", "next": None},
}

ESTADOS_KANBAN = ["En cola", "Preparando", "Listo"]


# COMPONENTES UI

def render_kanban_card(orden, estado_actual, col):
    """Renderiza una tarjeta kanban para una orden."""
    config = ESTADOS_CONFIG[estado_actual]
    total = calcular_total_orden(orden["platos"])

    with col:
        with st.container(border=True):

            # Encabezado: solo datos estáticos en HTML
            st.markdown(
                f"""
                <div style="
                    border-left: 6px solid {config['color']};
                    padding: 10px 14px;
                    border-radius: 8px;
                    background-color: #111827;
                    margin-bottom: 10px;
                ">
                    <div style="font-size: 20px; font-weight: bold; color: white;">
                        🍽️ Mesa {orden['mesa']}
                    </div>
                    <div style="color: #9ca3af; font-size: 13px; margin-top: 4px;">
                        👨 {orden['mesero']}
                        &nbsp;•&nbsp;
                        🕒 {formatear_fecha(orden['timestamp'])}
                        &nbsp;•&nbsp;
                        🌙 {orden['turno'].capitalize()}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            # Platos: solo datos estáticos en HTML
            for plato in orden["platos"]:
                st.markdown(
                    f"""
                    <div style="
                        background: #1f2937;
                        padding: 9px 12px;
                        border-radius: 8px;
                        margin-bottom: 6px;
                        color: white;
                    ">
                        <b>{plato['cantidad']}x {plato['nombre']}</b><br>
                        <small style="color: #9ca3af;">
                            {plato['categoria'].capitalize()} &nbsp;•&nbsp; S/ {plato['precio']}
                        </small>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                if plato.get("nota"):
                    st.caption(f"📝 {plato['nota']}")

            # Total y botón: componentes nativos de Streamlit
            st.success(f"💰 Total: S/ {total:.2f}")

            if config["next"]:
                if st.button(
                    f"➡️ Pasar a {config['next']}",
                    key=f"btn_{orden['_id']}_{config['next']}",
                    use_container_width=True
                ):
                    actualizar_estado(orden["_id"], config["next"])
                    st.cache_data.clear()
                    st.rerun()


def render_header_columna(estado):
    """Renderiza el encabezado de cada columna kanban."""
    config = ESTADOS_CONFIG[estado]
    st.markdown(
        f"""
        <div style="
            background-color: #111827;
            border-left: 5px solid {config['color']};
            padding: 8px 14px;
            border-radius: 8px;
            margin-bottom: 12px;
        ">
            <span style="font-size: 16px; font-weight: bold; color: white;">
                {config['emoji']} {estado}
            </span>
        </div>
        """,
        unsafe_allow_html=True
    )


# SIDEBAR Y NAVEGACIÓN
st.title("🍛 Restaurant Fusion Pro")
st.caption("Sistema Inteligente de Cocina y Analítica en Tiempo Real")

st.sidebar.title("⚙️ Panel de Control")
st.sidebar.divider()

pagina = st.sidebar.radio(
    "📂 Navegación",
    ["👨‍🍳 Cocina Interactiva", "📋 Menú del Día", "📊 Analítica"]
)

ordenes = obtener_ordenes()
menu_dia = obtener_menu()


# PÁGINA: COCINA INTERACTIVA
if pagina == "👨‍🍳 Cocina Interactiva":

    st.subheader("👨‍🍳 Cocina en Tiempo Real")

    busqueda = st.text_input(
        "🔎 Buscar pedido",
        placeholder="Mesa, mesero o plato..."
    )

    def coincide_busqueda(orden):
        texto = busqueda.lower()
        platos_texto = " ".join(p["nombre"].lower() for p in orden["platos"])
        return (
            texto in str(orden["mesa"]).lower()
            or texto in orden["mesero"].lower()
            or texto in platos_texto
        )

    ordenes_activas = [
        o for o in ordenes
        if o["estado"] in ESTADOS_KANBAN
        and o["turno"] in ("almuerzo", "cena")
        and (coincide_busqueda(o) if busqueda else True)
    ]

    # KPIs
    conteo = {e: 0 for e in ESTADOS_KANBAN}
    for o in ordenes:
        if o["estado"] in conteo:
            conteo[o["estado"]] += 1

    k1, k2, k3 = st.columns(3)
    k1.metric("🔴 En Cola",    conteo["En cola"])
    k2.metric("🟡 Preparando", conteo["Preparando"])
    k3.metric("🟢 Listo",      conteo["Listo"])

    st.divider()

    # Tablero kanban
    col1, col2, col3 = st.columns(3)
    columnas_map = {
        "En cola":    col1,
        "Preparando": col2,
        "Listo":      col3,
    }

    # Encabezados de columna
    for estado, col in columnas_map.items():
        with col:
            render_header_columna(estado)

    # Tarjetas por estado
    for orden in ordenes_activas:
        estado = orden["estado"]
        if estado in columnas_map:
            render_kanban_card(orden, estado, columnas_map[estado])

    if not ordenes_activas:
        st.info("No hay órdenes activas en este momento.")


# PÁGINA: MENÚ DEL DÍA
elif pagina == "📋 Menú del Día":

    st.subheader("📋 Nuevo Pedido")

    if not menu_dia:

        st.warning("No hay menú registrado.")

    else:

        menu_actual = menu_dia[0]

        st.markdown(
            f"### 🍽️ {menu_actual['fecha']} — {menu_actual['turno'].capitalize()}"
        )

        platos_disponibles = [
            p for p in menu_actual["platos"]
            if p["disponible"]
        ]

        with st.form("nuevo_pedido"):

            col1, col2 = st.columns(2)

            with col1:

                mesa = st.number_input(
                    "🍽️ Mesa",
                    min_value=1,
                    step=1
                )

                mesero = st.text_input(
                    "👨 Nombre del mesero"
                )

            with col2:

                turno = st.selectbox(
                    "🌙 Turno",
                    ["almuerzo", "cena"]
                )

                estado = "En cola"

            st.divider()

            st.markdown("### 🍛 Seleccionar Platos")

            platos_pedido = []

            for plato in platos_disponibles:

                with st.container(border=True):

                    c1, c2 = st.columns([3,1])

                    with c1:

                        agregar = st.checkbox(
                            f"{plato['nombre']} • S/ {plato.get('precio_especial', plato['precio_base'])}",
                            key=f"check_{plato['nombre']}"
                        )

                    with c2:

                        cantidad = st.number_input(
                            "Cantidad",
                            min_value=1,
                            max_value=20,
                            value=1,
                            key=f"cant_{plato['nombre']}"
                        )

                    nota = st.text_input(
                        "Nota",
                        placeholder="Ej: sin cebolla",
                        key=f"nota_{plato['nombre']}"
                    )

                    if agregar:

                        platos_pedido.append({

                            "nombre": plato["nombre"],

                            "categoria": plato["categoria"],

                            "precio": plato.get(
                                "precio_especial",
                                plato["precio_base"]
                            ),

                            "cantidad": cantidad,

                            "nota": nota if nota else None
                        })

            enviado = st.form_submit_button(
                "🚀 Enviar Pedido a Cocina",
                use_container_width=True
            )

            if enviado:

                if not mesero.strip():

                    st.error("Ingresa el nombre del mesero.")

                elif not platos_pedido:

                    st.error("Debes seleccionar al menos un plato.")

                else:

                    nueva_orden = {

                        "mesa": int(mesa),

                        "turno": turno,

                        "mesero": mesero,

                        "estado": estado,

                        "timestamp": datetime.utcnow().isoformat(),

                        "platos": platos_pedido
                    }

                    ordenes_collection.insert_one(
                        nueva_orden
                    )

                    st.cache_data.clear()

                    st.success(
                        "✅ Pedido enviado correctamente a cocina."
                    )

                    st.rerun()

        st.divider()

        st.markdown("### 🍽️ Menú Disponible")

        columnas = st.columns(3)

        for idx, plato in enumerate(platos_disponibles):

            with columnas[idx % 3]:

                precio = plato.get(
                    "precio_especial",
                    plato["precio_base"]
                )

                with st.container(border=True):

                    st.markdown(
                        f"### {plato['nombre']}"
                    )

                    st.caption(
                        plato["categoria"].capitalize()
                    )

                    st.write(f"💵 S/ {precio}")

                    st.write(
                        f"⏱️ {plato['tiempo_prep_min']} min"
                    )

                    st.success("🟢 Disponible")



# PÁGINA: ANALÍTICA
elif pagina == "📊 Analítica":

    st.subheader("📊 Dashboard Analítico")

    if not ordenes:
        st.warning("No existen datos.")
    else:
        total_ordenes = len(ordenes)
        total_ventas  = sum(calcular_total_orden(o["platos"]) for o in ordenes)
        platos_totales = sum(
            sum(p["cantidad"] for p in o["platos"]) for o in ordenes
        )
        ticket_promedio = total_ventas / total_ordenes if total_ordenes else 0

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("📦 Órdenes",  total_ordenes)
        k2.metric("💰 Ventas",   f"S/ {total_ventas:.2f}")
        k3.metric("🍽️ Platos",  platos_totales)
        k4.metric("🧾 Ticket",   f"S/ {ticket_promedio:.2f}")

        st.divider()

        # Construir DataFrame
        data_platos = [
            {
                "Plato":     plato["nombre"],
                "Categoría": plato["categoria"],
                "Cantidad":  plato["cantidad"],
                "Precio":    plato["precio"],
                "Mesero":    orden["mesero"],
                "Mesa":      orden["mesa"],
                "Estado":    orden["estado"],
                "Turno":     orden["turno"],
            }
            for orden in ordenes
            for plato in orden["platos"]
        ]
        df = pd.DataFrame(data_platos)

        # Top platos
        st.markdown("### 🔥 Top Platos")
        top_platos = (
            df.groupby("Plato")["Cantidad"]
            .sum()
            .reset_index()
            .sort_values("Cantidad", ascending=True)
        )
        fig1 = px.bar(
            top_platos,
            x="Cantidad", y="Plato",
            orientation="h", height=500
        )
        st.plotly_chart(fig1, use_container_width=True)

        # Categorías
        st.markdown("### 📦 Categorías Más Vendidas")
        categorias = df.groupby("Categoría")["Cantidad"].sum().reset_index()
        fig2 = px.pie(
            categorias,
            names="Categoría", values="Cantidad",
            height=450
        )
        st.plotly_chart(fig2, use_container_width=True)

        # Meseros
        st.markdown("### 👨‍💼 Rendimiento de Meseros")
        meseros = (
            df.groupby("Mesero")["Cantidad"]
            .sum()
            .reset_index()
            .sort_values("Cantidad", ascending=True)
        )
        fig3 = px.bar(
            meseros,
            x="Cantidad", y="Mesero",
            orientation="h", height=450
        )
        st.plotly_chart(fig3, use_container_width=True)

        # Estados
        st.markdown("### 🚦 Estados de Pedidos")
        estados = df.groupby("Estado").size().reset_index(name="Total")
        fig4 = px.bar(estados, x="Estado", y="Total", height=400)
        st.plotly_chart(fig4, use_container_width=True)

        # Tabla completa
        st.markdown("### 📋 Datos Completos")
        st.dataframe(df, use_container_width=True, hide_index=True)