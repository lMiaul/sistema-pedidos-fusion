import streamlit as st
import requests
from datetime import datetime
import pandas as pd
import plotly.express as px
import os
import time

# =========================================================
# CONFIGURACIÓN INICIAL
# =========================================================

st.set_page_config(
    page_title="Restaurant Fusion Pro 🍛",
    page_icon="🍛",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
</style>
""", unsafe_allow_html=True)

# =========================================================
# API CONFIG
# =========================================================

API_URL = os.getenv("API_URL", "http://localhost:8000")

# =========================================================
# FUNCIONES API
# =========================================================

@st.cache_data(ttl=5)
def obtener_ordenes():

    try:

        response = requests.get(
            f"{API_URL}/api/ordenes/activas"
        )

        if response.status_code == 200:
            return response.json()

        return []

    except Exception as e:
        st.error(f"Error conectando API: {e}")
        return []


@st.cache_data(ttl=30)
def obtener_menu():

    # OPCIÓN RÁPIDA (SIN API)

    return [{
        "fecha": "2026-06-09",
        "turno": "almuerzo",
        "platos": [
            {
                "nombre": "Lomo Saltado",
                "categoria": "fondo",
                "precio_base": 25,
                "tiempo_prep_min": 20,
                "disponible": True
            },
            {
                "nombre": "Ceviche",
                "categoria": "entrada",
                "precio_base": 30,
                "tiempo_prep_min": 15,
                "disponible": True
            },
            {
                "nombre": "Ají de Gallina",
                "categoria": "fondo",
                "precio_base": 22,
                "tiempo_prep_min": 18,
                "disponible": True
            }
        ]
    }]


def actualizar_estado(orden_id, nuevo_estado):

    try:

        response = requests.put(
            f"{API_URL}/api/ordenes/{orden_id}/estado",
            json={"nuevo_estado": nuevo_estado}
        )

        return response.status_code == 200

    except Exception as e:
        st.error(f"Error actualizando estado: {e}")
        return False


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
# CONFIGURACIÓN KANBAN
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
    },
}

ESTADOS_KANBAN = [
    "En cola",
    "Preparando",
    "Listo"
]

# =========================================================
# COMPONENTES UI
# =========================================================

def render_kanban_card(orden, estado_actual, col):

    config = ESTADOS_CONFIG[estado_actual]

    total = calcular_total_orden(
        orden["platos"]
    )

    with col:

        with st.container(border=True):

            st.markdown(
                f"""
                <div style="
                    border-left: 6px solid {config['color']};
                    padding: 10px 14px;
                    border-radius: 8px;
                    background-color: #111827;
                    margin-bottom: 10px;
                ">
                    <div style="
                        font-size: 20px;
                        font-weight: bold;
                        color: white;
                    ">
                        🍽️ Mesa {orden['mesa']}
                    </div>

                    <div style="
                        color: #9ca3af;
                        font-size: 13px;
                        margin-top: 4px;
                    ">
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
                            {plato['categoria'].capitalize()}
                            &nbsp;•&nbsp;
                            S/ {plato['precio']}
                        </small>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                if plato.get("nota"):
                    st.caption(f"📝 {plato['nota']}")

            st.success(f"💰 Total: S/ {total:.2f}")

            if config["next"]:

                if st.button(
                    f"➡️ Pasar a {config['next']}",
                    key=f"btn_{orden['_id']}_{config['next']}",
                    use_container_width=True
                ):

                    ok = actualizar_estado(
                        orden["_id"],
                        config["next"]
                    )

                    if ok:
                        st.cache_data.clear()
                        st.rerun()


def render_header_columna(estado):

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
            <span style="
                font-size: 16px;
                font-weight: bold;
                color: white;
            ">
                {config['emoji']} {estado}
            </span>
        </div>
        """,
        unsafe_allow_html=True
    )

# =========================================================
# SIDEBAR
# =========================================================

st.title("🍛 Restaurant Fusion Pro")

st.caption(
    "Sistema Inteligente de Cocina y Analítica en Tiempo Real"
)

st.sidebar.title("⚙️ Panel de Control")

st.sidebar.divider()

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
# COCINA INTERACTIVA
# =========================================================

if pagina == "👨‍🍳 Cocina Interactiva":

    st.subheader("👨‍🍳 Cocina en Tiempo Real")

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
        "Listo": col3,
    }

    for estado, col in columnas_map.items():

        with col:
            render_header_columna(estado)

    for orden in ordenes_activas:

        estado = orden["estado"]

        if estado in columnas_map:

            render_kanban_card(
                orden,
                estado,
                columnas_map[estado]
            )

    if not ordenes_activas:
        st.info("No hay órdenes activas.")

# =========================================================
# MENÚ DEL DÍA
# =========================================================

elif pagina == "📋 Menú del Día":

    st.subheader("📋 Nuevo Pedido")

    menu_actual = menu_dia[0]

    st.markdown(
        f"### 🍽️ {menu_actual['fecha']} — "
        f"{menu_actual['turno'].capitalize()}"
    )

    platos_disponibles = [

        p for p in menu_actual["platos"]

        if p["disponible"]
    ]

    with st.form(
        "nuevo_pedido",
        clear_on_submit=True
    ):

        st.markdown(
            "## 🧾 Información del Pedido"
        )

        col1, col2, col3 = st.columns(3)

        with col1:

            mesa = st.selectbox(
                "🍽️ Mesa",
                options=["Seleccionar"] + list(range(1, 11))
            )

        with col2:

            turno = st.selectbox(
                "🌙 Turno",
                options=[
                    "Seleccionar",
                    "almuerzo",
                    "cena"
                ]
            )

        with col3:

            mesero = st.selectbox(
                "👨 Nombre del mesero",
                [
                    "Seleccionar",
                    "Ana Torres",
                    "Carlos Diaz",
                    "Juan Perez",
                    "Maria Lopez"
                ]
            )

        estado = "En cola"

        st.divider()

        st.markdown(
            "## 🍛 Seleccionar Platos"
        )

        platos_pedido = []

        for plato in platos_disponibles:

            id_plato = plato["nombre"]

            precio_mostrar = plato["precio_base"]

            with st.container(border=True):

                c1, c2 = st.columns([4, 1])

                with c1:

                    agregar = st.checkbox(
                        f"{plato['nombre']} • "
                        f"S/ {precio_mostrar}",
                        key=f"check_{id_plato}"
                    )

                with c2:

                    cantidad = st.number_input(
                        "Cant",
                        min_value=1,
                        max_value=20,
                        value=1,
                        step=1,
                        key=f"cant_{id_plato}"
                    )

                nota = st.text_input(
                    "📝 Nota",
                    key=f"nota_{id_plato}"
                )

                if agregar:

                    platos_pedido.append({
                        "nombre": plato["nombre"],
                        "categoria": plato["categoria"],
                        "precio": float(precio_mostrar),
                        "cantidad": int(cantidad),
                        "nota": nota.strip()
                        if nota.strip()
                        else None
                    })

        st.divider()

        enviado = st.form_submit_button(
            "🚀 Enviar Pedido a Cocina",
            use_container_width=True
        )

    # =====================================================
    # ENVÍO
    # =====================================================

    if enviado:

        if mesa == "Seleccionar":

            st.error("Selecciona una mesa.")

        elif turno == "Seleccionar":

            st.error("Selecciona un turno.")

        elif mesero == "Seleccionar":

            st.error("Selecciona un mesero.")

        elif len(platos_pedido) == 0:

            st.error(
                "Debes seleccionar al menos un plato."
            )

        else:

            try:

                nueva_orden = {
                    "mesa": int(mesa),
                    "turno": turno,
                    "mesero": mesero,
                    "estado": estado,
                    "platos": platos_pedido
                }

                response = requests.post(
                    f"{API_URL}/api/ordenes",
                    json=nueva_orden
                )

                if response.status_code == 201:

                    st.cache_data.clear()

                    mensaje = st.success(
                        "✅ Pedido enviado correctamente."
                    )

                    time.sleep(3)

                    mensaje.empty()

                    st.rerun()

                else:

                    st.error(
                        f"Error API: {response.text}"
                    )

            except Exception as e:

                st.error(
                    f"Error enviando pedido: {e}"
                )

# =========================================================
# ANALÍTICA
# =========================================================

elif pagina == "📊 Analítica":

    st.subheader("📊 Dashboard Analítico")

    if not ordenes:

        st.warning("No existen datos.")

    else:

        total_ordenes = len(ordenes)

        total_ventas = sum(
            calcular_total_orden(o["platos"])
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
            if total_ordenes
            else 0
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
                "Turno": orden["turno"],
            }

            for orden in ordenes
            for plato in orden["platos"]
        ]

        df = pd.DataFrame(data_platos)

        st.markdown("### 🔥 Top Platos")

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
            "### 📦 Categorías Más Vendidas"
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
            "### 👨‍💼 Rendimiento de Meseros"
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
            "### 🚦 Estados de Pedidos"
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

        st.markdown("### 📋 Datos Completos")

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )
