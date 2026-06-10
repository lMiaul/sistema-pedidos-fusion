import streamlit as st
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
import pandas as pd
import plotly.express as px
import os
import time

# CONFIGURACIÓN

st.set_page_config(
    page_title="Restaurant Fusion Pro 🍛",
    page_icon="🍛",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ESTILOS

st.markdown("""
<style>

.main {
    background-color: #0f1117;
}

.block-container {
    padding-top: 1rem;
    padding-bottom: 1rem;
}

h1, h2, h3 {
    color: white;
}

[data-testid="stMetricValue"] {
    color: white;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# MONGODB
# =========================================================

MONGO_URL = os.getenv(
    "MONGO_URL",
    "mongodb://localhost:27017/"
)

client = MongoClient(MONGO_URL)

db = client["restaurante_fusion"]

ordenes_collection = db["ordenes"]

menu_collection = db["menu_del_dia"]

# =========================================================
# HELPERS

@st.cache_data(ttl=5)
def obtener_ordenes():

    ordenes = list(
        ordenes_collection.find().sort(
            "timestamp",
            1
        )
    )

    for o in ordenes:
        o["_id"] = str(o["_id"])

    return ordenes


@st.cache_data(ttl=30)
def obtener_menu():

    menu = list(menu_collection.find())

    for m in menu:
        m["_id"] = str(m["_id"])

    return menu


def actualizar_estado(orden_id, nuevo_estado):

    ordenes_collection.update_one(
        {"_id": ObjectId(orden_id)},
        {
            "$set": {
                "estado": nuevo_estado
            }
        }
    )


def calcular_total_orden(platos):

    return sum(
        p["precio"] * p["cantidad"]
        for p in platos
    )


def formatear_fecha(fecha_iso):

    try:

        fecha = datetime.fromisoformat(
            fecha_iso.replace("Z", "")
        )

        return fecha.strftime("%H:%M")

    except Exception:

        return str(fecha_iso)

# =========================================================
# KANBAN
# =========================================================

ESTADOS_CONFIG = {

    "En cola": {
        "color": "#ef4444",
        "emoji": "🔴",
        "next": "Preparando"
    },

    "Preparando": {
        "color": "#f59e0b",
        "emoji": "🟡",
        "next": "Listo"
    },

    "Listo": {
        "color": "#10b981",
        "emoji": "🟢",
        "next": None
    }
}

ESTADOS_KANBAN = [
    "En cola",
    "Preparando",
    "Listo"
]

# =========================================================
# UI COMPONENTS
# =========================================================

def render_header_columna(estado):

    config = ESTADOS_CONFIG[estado]

    st.markdown(
        f"""
        <div style="
            background: #111827;
            border-left: 5px solid {config['color']};
            padding: 10px 14px;
            border-radius: 10px;
            margin-bottom: 15px;
        ">
            <span style="
                font-size: 17px;
                font-weight: bold;
                color: white;
            ">
                {config['emoji']} {estado}
            </span>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_kanban_card(orden, estado_actual, col):
    config = ESTADOS_CONFIG[estado_actual]
    total = calcular_total_orden(orden["platos"])

    with col:
        with st.container(border=True):
            st.markdown(
                f"""
                <div style="
                    border-left: 6px solid {config['color']};
                    background: #111827;
                    padding: 12px;
                    border-radius: 12px;
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
                unsafe_allow_html=True # <--- AQUÍ ESTÁ EL CAMBIO
            )

            for plato in orden["platos"]:
                st.markdown(
                    f"""
                    <div style="
                        background: #1f2937;
                        padding: 10px 12px;
                        border-radius: 10px;
                        margin-bottom: 8px;
                        color: white;
                    ">
                        <b>{plato['cantidad']}x {plato['nombre']}</b><br>
                        <small style="color:#9ca3af;">
                            {plato['categoria'].capitalize()} &nbsp;•&nbsp; S/ {plato['precio']}
                        </small>
                    </div>
                    """,
                    unsafe_allow_html=True # <--- AQUÍ ESTÁ EL CAMBIO
                )
                if plato.get("nota"):
                    st.caption(f"📝 {plato['nota']}")

            st.success(f"💰 Total: S/ {total:.2f}")

            if config["next"]:
                if st.button(
                    f"➡️ {config['next']}",
                    key=f"btn_{orden['_id']}_{config['next']}",
                    use_container_width=True
                ):
                    actualizar_estado(orden["_id"], config["next"])
                    st.cache_data.clear()
                    st.rerun()

# =========================================================
# HEADER
# =========================================================

st.title("🍛 Restaurant Fusion Pro")

st.caption(
    "Sistema Inteligente de Cocina y Analítica en Tiempo Real"
)

st.sidebar.title("⚙️ Panel de Control")

pagina = st.sidebar.radio(
    "📂 Navegación",
    [
        "👨‍🍳 Cocina Interactiva",
        "📋 Menú del Día",
        "📊 Analítica"
    ]
)

ordenes = obtener_ordenes()

menu_dia = obtener_menu()

# =========================================================
# COCINA
# =========================================================

if pagina == "👨‍🍳 Cocina Interactiva":

    st.subheader(
        "👨‍🍳 Cocina en Tiempo Real"
    )

    busqueda = st.text_input(
        "🔎 Buscar pedido",
        placeholder="Mesa, mesero o plato..."
    )

    def coincide_busqueda(orden):

        texto = busqueda.lower()

        platos_texto = " ".join(
            p["nombre"].lower()
            for p in orden["platos"]
        )

        return (
            texto in str(orden["mesa"]).lower()
            or texto in orden["mesero"].lower()
            or texto in platos_texto
        )

    ordenes_activas = [

        o for o in ordenes

        if o["estado"] in ESTADOS_KANBAN

        and (
            coincide_busqueda(o)
            if busqueda else True
        )
    ]

    conteo = {
        e: 0
        for e in ESTADOS_KANBAN
    }

    for o in ordenes:

        if o["estado"] in conteo:

            conteo[o["estado"]] += 1

    k1, k2, k3 = st.columns(3)

    k1.metric(
        "🔴 En Cola",
        conteo["En cola"]
    )

    k2.metric(
        "🟡 Preparando",
        conteo["Preparando"]
    )

    k3.metric(
        "🟢 Listo",
        conteo["Listo"]
    )

    st.divider()

    col1, col2, col3 = st.columns(3)

    columnas_map = {
        "En cola": col1,
        "Preparando": col2,
        "Listo": col3
    }

    for estado, col in columnas_map.items():
        with col:
            render_header_columna(estado)
            
            ordenes_estado = [o for o in ordenes_activas if o["estado"] == estado]
            
            for orden in ordenes_estado:
                # Aquí pasas el objeto 'col' que viene del diccionario
                render_kanban_card(orden, estado, col)

    if not ordenes_activas:

        st.info(
            "No hay órdenes activas."
        )

# =========================================================
# NUEVO PEDIDO
# =========================================================

elif pagina == "📋 Menú del Día":

    st.subheader("📋 Nuevo Pedido")

    if not menu_dia:

        st.warning(
            "No hay menú registrado."
        )

    else:

        menu_actual = menu_dia[0]

        st.markdown(
            f"""
            ### 🍽️
            {menu_actual['fecha']}
            —
            {menu_actual['turno'].capitalize()}
            """
        )

        platos_disponibles = [

            p for p in menu_actual["platos"]

            if p["disponible"]
        ]

        with st.form(
            "nuevo_pedido",
            clear_on_submit=True
        ):

            col1, col2, col3 = st.columns(3)

            with col1:

                mesa = st.selectbox(
                    "🍽️ Mesa",
                    ["Seleccionar"] + list(range(1, 11))
                )

            with col2:

                turno = st.selectbox(
                    "🌙 Turno",
                    [
                        "Seleccionar",
                        "almuerzo",
                        "cena"
                    ]
                )

            with col3:

                mesero = st.selectbox(
                    "👨 Mesero",
                    [
                        "Seleccionar",
                        "Ana Torres",
                        "Carlos Diaz",
                        "Juan Perez",
                        "Maria Lopez"
                    ]
                )

            st.divider()

            platos_pedido = []

            for plato in platos_disponibles:

                with st.container(border=True):

                    c1, c2 = st.columns([4, 1])

                    with c1:

                        agregar = st.checkbox(
                            f"{plato['nombre']} • S/ {plato['precio_base']}",
                            key=f"check_{plato['nombre']}"
                        )

                    with c2:

                        cantidad = st.number_input(
                            "Cant",
                            min_value=1,
                            max_value=20,
                            value=1,
                            key=f"cant_{plato['nombre']}"
                        )

                    nota = st.text_input(
                        "📝 Nota",
                        key=f"nota_{plato['nombre']}"
                    )

                    if agregar:

                        platos_pedido.append({

                            "nombre": plato["nombre"],

                            "categoria": plato["categoria"],

                            "precio": float(
                                plato["precio_base"]
                            ),

                            "cantidad": int(
                                cantidad
                            ),

                            "nota": (
                                nota.strip()
                                if nota.strip()
                                else None
                            )
                        })

            enviado = st.form_submit_button(
                "🚀 Enviar Pedido",
                use_container_width=True
            )

        if enviado:

            if mesa == "Seleccionar":

                st.error(
                    "Selecciona una mesa."
                )

            elif turno == "Seleccionar":

                st.error(
                    "Selecciona un turno."
                )

            elif mesero == "Seleccionar":

                st.error(
                    "Selecciona un mesero."
                )

            elif len(platos_pedido) == 0:

                st.error(
                    "Selecciona platos."
                )

            else:

                try:

                    nueva_orden = {

                        "mesa": int(mesa),

                        "turno": turno,

                        "mesero": mesero,

                        "estado": "En cola",

                        "timestamp":
                        datetime.utcnow().isoformat(),

                        "platos": platos_pedido
                    }

                    resultado = (
                        ordenes_collection.insert_one(
                            nueva_orden
                        )
                    )

                    if resultado.inserted_id:

                        st.cache_data.clear()

                        mensaje = st.success(
                            "✅ Pedido enviado."
                        )

                        time.sleep(2)

                        mensaje.empty()

                        st.rerun()

                except Exception as e:

                    st.error(
                        f"Error: {e}"
                    )

# =========================================================
# ANALÍTICA
# =========================================================

elif pagina == "📊 Analítica":

    st.subheader(
        "📊 Dashboard Analítico"
    )

    if not ordenes:

        st.warning(
            "No existen datos."
        )

    else:

        total_ordenes = len(ordenes)

        total_ventas = sum(
            calcular_total_orden(
                o["platos"]
            )
            for o in ordenes
        )

        platos_totales = sum(
            sum(
                p["cantidad"]
                for p in o["platos"]
            )
            for o in ordenes
        )

        ticket_promedio = (
            total_ventas / total_ordenes
        )

        k1, k2, k3, k4 = st.columns(4)

        k1.metric(
            "📦 Órdenes",
            total_ordenes
        )

        k2.metric(
            "💰 Ventas",
            f"S/ {total_ventas:.2f}"
        )

        k3.metric(
            "🍽️ Platos",
            platos_totales
        )

        k4.metric(
            "🧾 Ticket",
            f"S/ {ticket_promedio:.2f}"
        )

        st.divider()

        data_platos = [

            {
                "Plato": plato["nombre"],
                "Categoría": plato["categoria"],
                "Cantidad": plato["cantidad"],
                "Precio": plato["precio"],
                "Mesero": orden["mesero"],
                "Mesa": orden["mesa"],
                "Estado": orden["estado"],
                "Turno": orden["turno"]
            }

            for orden in ordenes

            for plato in orden["platos"]
        ]

        df = pd.DataFrame(data_platos)

        st.markdown(
            "### 🔥 Top Platos"
        )

        top_platos = (

            df.groupby("Plato")["Cantidad"]

            .sum()

            .reset_index()

            .sort_values(
                "Cantidad",
                ascending=True
            )
        )

        fig1 = px.bar(
            top_platos,
            x="Cantidad",
            y="Plato",
            orientation="h",
            height=500
        )

        st.plotly_chart(
            fig1,
            use_container_width=True
        )

        st.markdown(
            "### 📦 Categorías"
        )

        categorias = (

            df.groupby("Categoría")["Cantidad"]

            .sum()

            .reset_index()
        )

        fig2 = px.pie(
            categorias,
            names="Categoría",
            values="Cantidad",
            height=450
        )

        st.plotly_chart(
            fig2,
            use_container_width=True
        )

        st.markdown(
            "### 👨‍💼 Meseros"
        )

        meseros = (

            df.groupby("Mesero")["Cantidad"]

            .sum()

            .reset_index()

            .sort_values(
                "Cantidad",
                ascending=True
            )
        )

        fig3 = px.bar(
            meseros,
            x="Cantidad",
            y="Mesero",
            orientation="h",
            height=450
        )

        st.plotly_chart(
            fig3,
            use_container_width=True
        )

        st.markdown(
            "### 🚦 Estados"
        )

        estados = (

            df.groupby("Estado")

            .size()

            .reset_index(name="Total")
        )

        fig4 = px.bar(
            estados,
            x="Estado",
            y="Total",
            height=400
        )

        st.plotly_chart(
            fig4,
            use_container_width=True
        )

        st.markdown(
            "### 📋 Datos"
        )

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )
