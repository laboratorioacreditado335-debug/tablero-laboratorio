import time
from datetime import datetime
import pandas as pd
import streamlit as st
from bs4 import BeautifulSoup
import gspread
from google.oauth2.service_account import Credentials

# ---------------------------------------------------------
# CONFIGURACIÓN DE LA PÁGINA
# ---------------------------------------------------------
st.set_page_config(
    page_title="Tablero de Control - Laboratorio de Calibración",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ---------------------------------------------------------
# ESTILOS CSS PERSONALIZADOS (MODO OSCURO)
# ---------------------------------------------------------
DARK_THEME_CSS = """
<style>
    /* Fondo principal y estructura */
    .stApp {
        background-color: #0B1120;
        color: #F3F4F6;
    }

    /* Ocultar elementos nativos innecesarios de Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Tarjetas KPI y contenedores */
    .kpi-card {
        background-color: #111827;
        border: 1px solid #1F2937;
        border-radius: 8px;
        padding: 16px;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
    }
    .kpi-title {
        font-size: 0.85rem;
        color: #9CA3AF;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 6px;
    }
    .kpi-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #3B82F6;
    }

    /* Tablas estilo Dashboard */
    .custom-table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 10px;
        background-color: #111827;
        border-radius: 8px;
        overflow: hidden;
    }
    .custom-table th {
        background-color: #1F2937;
        color: #9CA3AF;
        padding: 12px;
        text-align: left;
        font-size: 0.85rem;
        border-bottom: 1px solid #374151;
    }
    .custom-table td {
        padding: 10px 12px;
        color: #E5E7EB;
        font-size: 0.9rem;
        border-bottom: 1px solid #1F2937;
    }

    /* Badges de Estado */
    .badge {
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 600;
        display: inline-block;
    }
    .badge-ok { background-color: #064E3B; color: #34D399; }
    .badge-warning { background-color: #78350F; color: #FBBF24; }
    
    /* Animación de Parpadeo para Alertas */
    @keyframes blink {
        0% { opacity: 1; }
        50% { opacity: 0.3; }
        100% { opacity: 1; }
    }
    .badge-alert {
        background-color: #7F1D1D;
        color: #F87171;
        animation: blink 1.5s infinite;
    }

    /* Tarjetas de Bitácora / Avisos */
    .bitacora-card {
        background-color: #111827;
        border-left: 4px solid #3B82F6;
        padding: 12px;
        margin-bottom: 10px;
        border-radius: 4px;
    }
    .bitacora-card.alta { border-left-color: #EF4444; }
    .bitacora-card.media { border-left-color: #F59E0B; }
</style>
"""

st.markdown(DARK_THEME_CSS, unsafe_allow_html_ Glosario=True) if hasattr(st, "markdown") else None
st.markdown(DARK_THEME_CSS, unsafe_allow_html=True)

# ---------------------------------------------------------
# LECTURA Y PROCESAMIENTO DE DATOS (GSHEETS & PANDAS)
# ---------------------------------------------------------
def obtener_conexion_gsheets():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    credentials = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=scope
    )
    client = gspread.authorize(credentials)
    return client.open_by_key(st.secrets["SPREADSHEET_ID"])

def cargar_datos_gsheets():
    try:
        sh = obtener_conexion_gsheets()
        
        # Cargar 'C. Proceso órdenes'
        ws_ordenes = sh.worksheet("C. Proceso órdenes")
        data_ordenes = ws_ordenes.get_all_records()
        df_ordenes = pd.DataFrame(data_ordenes)

        if not df_ordenes.empty:
            # Rellenar celdas combinadas de Fecha
            if "Fecha" in df_ordenes.columns:
                df_ordenes["Fecha"] = df_ordenes["Fecha"].ffill()
            
            # Limpiar número de orden (remover decimales tipo .0)
            if "Orden" in df_ordenes.columns:
                df_ordenes["Orden"] = (
                    df_ordenes["Orden"]
                    .astype(str)
                    .str.replace(r"\.0$", "", regex=True)
                    .str.strip()
                )

        # Cargar 'NOTAS DEL DIA'
        ws_notas = sh.worksheet("NOTAS DEL DIA")
        data_notas = ws_notas.get_all_records()
        df_notas = pd.DataFrame(data_notas)

        return df_ordenes, df_notas
    except Exception as e:
        st.error(f"Error al conectar con Google Sheets: {e}")
        return pd.DataFrame(), pd.DataFrame()

# ---------------------------------------------------------
# FUNCIONES DE RENDERIZADO VISUAL
# ---------------------------------------------------------
def render_dark_table(df_page):
    if df_page.empty:
        st.info("No hay datos disponibles para mostrar en la tabla.")
        return

    html = "<table class='custom-table'><thead><tr>"
    for col in df_page.columns:
        html += f"<th>{col}</th>"
    html += "</tr></thead><tbody>"

    for _, row in df_page.iterrows():
        html += "<tr>"
        for col in df_page.columns:
            val = str(row[col])
            # Aplicar badges según contenido
            if val in ["Atascada", "Corrección"]:
                cell_content = f"<span class='badge badge-alert'>{val}</span>"
            elif val in ["Aprobación", "Pendiente"]:
                cell_content = f"<span class='badge badge-warning'>{val}</span>"
            elif val in ["Firmada", "Enviada", "Completado"]:
                cell_content = f"<span class='badge badge-ok'>{val}</span>"
            else:
                cell_content = val
            html += f"<td>{cell_content}</td>"
        html += "</tr>"
    html += "</tbody></table>"
    
    st.markdown(html, unsafe_allow_html=True)

def render_bitacora_card(nota):
    prioridad = str(nota.get("Prioridad", "Media")).lower()
    titulo = nota.get("Titulo", "Aviso sin título")
    mensaje = nota.get("Mensaje", "")
    hora = nota.get("Hora", "")

    card_html = f"""
    <div class='bitacora-card {prioridad}'>
        <div style='display: flex; justify-content: space-between; font-weight: bold; font-size: 0.9rem;'>
            <span>{titulo}</span>
            <span style='color: #9CA3AF; font-size: 0.75rem;'>{hora}</span>
        </div>
        <div style='color: #D1D5DB; font-size: 0.85rem; margin-top: 4px;'>{mensaje}</div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)

# ---------------------------------------------------------
# COMPONENTE FLUIDO CON @st.fragment
# ---------------------------------------------------------
@st.fragment(run_every=5)
def render_tablero_fluido():
    # Cargar datos
    df_ordenes, df_notas = cargar_datos_gsheets()

    # Manejo de estado de paginación y rotación (90 segundos)
    if "last_page_rotation" not in st.session_state:
        st.session_state.last_page_rotation = time.time()
        st.session_state.current_page = 0

    now = time.time()
    rows_per_page = 8
    total_rows = len(df_ordenes) if not df_ordenes.empty else 0
    total_pages = max(1, (total_rows + rows_per_page - 1) // rows_per_page)

    if now - st.session_state.last_page_rotation > 90:
        st.session_state.current_page = (st.session_state.current_page + 1) % total_pages
        st.session_state.last_page_rotation = now

    # 1. KPIs Superiores
    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
    
    reg_count = len(df_ordenes) if not df_ordenes.empty else 0
    firm_count = len(df_ordenes[df_ordenes["Estado"] == "Firmada"]) if "Estado" in df_ordenes.columns else 0
    env_count = len(df_ordenes[df_ordenes["Estado"] == "Enviada"]) if "Estado" in df_ordenes.columns else 0
    pend_count = len(df_ordenes[df_ordenes["Estado"] == "Pendiente"]) if "Estado" in df_ordenes.columns else 0

    with kpi_col1:
        st.markdown(f"<div class='kpi-card'><div class='kpi-title'>REGISTRADAS</div><div class='kpi-value'>{reg_count}</div></div>", unsafe_allow_html=True)
    with kpi_col2:
        st.markdown(f"<div class='kpi-card'><div class='kpi-title'>FIRMADAS</div><div class='kpi-value'>{firm_count}</div></div>", unsafe_allow_html=True)
    with kpi_col3:
        st.markdown(f"<div class='kpi-card'><div class='kpi-title'>ENVIADAS</div><div class='kpi-value'>{env_count}</div></div>", unsafe_allow_html=True)
    with kpi_col4:
        st.markdown(f"<div class='kpi-card'><div class='kpi-title'>PENDIENTES</div><div class='kpi-value' style='color: #F59E0B;'>{pend_count}</div></div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 2. Tabla Principal Paginada
    st.subheader(f"Órdenes en Proceso (Página {st.session_state.current_page + 1} de {total_pages})")
    if not df_ordenes.empty:
        start_idx = st.session_state.current_page * rows_per_page
        end_idx = start_idx + rows_per_page
        df_page = df_ordenes.iloc[start_idx:end_idx]
        render_dark_table(df_page)
    else:
        st.info("No se registraron datos en la hoja de proceso.")

    st.markdown("<br><hr style='border-color: #1F2937;'><br>", unsafe_allow_html=True)

    # 3. Sección Inferior (3 Columnas)
    col_prog, col_meta, col_bitacora = st.columns([1, 1, 1])

    with col_prog:
        st.subheader("📌 Programadas p/ Hoy")
        if not df_ordenes.empty and "Programada" in df_ordenes.columns:
            df_hoy = df_ordenes[df_ordenes["Programada"] == "Sí"]
            if not df_hoy.empty:
                for _, row in df_hoy.iterrows():
                    st.markdown(f"• **Orden #{row.get('Orden', 'N/A')}** - {row.get('Cliente', 'Cliente General')}")
            else:
                st.write("No hay órdenes programadas para hoy.")
        else:
            st.write("Sin programación asignada.")

    with col_meta:
        st.subheader("🎯 Meta del Día")
        meta_objetivo = 15
        despachados = env_count
        porcentaje = min(100, int((despachados / meta_objetivo) * 100)) if meta_objetivo > 0 else 0
        
        st.markdown(f"**Despachos:** {despachados} / {meta_objetivo}")
        st.progress(porcentaje / 100)
        st.caption(f"Cumplimiento del {porcentaje}% sobre la meta diaria.")

    with col_bitacora:
        st.subheader("📝 Bitácora / Avisos del Día")
        if not df_notas.empty:
            for _, nota in df_notas.iterrows():
                render_bitacora_card(nota)
        else:
            st.write("No hay avisos registrados para el día de hoy.")

# ---------------------------------------------------------
# PUNTO DE ENTRADA PRINCIPAL
# ---------------------------------------------------------
def main():
    render_tablero_fluido()

if __name__ == "__main__":
    main()
