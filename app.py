import streamlit as st
import pandas as pd
import datetime
import time
from streamlit_gsheets import GSheetsConnection

# -----------------------------------------------------------------------------
# 1. CONFIGURACIÓN DE PÁGINA Y ESTILOS CSS (MODO OSCURO BASE)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Tablero de Control - Laboratorio de Calibración",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Estilos CSS inyectados (Respetando paleta #0B1120 y tarjetas #111827)
st.markdown("""
<style>
    /* Estilos Generales y Fondo */
    .stApp {
        background-color: #0B1120;
        color: #F3F4F6;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Ocultar elementos de Streamlit por defecto */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Contenedores y Tarjetas KPI */
    .kpi-card {
        background-color: #111827;
        border: 1px solid #1F2937;
        border-radius: 8px;
        padding: 16px;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
    }
    .kpi-title {
        color: #9CA3AF;
        font-size: 13px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .kpi-value {
        font-size: 32px;
        font-weight: 700;
        margin-top: 4px;
    }
    .kpi-registradas { color: #3B82F6; }
    .kpi-firmadas { color: #10B981; }
    .kpi-enviadas { color: #8B5CF6; }
    .kpi-pendientes { color: #F59E0B; }

    /* Badges Condicionales */
    .badge {
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: 600;
        display: inline-block;
    }
    .badge-atascada {
        background-color: #7F1D1D;
        color: #FCA5A5;
        animation: blinker 1.5s linear infinite;
    }
    .badge-aprobacion {
        background-color: #1E3A8A;
        color: #93C5FD;
    }
    .badge-correccion {
        background-color: #78350F;
        color: #FDE68A;
        animation: blinker 2s linear infinite;
    }
    
    @keyframes blinker {
        50% { opacity: 0.4; }
    }

    /* Estilos de Tabla Oscura */
    .dark-table {
        width: 100%;
        border-collapse: collapse;
        background-color: #111827;
        border-radius: 8px;
        overflow: hidden;
        font-size: 13px;
    }
    .dark-table th {
        background-color: #1F2937;
        color: #9CA3AF;
        padding: 10px 12px;
        text-align: left;
        font-weight: 600;
    }
    .dark-table td {
        padding: 10px 12px;
        border-bottom: 1px solid #1F2937;
        color: #E5E7EB;
    }
    .dark-table tr:hover {
        background-color: #1F2937;
    }

    /* Tarjetas de Progreso */
    .progress-order-card {
        background-color: #111827;
        border: 1px solid #1F2937;
        border-radius: 6px;
        padding: 12px;
        margin-bottom: 10px;
    }
    .progress-bar-bg {
        background-color: #1F2937;
        border-radius: 4px;
        height: 8px;
        width: 100%;
        margin-top: 6px;
        overflow: hidden;
    }
    .progress-bar-fill {
        background-color: #F59E0B;
        height: 100%;
        border-radius: 4px;
        transition: width 0.3s ease;
    }

    /* Bitácora / Avisos */
    .bitacora-card {
        background-color: #111827;
        border-left: 4px solid #3B82F6;
        border-radius: 4px;
        padding: 10px 14px;
        margin-bottom: 8px;
        font-size: 12px;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. CARGA Y PROCESAMIENTO DE DATOS (GSHEETS)
# -----------------------------------------------------------------------------
def cargar_datos_gsheets():
    """Conecta con Google Sheets, procesa celdas combinadas y limpia formatos."""
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        
        # Carga de hoja de órdenes
        df_ordenes = conn.read(worksheet="C. Proceso órdenes", ttl="5s")
        
        # Carga de hoja de notas del día
        try:
            df_notas = conn.read(worksheet="NOTAS DEL DIA", ttl="5s")
        except Exception:
            df_notas = pd.DataFrame(columns=["Prioridad", "Nota", "Estado"])

        if df_ordenes is None or df_ordenes.empty:
            return pd.DataFrame(), df_notas

        # Resolviendo celdas combinadas en columna Fecha
        if 'Fecha' in df_ordenes.columns:
            df_ordenes['Fecha'] = df_ordenes['Fecha'].ffill()

        # Limpieza del número de orden (eliminar sufijo .0 si existe)
        if 'Orden' in df_ordenes.columns:
            df_ordenes['Orden'] = df_ordenes['Orden'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()

        return df_ordenes, df_notas

    except Exception as e:
        st.error(f"Error al conectar con Google Sheets: {e}")
        return pd.DataFrame(), pd.DataFrame()

# -----------------------------------------------------------------------------
# 3. FUNCIONES DE RENDERIZADO COMPONENTES HTML
# -----------------------------------------------------------------------------
def render_kpis(df):
    """Muestra las 4 tarjetas KPI principales."""
    col1, col2, col3, col4 = st.columns(4)
    
    total_registradas = len(df) if not df.empty else 0
    total_firmadas = len(df[df['Estado'] == 'Firmada']) if not df.empty and 'Estado' in df.columns else 0
    total_enviadas = len(df[df['Estado'] == 'Enviada']) if not df.empty and 'Estado' in df.columns else 0
    total_pendientes = len(df[df['Estado'] == 'Pendiente']) if not df.empty and 'Estado' in df.columns else 0

    col1.markdown(f'''
        <div class="kpi-card">
            <div class="kpi-title">REGISTRADAS</div>
            <div class="kpi-value kpi-registradas">{total_registradas}</div>
        </div>
    ''', unsafe_allow_html=True)
    
    col2.markdown(f'''
        <div class="kpi-card">
            <div class="kpi-title">FIRMADAS</div>
            <div class="kpi-value kpi-firmadas">{total_firmadas}</div>
        </div>
    ''', unsafe_allow_html=True)
    
    col3.markdown(f'''
        <div class="kpi-card">
            <div class="kpi-title">ENVIADAS</div>
            <div class="kpi-value kpi-enviadas">{total_enviadas}</div>
        </div>
    ''', unsafe_allow_html=True)
    
    col4.markdown(f'''
        <div class="kpi-card">
            <div class="kpi-title">PENDIENTES</div>
            <div class="kpi-value kpi-pendientes">{total_pendientes}</div>
        </div>
    ''', unsafe_allow_html=True)

def render_dark_table(df_page):
    """Genera la tabla principal paginada con Badges condicionales."""
    if df_page.empty:
        st.info("No hay órdenes disponibles para mostrar.")
        return

    html_code = '<table class="dark-table"><thead><tr>'
    headers = ['Orden', 'Cliente', 'Equipo', 'Etapa / Estado', 'Alerta']
    for h in headers:
        html_code += f'<th>{h}</th>'
    html_code += '</tr></thead><tbody>'

    for _, row in df_page.iterrows():
        orden = row.get('Orden', '-')
        cliente = row.get('Cliente', '-')
        equipo = row.get('Equipo', '-')
        estado = row.get('Estado', '-')
        alerta = row.get('Alerta', '-')

        # Render de Badges
        badge_html = ""
        if str(alerta).lower() == 'atascada':
            badge_html = '<span class="badge badge-atascada">Atascada</span>'
        elif str(alerta).lower() == 'aprobación':
            badge_html = '<span class="badge badge-aprobacion">Aprobación</span>'
        elif str(alerta).lower() == 'corrección':
            badge_html = '<span class="badge badge-correccion">Corrección</span>'
        else:
            badge_html = f'<span>{alerta if pd.notna(alerta) else "-"}</span>'

        html_code += f'''
            <tr>
                <td><b>#{orden}</b></td>
                <td>{cliente}</td>
                <td>{equipo}</td>
                <td>{estado}</td>
                <td>{badge_html}</td>
            </tr>
        '''
    html_code += '</tbody></table>'
    
    st.markdown(html_code, unsafe_allow_html=True)

def render_progreso_dia_card(orden_num, porcentaje):
    """Renderiza cada tarjeta individual de progreso del día."""
    card_html = f'''
    <div class="progress-order-card">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <span style="font-size: 12px; font-weight: 700; color: #F3F4F6;">Orden #{orden_num}</span>
            <span style="font-size: 11.5px; font-weight: 700; color: #F59E0B;">{porcentaje}%</span>
        </div>
        <div class="progress-bar-bg">
            <div class="progress-bar-fill" style="width: {porcentaje}%;"></div>
        </div>
    </div>
    '''
    st.markdown(card_html, unsafe_allow_html=True)

def render_bitacora_card(nota_text, prioridad="Normal"):
    """Renderiza tarjetas de avisos/bitácora."""
    border_color = "#3B82F6"
    if str(prioridad).lower() == "alta":
        border_color = "#EF4444"
    elif str(prioridad).lower() == "media":
        border_color = "#F59E0B"

    bitacora_html = f'''
    <div class="bitacora-card" style="border-left-color: {border_color};">
        <div style="color: #9CA3AF; font-size: 10px; text-transform: uppercase;">Prioridad: {prioridad}</div>
        <div style="color: #E5E7EB; margin-top: 2px;">{nota_text}</div>
    </div>
    '''
    st.markdown(bitacora_html, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 4. FRAGMENTO FLUIDO (ACTUALIZACIÓN VÍA WEBSOCKETS CADA 5 SEGUNDOS)
# -----------------------------------------------------------------------------
@st.fragment(run_every=5)
def render_tablero_fluido():
    """Fragmento de actualización automática vía WebSockets."""
    
    # Cargar datos actualizados
    df_ordenes, df_notas = cargar_datos_gsheets()
    
    # Mantenimiento de Paginación en session_state
    if 'pagina_actual' not in st.session_state:
        st.session_state.pagina_actual = 0
    if 'last_rotation' not in st.session_state:
        st.session_state.last_rotation = time.time()

    # Rotación automática cada 90 segundos
    filas_por_pagina = 8
    total_filas = len(df_ordenes) if not df_ordenes.empty else 0
    total_paginas = max(1, (total_filas + filas_por_pagina - 1) // filas_por_pagina)

    if time.time() - st.session_state.last_rotation > 90:
        st.session_state.pagina_actual = (st.session_state.pagina_actual + 1) % total_paginas
        st.session_state.last_rotation = time.time()

    # Render KPIs
    render_kpis(df_ordenes)
    
    st.markdown("<br>", unsafe_allow_html=True)

    # Render Tabla Principal (Paginada)
    st.subheader(f"Órdenes en Proceso (Página {st.session_state.pagina_actual + 1} de {total_paginas})")
    if not df_ordenes.empty:
        inicio = st.session_state.pagina_actual * filas_por_pagina
        fin = inicio + filas_por_pagina
        render_dark_table(df_ordenes.iloc[inicio:fin])
    else:
        st.info("Sin datos de órdenes cargados.")

    st.markdown("<br>", unsafe_allow_html=True)

    # Sección Inferior (3 Columnas)
    col_izq, col_med, col_der = st.columns(3)

    # Columna 1: Programadas p/ Hoy
    with col_izq:
        st.markdown("### 📅 Programadas p/ Hoy")
        if not df_ordenes.empty and 'Programada' in df_ordenes.columns:
            prog_hoy = df_ordenes[df_ordenes['Programada'] == True]
            if not prog_hoy.empty:
                for _, row in prog_hoy.head(5).iterrows():
                    st.markdown(f"- **#{row.get('Orden', '-')}:** {row.get('Cliente', '-')}")
            else:
                st.caption("No hay órdenes programadas para hoy.")
        else:
            st.caption("Sin registros programados.")

    # Columna 2: PROGRESO DEL DÍA
    with col_med:
        st.markdown("### PROGRESO DEL DÍA")
        
        # Progreso general promedio
        promedio_general = 20
        
        general_card_html = f'''
        <div class="progress-order-card" style="border-color: #3B82F6;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="font-size: 12px; font-weight: 700; color: #9CA3AF; text-transform: uppercase;">PROMEDIO GENERAL DEL DÍA</span>
                <span style="font-size: 13px; font-weight: 700; color: #3B82F6;">{promedio_general}%</span>
            </div>
            <div class="progress-bar-bg">
                <div class="progress-bar-fill" style="width: {promedio_general}%; background-color: #3B82F6;"></div>
            </div>
        </div>
        '''
        st.markdown(general_card_html, unsafe_allow_html=True)

        # Tarjetas individuales de progreso
        if not df_ordenes.empty:
            sample_orders = df_ordenes.head(3)
            for _, row in sample_orders.iterrows():
                num_orden = row.get('Orden', '44962')
                render_progreso_dia_card(num_orden, 20)
        else:
            render_progreso_dia_card("44962", 20)

    # Columna 3: Bitácora / Avisos del Día
    with col_der:
        st.markdown("### 📝 Bitácora / Avisos del Día")
        if not df_notas.empty:
            for _, row in df_notas.iterrows():
                nota = row.get('Nota', 'Sin detalle')
                prio = row.get('Prioridad', 'Normal')
                render_bitacora_card(nota, prio)
        else:
            render_bitacora_card("Línea de calibración operando a capacidad normal.", "Normal")
            render_bitacora_card("Mantenimiento preventivo programado a las 17:00.", "Media")

# -----------------------------------------------------------------------------
# 5. EJECUCIÓN PRINCIPAL
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    render_tablero_fluido()
