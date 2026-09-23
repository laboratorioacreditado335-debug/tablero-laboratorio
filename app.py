import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import time
from datetime import datetime
import json

# ==========================================
# CONFIGURACIÓN DE LA PÁGINA
# ==========================================
st.set_page_config(
    page_title="Tablero de Control - Laboratorio de Calibración",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==========================================
# ESTILOS CSS PERSONALIZADOS (MODO OSCURO)
# ==========================================
CUSTOM_CSS = """
<style>
    /* Fondo principal y contenedor */
    .stApp {
        background-color: #0B1120;
        color: #F3F4F6;
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
    }
    
    /* Encabezado */
    .header-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 1rem 0rem;
        border-bottom: 1px solid #1E293B;
        margin-bottom: 1.5rem;
    }
    .header-title {
        font-size: 1.75rem;
        font-weight: 700;
        color: #F9FAFB;
        margin: 0;
    }
    .header-status {
        font-size: 0.875rem;
        color: #10B981;
        background-color: rgba(16, 185, 129, 0.1);
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        border: 1px solid rgba(16, 185, 129, 0.2);
    }

    /* Tarjetas KPI */
    .kpi-card {
        background-color: #111827;
        border: 1px solid #1E293B;
        border-radius: 0.75rem;
        padding: 1.25rem;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
    }
    .kpi-title {
        font-size: 0.85rem;
        font-weight: 600;
        color: #9CA3AF;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.5rem;
    }
    .kpi-value {
        font-size: 2.25rem;
        font-weight: 800;
        color: #F9FAFB;
    }

    /* Tabla Principal */
    .table-container {
        background-color: #111827;
        border: 1px solid #1E293B;
        border-radius: 0.75rem;
        padding: 1rem;
        margin-top: 1.5rem;
        margin-bottom: 1.5rem;
    }
    .custom-table {
        width: 100%;
        border-collapse: collapse;
        color: #E5E7EB;
        font-size: 0.9rem;
    }
    .custom-table th {
        background-color: #1F2937;
        color: #9CA3AF;
        text-transform: uppercase;
        font-size: 0.75rem;
        letter-spacing: 0.05em;
        padding: 0.75rem 1rem;
        text-align: left;
        border-bottom: 1px solid #374151;
    }
    .custom-table td {
        padding: 0.75rem 1rem;
        border-bottom: 1px solid #1F2937;
    }
    .custom-table tr:hover {
        background-color: #1E293B;
    }

    /* Badges con animación */
    .badge {
        padding: 0.25rem 0.6rem;
        border-radius: 0.375rem;
        font-size: 0.75rem;
        font-weight: 600;
        display: inline-block;
    }
    .badge-atascada {
        background-color: rgba(239, 68, 68, 0.2);
        color: #EF4444;
        border: 1px solid rgba(239, 68, 68, 0.4);
        animation: blink 1.5s infinite;
    }
    .badge-aprobacion {
        background-color: rgba(245, 158, 11, 0.2);
        color: #F59E0B;
        border: 1px solid rgba(245, 158, 11, 0.4);
    }
    .badge-correccion {
        background-color: rgba(59, 130, 246, 0.2);
        color: #3B82F6;
        border: 1px solid rgba(59, 130, 246, 0.4);
    }
    .badge-normal {
        background-color: rgba(107, 114, 128, 0.2);
        color: #9CA3AF;
        border: 1px solid rgba(107, 114, 128, 0.4);
    }

    @keyframes blink {
        0% { opacity: 1; }
        50% { opacity: 0.3; }
        100% { opacity: 1; }
    }

    /* Sección de 3 columnas inferior */
    .sec-card {
        background-color: #111827;
        border: 1px solid #1E293B;
        border-radius: 0.75rem;
        padding: 1.25rem;
        height: 100%;
    }
    .sec-title {
        font-size: 1rem;
        font-weight: 700;
        color: #F9FAFB;
        margin-bottom: 1rem;
        border-bottom: 1px solid #1E293B;
        padding-bottom: 0.5rem;
    }

    /* Tarjetas de Bitácora */
    .bitacora-item {
        background-color: #1F2937;
        border-left: 4px solid #3B82F6;
        border-radius: 0.375rem;
        padding: 0.75rem;
        margin-bottom: 0.75rem;
    }
    .bitacora-urgente { border-left-color: #EF4444; }
    .bitacora-revision { border-left-color: #F59E0B; }
    .bitacora-normal { border-left-color: #3B82F6; }
    
    .bitacora-prioridad {
        font-size: 0.7rem;
        font-weight: 700;
        text-transform: uppercase;
        margin-bottom: 0.25rem;
    }
    .bitacora-desc {
        font-size: 0.85rem;
        color: #E5E7EB;
    }
    .bitacora-estado {
        font-size: 0.75rem;
        color: #9CA3AF;
        margin-top: 0.25rem;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ==========================================
# CONEXIÓN BÚSQUEDA EXACTA DE CREDENCIALES
# ==========================================
@st.cache_resource
def get_gspread_client():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    
    creds_dict = None

    # 1. Verificar si la raíz de secrets tiene los datos directos
    if "client_email" in st.secrets and "private_key" in st.secrets:
        creds_dict = dict(st.secrets)
    else:
        # 2. Buscar en todas las secciones/bloques de secrets el objeto real de credenciales
        for key, val in st.secrets.items():
            if hasattr(val, "get") or isinstance(val, dict):
                if "client_email" in val and "private_key" in val:
                    creds_dict = dict(val)
                    break
            elif isinstance(val, str) and "client_email" in val and "private_key" in val:
                try:
                    creds_dict = json.loads(val)
                    break
                except Exception:
                    pass
        
        # 3. Buscar en conexiones integradas (connections.gsheets)
        if not creds_dict and "connections" in st.secrets and "gsheets" in st.secrets["connections"]:
            conn = st.secrets["connections"]["gsheets"]
            if "client_email" in conn and "private_key" in conn:
                creds_dict = dict(conn)

    if not creds_dict:
        raise ValueError("No se encontraron credenciales válidas en st.secrets (debe incluir 'client_email' y 'private_key').")

    # Formatear saltos de línea de la clave privada
    if "private_key" in creds_dict and isinstance(creds_dict["private_key"], str):
        creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")

    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    return gspread.authorize(creds)

def cargar_datos_gsheets():
    client = get_gspread_client()
    spreadsheet_id = st.secrets["SPREADSHEET_ID"]
    sh = client.open_by_key(spreadsheet_id)
    
    # 1. Hoja C. Proceso órdenes
    ws_ordenes = sh.worksheet("C. Proceso órdenes")
    data_ordenes = ws_ordenes.get_all_records()
    df_ordenes = pd.DataFrame(data_ordenes)
    
    # Limpieza de datos
    if 'Fecha' in df_ordenes.columns:
        df_ordenes['Fecha'] = df_ordenes['Fecha'].ffill()
    if 'Orden' in df_ordenes.columns:
        df_ordenes['Orden'] = df_ordenes['Orden'].astype(str).str.replace(r'\.0$', '', regex=True)

    # 2. Hoja NOTAS DEL DIA
    ws_notas = sh.worksheet("NOTAS DEL DIA")
    data_notas = ws_notas.get_all_records()
    df_notas = pd.DataFrame(data_notas)
    
    # Lectura de la celda de alarma (E4)
    try:
        alarm_trigger = ws_notas.acell("E4").value
        alarm_trigger = str(alarm_trigger) if alarm_trigger else "0"
    except Exception:
        alarm_trigger = "0"
        
    return df_ordenes, df_notas, alarm_trigger

# ==========================================
# RENDERIZADO DE COMPONENTES
# ==========================================
def render_kpis(df):
    reg = len(df[df['Estado'].str.contains('REGISTRADA', case=False, na=False)]) if 'Estado' in df.columns else 0
    firm = len(df[df['Estado'].str.contains('FIRMADA', case=False, na=False)]) if 'Estado' in df.columns else 0
    env = len(df[df['Estado'].str.contains('ENVIADA', case=False, na=False)]) if 'Estado' in df.columns else 0
    pend = len(df[df['Estado'].str.contains('PENDIENTE', case=False, na=False)]) if 'Estado' in df.columns else 0

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f'<div class="kpi-card"><div class="kpi-title">Registradas</div><div class="kpi-value" style="color:#3B82F6;">{reg}</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="kpi-card"><div class="kpi-title">Firmadas</div><div class="kpi-value" style="color:#10B981;">{firm}</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="kpi-card"><div class="kpi-title">Enviadas</div><div class="kpi-value" style="color:#8B5CF6;">{env}</div></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="kpi-card"><div class="kpi-title">Pendientes</div><div class="kpi-value" style="color:#F59E0B;">{pend}</div></div>', unsafe_allow_html=True)

def render_dark_table(df_page):
    table_html = """
    <div class="table-container">
        <table class="custom-table">
            <thead>
                <tr>
                    <th>Orden</th>
                    <th>Cliente</th>
                    <th>Equipo / Instrumento</th>
                    <th>Estado</th>
                    <th>Alerta / Prioridad</th>
                </tr>
            </thead>
            <tbody>
    """
    
    for _, row in df_page.iterrows():
        orden = row.get('Orden', '-')
        cliente = row.get('Cliente', '-')
        equipo = row.get('Equipo', row.get('Instrumento', '-'))
        estado = row.get('Estado', 'NORMAL')
        alerta = str(row.get('Alerta', 'NORMAL')).upper()
        
        badge_class = "badge-normal"
        if "ATASCADA" in alerta:
            badge_class = "badge-atascada"
        elif "APROBACIÓN" in alerta or "APROBACION" in alerta:
            badge_class = "badge-aprobacion"
        elif "CORRECCIÓN" in alerta or "CORRECCION" in alerta:
            badge_class = "badge-correccion"
            
        table_html += f"""
            <tr>
                <td style="font-weight:700; color:#F3F4F6;">{orden}</td>
                <td>{cliente}</td>
                <td>{equipo}</td>
                <td>{estado}</td>
                <td><span class="badge {badge_class}">{alerta}</span></td>
            </tr>
        """
        
    table_html += """
            </tbody>
        </table>
    </div>
    """
    st.markdown(table_html, unsafe_allow_html=True)

def render_bitacora_card(row):
    prioridad = str(row.get('PO / PRIORIDA', row.get('PRIORIDAD', 'NORMAL'))).upper()
    descripcion = row.get('DESCRIPCIÓN DE LA NOTA O AVISO', row.get('DESCRIPCION', ''))
    estado = row.get('ESTADO', '')
    
    p_class = "bitacora-normal"
    p_color = "#3B82F6"
    if "URGENTE" in prioridad:
        p_class = "bitacora-urgente"
        p_color = "#EF4444"
    elif "REVISIÓN" in prioridad or "REVISION" in prioridad:
        p_class = "bitacora-revision"
        p_color = "#F59E0B"
        
    st.markdown(f"""
        <div class="bitacora-item {p_class}">
            <div class="bitacora-prioridad" style="color: {p_color};">{prioridad}</div>
            <div class="bitacora-desc">{descripcion}</div>
            <div class="bitacora-estado">Estado: <b>{estado}</b></div>
        </div>
    """, unsafe_allow_html=True)

# ==========================================
# FRAGMENTO DE ACTUALIZACIÓN EN TIEMPO REAL
# ==========================================
@st.fragment(run_every=5)
def render_tablero_fluido():
    # Cargar datos desde Google Sheets
    try:
        df_ordenes, df_notas, alarm_trigger = cargar_datos_gsheets()
    except Exception as e:
        st.error(f"Error cargando datos de Google Sheets: {e}")
        return

    # --------------------------------------
    # LÓGICA DE ALARMA SONORA DE NOTIFICACIÓN
    # --------------------------------------
    if 'last_alarm' not in st.session_state:
        st.session_state['last_alarm'] = alarm_trigger

    # Si cambia el valor de control en la celda E4
    if alarm_trigger != st.session_state['last_alarm'] and alarm_trigger != "0":
        st.session_state['last_alarm'] = alarm_trigger
        st.toast("🔔 ¡NUEVA ALERTA RECIBIDA DESDE LA HOJA DE CÁLCULO!", icon="🔔")
        
        # Reproducción de tono melodioso tipo Chime por HTML5
        audio_html = """
            <audio autoplay style="display:none;">
                <source src="https://assets.mixkit.co/active_storage/sfx/2869/2869-preview.mp3" type="audio/mpeg">
            </audio>
        """
        st.components.v1.html(audio_html, height=0)

    # --------------------------------------
    # Paginación Automática de la Tabla (90s)
    # --------------------------------------
    if 'page_index' not in st.session_state:
        st.session_state['page_index'] = 0
        st.session_state['last_page_switch'] = time.time()
        
    rows_per_page = 8
    total_rows = len(df_ordenes)
    total_pages = max(1, (total_rows + rows_per_page - 1) // rows_per_page)
    
    if time.time() - st.session_state['last_page_switch'] > 90:
        st.session_state['page_index'] = (st.session_state['page_index'] + 1) % total_pages
        st.session_state['last_page_switch'] = time.time()

    current_page = st.session_state['page_index']
    start_idx = current_page * rows_per_page
    end_idx = start_idx + rows_per_page
    df_page = df_ordenes.iloc[start_idx:end_idx] if not df_ordenes.empty else pd.DataFrame()

    # --------------------------------------
    # RENDERING DE COMPONENTES DE INTERFAZ
    # --------------------------------------
    # Encabezado
    st.markdown(f"""
        <div class="header-container">
            <div>
                <h1 class="header-title">Tablero de Control - Laboratorio de Calibración</h1>
                <span style="color:#6B7280; font-size:0.85rem;">Sincronizado con Google Sheets</span>
            </div>
            <div class="header-status">● EN VIVO (Página {current_page + 1}/{total_pages})</div>
        </div>
    """, unsafe_allow_html=True)

    # KPIs
    render_kpis(df_ordenes)

    # Tabla Principal
    render_dark_table(df_page)

    # Sección Inferior (3 Columnas)
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown('<div class="sec-card"><div class="sec-title">Programadas p/ Hoy</div>', unsafe_allow_html=True)
        if not df_ordenes.empty and 'Fecha' in df_ordenes.columns:
            hoy = datetime.now().strftime('%Y-%m-%d')
            prog_hoy = df_ordenes[df_ordenes['Fecha'].astype(str).str.contains(hoy, na=False)]
            if not prog_hoy.empty:
                for _, r in prog_hoy.head(5).iterrows():
                    st.markdown(f"• **{r.get('Orden','')}** - {r.get('Cliente','')}")
            else:
                st.info("No hay órdenes programadas con fecha de hoy.")
        else:
            st.info("Sin datos de programación.")
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="sec-card"><div class="sec-title">Meta del Día</div>', unsafe_allow_html=True)
        completadas = len(df_ordenes[df_ordenes['Estado'].str.contains('ENVIADA|FIRMADA', case=False, na=False)]) if not df_ordenes.empty and 'Estado' in df_ordenes.columns else 0
        meta = 20
        pct = min(100, int((completadas / meta) * 100)) if meta > 0 else 0
        
        st.metric(label="Despachos Cumplidos", value=f"{completadas} / {meta}", delta=f"{pct}% logrado")
        st.progress(pct / 100)
        st.markdown('</div>', unsafe_allow_html=True)

    with col3:
        st.markdown('<div class="sec-card"><div class="sec-title">Bitácora / Avisos del Día</div>', unsafe_allow_html=True)
        if not df_notas.empty:
            for _, r in df_notas.head(4).iterrows():
                render_bitacora_card(r)
        else:
            st.write("Sin avisos registrados hoy.")
        st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# PUNTO DE ENTRADA PRINCIPAL
# ==========================================
def main():
    render_tablero_fluido()

if __name__ == "__main__":
    main()
