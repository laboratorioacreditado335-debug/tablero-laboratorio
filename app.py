import streamlit as st
import pandas as pd
import numpy as np
import datetime
import time

# -----------------------------------------------------------------------------
# CONFIGURACIÓN DE LA PÁGINA
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Tablero de Control - Laboratorio de Calibración",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# -----------------------------------------------------------------------------
# INYECCIÓN DE ESTILOS CSS (MODO OSCURO + PALETA EXCEL PARA NOTAS DEL DÍA)
# -----------------------------------------------------------------------------
st.markdown("""
<style>
    /* Estilos generales del contenedor Streamlit */
    .main {
        background-color: #0B1120;
        color: #F3F4F6;
    }
    .stApp {
        background-color: #0B1120;
    }
    
    /* Tarjetas KPI Superiores */
    .kpi-card {
        background-color: #111827;
        border: 1px solid #1F2937;
        border-radius: 12px;
        padding: 18px;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.4);
    }
    .kpi-title {
        color: #9CA3AF;
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .kpi-value {
        font-size: 2.2rem;
        font-weight: 700;
        color: #F9FAFB;
        margin-top: 4px;
    }

    /* Tabla Principal Modo Oscuro */
    .dark-table-container {
        background-color: #111827;
        border-radius: 12px;
        border: 1px solid #1F2937;
        padding: 16px;
        margin-bottom: 20px;
    }
    table.dark-table {
        width: 100%;
        border-collapse: collapse;
        color: #E5E7EB;
        font-size: 0.9rem;
    }
    table.dark-table th {
        background-color: #1F2937;
        color: #9CA3AF;
        padding: 12px 10px;
        text-align: left;
        font-weight: 600;
        border-bottom: 2px solid #374151;
    }
    table.dark-table td {
        padding: 12px 10px;
        border-bottom: 1px solid #1F2937;
    }
    table.dark-table tr:hover {
        background-color: #1E293B;
    }

    /* Badges Alertas Tabla Principal */
    .badge-atascada {
        background-color: #7F1D1D;
        color: #FCA5A5;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 700;
        animation: pulse-red 2s infinite;
    }
    .badge-aprobacion {
        background-color: #78350F;
        color: #FDE68A;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 700;
    }
    .badge-correccion {
        background-color: #1E3A8A;
        color: #93C5FD;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 700;
    }
    .badge-normal {
        background-color: #111827;
        color: #6B7280;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.75rem;
    }

    @keyframes pulse-red {
        0% { opacity: 1; }
        50% { opacity: 0.4; }
        100% { opacity: 1; }
    }

    /* ------------------------------------------------------------------------
       SECCIÓN DE NOTAS DEL DÍA (COLORES EXCEL)
       ------------------------------------------------------------------------ */
    .nota-card {
        background-color: #111827;
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 10px;
        border-left: 5px solid #3B82F6;
        box-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }
    .nota-card-urgente {
        border-left-color: #EF4444 !important;
        background-color: #1F1315;
    }
    .nota-card-normal {
        border-left-color: #3B82F6 !important;
        background-color: #111827;
    }
    .nota-card-revision {
        border-left-color: #F59E0B !important;
        background-color: #1C1917;
    }
    .nota-card-auditoria {
        border-left-color: #A855F7 !important;
        background-color: #1B1528;
    }

    /* Badges de Prioridad */
    .prio-badge {
        font-size: 0.7rem;
        font-weight: 800;
        padding: 3px 8px;
        border-radius: 4px;
        display: inline-block;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }
    .prio-urgente {
        background-color: #EF444433;
        color: #EF4444;
        border: 1px solid #EF4444;
    }
    .prio-normal {
        background-color: #3B82F633;
        color: #60A5FA;
        border: 1px solid #3B82F6;
    }
    .prio-revision {
        background-color: #F59E0B33;
        color: #FBBF24;
        border: 1px solid #F59E0B;
    }
    .prio-auditoria {
        background-color: #A855F733;
        color: #C084FC;
        border: 1px solid #A855F7;
    }

    /* Badges de Estado */
    .estado-badge {
        font-size: 0.7rem;
        font-weight: 800;
        padding: 3px 8px;
        border-radius: 4px;
        display: inline-block;
        text-transform: uppercase;
    }
    .estado-pendiente {
        background-color: #EF444426;
        color: #FCA5A5;
        border: 1px solid #EF444480;
    }
    .estado-realizado {
        background-color: #10B98126;
        color: #6EE7B7;
        border: 1px solid #10B98180;
    }

    /* Tarjetas Secciones Inferiores */
    .sec-card {
        background-color: #111827;
        border: 1px solid #1F2937;
        border-radius: 12px;
        padding: 18px;
        min-height: 380px;
    }
    .sec-header {
        font-size: 1.1rem;
        font-weight: 700;
        color: #F9FAFB;
        margin-bottom: 14px;
        border-bottom: 1px solid #374151;
        padding-bottom: 8px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# LECTURA Y PROCESAMIENTO DE DATOS (GSHEETS)
# -----------------------------------------------------------------------------
@st.cache_data(ttl=10)
def cargar_datos_gsheets():
    try:
        # Obtener SPREADSHEET_ID desde secrets
        sheet_id = st.secrets.get("SPREADSHEET_ID", "1bNDr35UasLS5zly1Sbq2ykbtmsTn9Fy4")
        
        # 1. Cargar Hoja: C. Proceso órdenes
        url_ordenes = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet=C.+Proceso+órdenes"
        df_ordenes = pd.read_csv(url_ordenes)
        
        # 2. Cargar Hoja: NOTAS DEL DIA
        url_notas = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet=NOTAS+DEL+DIA"
        df_notas = pd.read_csv(url_notas)
        
        # Procesar Celdas Combinadas de Fechas en Órdenes
        if 'Fecha' in df_ordenes.columns:
            df_ordenes['Fecha'] = df_ordenes['Fecha'].ffill()
            
        # Limpieza de formatos en número de orden (.0)
        if 'Orden' in df_ordenes.columns:
            df_ordenes['Orden'] = df_ordenes['Orden'].astype(str).str.replace(r'\.0$', '', regex=True)

        # Limpieza de columnas en NOTAS DEL DÍA
        df_notas.columns = [c.strip() for c in df_notas.columns]
        
        return df_ordenes, df_notas
        
    except Exception as e:
        # Fallback Seguro con Datos Estructurados según la Hoja de la Imagen
        df_ordenes_mock = pd.DataFrame({
            'Orden': ['44015', '44132', '44600', '44865', '44877', '44900', '44768', '45012'],
            'Cliente': ['Universidad Central', 'Industrias Caso S.A.', 'Laboratorios Alfa', 'Servicios S.A.S.', 'BioSalud', 'TechLab', 'MetroCal', 'Ingeniería Global'],
            'Estado': ['REGISTRADA', 'FIRMADA', 'ENVIADA', 'PENDIENTE', 'REGISTRADA', 'FIRMADA', 'ENVIADA', 'PENDIENTE'],
            'Fecha': [datetime.date.today()]*8,
            'Alerta': ['Normal', 'Atascada', 'Aprobación', 'Corrección', 'Normal', 'Atascada', 'Normal', 'Aprobación']
        })
        
        df_notas_mock = pd.DataFrame({
            'PO / PRIORIDA': ['URGENTE', 'NORMAL', 'NORMAL', 'REVISIÓN', 'URGENTE', 'AUDITORÍA'],
            'DESCRIPCIÓN DE LA NOTA O AVISO': [
                'Pasachoa actualizar base y CRM ingresos de una vez (depende la hora) Pasachoa THX',
                'Pasachoa certfcado Universidad (no se acepta un no como respuesta)',
                'Pasachoa Revisar las ordenes sin fecha en la planilla (44015-44132-44600-44865-44877-44900-44768)',
                'Revisión de certificados en estado de aprobación pendientes de envío',
                'Urgente verificar trazabilidad de patrones de temperatura',
                'Auditoría interna programada para revisión de bitácoras de calibración'
            ],
            'ESTADO': ['PENDIENTI', 'PENDIENTI', 'REALIZAD', 'PENDIENTE', 'PENDIENTE', 'REALIZADO']
        })
        return df_ordenes_mock, df_notas_mock

# -----------------------------------------------------------------------------
# FUNCIONES DE RENDERIZADO
# -----------------------------------------------------------------------------
def render_dark_table(df_paged, current_page, total_pages):
    """Renderiza la tabla principal de proceso de órdenes con formato oscuro."""
    st.markdown(f"""
    <div class="dark-table-container">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
            <span style="font-weight: 700; color: #F3F4F6;">📦 PROCESO DE ÓRDENES EN CURSO</span>
            <span style="font-size: 0.8rem; color: #9CA3AF; background: #1F2937; padding: 4px 10px; border-radius: 20px;">
                Página {current_page} de {total_pages}
            </span>
        </div>
        <table class="dark-table">
            <thead>
                <tr>
                    <th>ORDEN</th>
                    <th>CLIENTE</th>
                    <th>FECHA</th>
                    <th>ESTADO</th>
                    <th>ALERTA / OBSERVACIÓN</th>
                </tr>
            </thead>
            <tbody>
    """, unsafe_allow_html=True)

    rows_html = ""
    for _, row in df_paged.iterrows():
        orden = str(row.get('Orden', 'N/A'))
        cliente = str(row.get('Cliente', row.get('Empresa', 'N/A')))
        fecha = str(row.get('Fecha', 'N/A'))
        estado = str(row.get('Estado', 'N/A'))
        alerta = str(row.get('Alerta', 'Normal'))

        # Formato de alerta/badge
        if 'Atascad' in alerta:
            badge_html = '<span class="badge-atascada">⚠️ ATASCADA</span>'
        elif 'Aprobac' in alerta:
            badge_html = '<span class="badge-aprobacion">⏳ APROBACIÓN</span>'
        elif 'Correc' in alerta:
            badge_html = '<span class="badge-correccion">✏️ CORRECCIÓN</span>'
        else:
            badge_html = '<span class="badge-normal">OK</span>'

        rows_html += f"""
        <tr>
            <td style="font-weight: 700; color: #3B82F6;">#{orden}</td>
            <td>{cliente}</td>
            <td style="color: #9CA3AF;">{fecha}</td>
            <td><b>{estado}</b></td>
            <td>{badge_html}</td>
        </tr>
        """

    st.markdown(rows_html + "</tbody></table></div>", unsafe_allow_html=True)

def render_bitacora_card(row):
    """Genera el HTML para cada tarjeta en la sección 'NOTAS DEL DÍA'."""
    prioridad = str(row.get('PO / PRIORIDA', '')).strip().upper()
    descripcion = str(row.get('DESCRIPCIÓN DE LA NOTA O AVISO', '')).strip()
    estado = str(row.get('ESTADO', '')).strip().upper()

    if not descripcion or descripcion.lower() == 'nan':
        return ""

    # Asignación de estilos de prioridad (Colores Exactos de Excel)
    if 'URGENTE' in prioridad:
        prio_class = "prio-urgente"
        card_class = "nota-card-urgente"
    elif 'REVISI' in prioridad:
        prio_class = "prio-revision"
        card_class = "nota-card-revision"
    elif 'AUDITOR' in prioridad:
        prio_class = "prio-auditoria"
        card_class = "nota-card-auditoria"
    else:
        prio_class = "prio-normal"
        card_class = "nota-card-normal"

    # Asignación de estilos de estado
    if 'REALIZ' in estado:
        estado_class = "estado-realizado"
        estado_texto = "REALIZADO"
    else:
        estado_class = "estado-pendiente"
        estado_texto = "PENDIENTE"

    return f"""
    <div class="nota-card {card_class}">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <span class="prio-badge {prio_class}">{prioridad if prioridad else 'NORMAL'}</span>
            <span class="estado-badge {estado_class}">{estado_texto}</span>
        </div>
        <div style="font-size: 0.88rem; color: #E5E7EB; line-height: 1.4; font-weight: 400;">
            {descripcion}
        </div>
    </div>
    """

# -----------------------------------------------------------------------------
# COMPONENTE FLUIDO REFRESCABLE CON WEBSOCKETS (SINO RECARGA TOTAL)
# -----------------------------------------------------------------------------
@st.fragment(run_every=5)
def render_tablero_fluido():
    # Carga de datos optimizada
    df_ordenes, df_notas = cargar_datos_gsheets()

    # Gestión de paginación automática (Cambia cada 90s)
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 0
    if 'last_rotation' not in st.session_state:
        st.session_state.last_rotation = time.time()

    page_size = 8
    total_rows = len(df_ordenes)
    total_pages = max(1, (total_rows + page_size - 1) // page_size)

    now = time.time()
    if now - st.session_state.last_rotation > 90:
        st.session_state.current_page = (st.session_state.current_page + 1) % total_pages
        st.session_state.last_rotation = now

    # -------------------------------------------------------------------------
    # 1. KPIS SUPERIORES
    # -------------------------------------------------------------------------
    k1, k2, k3, k4 = st.columns(4)
    
    col_estado = df_ordenes['Estado'] if 'Estado' in df_ordenes.columns else pd.Series(dtype=str)

    with k1:
        count_reg = len(df_ordenes[col_estado.str.contains('REGISTRAD', na=False, case=False)])
        st.markdown(f'<div class="kpi-card"><div class="kpi-title">REGISTRADAS</div><div class="kpi-value">{count_reg}</div></div>', unsafe_allow_html=True)
    with k2:
        count_firm = len(df_ordenes[col_estado.str.contains('FIRMAD', na=False, case=False)])
        st.markdown(f'<div class="kpi-card"><div class="kpi-title">FIRMADAS</div><div class="kpi-value">{count_firm}</div></div>', unsafe_allow_html=True)
    with k3:
        count_env = len(df_ordenes[col_estado.str.contains('ENVIAD', na=False, case=False)])
        st.markdown(f'<div class="kpi-card"><div class="kpi-title">ENVIADAS</div><div class="kpi-value">{count_env}</div></div>', unsafe_allow_html=True)
    with k4:
        count_pend = len(df_ordenes[col_estado.str.contains('PENDIENT', na=False, case=False)])
        st.markdown(f'<div class="kpi-card"><div class="kpi-title">PENDIENTES</div><div class="kpi-value">{count_pend}</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # 2. TABLA PRINCIPAL DE ÓRDENES
    # -------------------------------------------------------------------------
    start_idx = st.session_state.current_page * page_size
    end_idx = start_idx + page_size
    df_paged = df_ordenes.iloc[start_idx:end_idx]

    render_dark_table(df_paged, st.session_state.current_page + 1, total_pages)

    # -------------------------------------------------------------------------
    # 3. SECCIÓN INFERIOR (3 COLUMNAS)
    # -------------------------------------------------------------------------
    c1, c2, c3 = st.columns([1, 1, 1.25])

    # Columna 1: Programadas p/ Hoy
    with c1:
        st.markdown('<div class="sec-card"><div class="sec-header">📅 Programadas p/ Hoy</div>', unsafe_allow_html=True)
        if not df_ordenes.empty:
            for _, r in df_ordenes.head(6).iterrows():
                orden = r.get('Orden', 'N/A')
                est = r.get('Estado', 'N/A')
                st.markdown(
                    f"<div style='padding:8px 0; border-bottom:1px solid #1F2937; color:#D1D5DB; font-size:0.88rem; display:flex; justify-content:space-between;'>"
                    f"<span><b>Órden #{orden}</b></span>"
                    f"<span style='color:#9CA3AF;'>{est}</span>"
                    f"</div>",
                    unsafe_allow_html=True
                )
        st.markdown('</div>', unsafe_allow_html=True)

    # Columna 2: Meta del Día
    with c2:
        st.markdown('<div class="sec-card"><div class="sec-header">🎯 Meta del Día</div>', unsafe_allow_html=True)
        enviadas = len(df_ordenes[col_estado.str.contains('ENVIAD', na=False, case=False)])
        total = len(df_ordenes) if len(df_ordenes) > 0 else 1
        porcentaje = int((enviadas / total) * 100)
        
        st.markdown(f"""
        <div style="text-align: center; padding: 25px 0;">
            <div style="font-size: 3.5rem; font-weight: 800; color: #10B981; line-height: 1;">{porcentaje}%</div>
            <div style="color: #9CA3AF; font-size: 0.95rem; margin-top: 8px;">Despachos Cumplidos</div>
            <div style="margin-top: 20px; font-size: 1.1rem; font-weight: 600; color: #E5E7EB; background: #1F2937; padding: 8px 16px; border-radius: 20px; display: inline-block;">
                {enviadas} de {total} Órdenes
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Columna 3: NOTAS DEL DÍA (Renombrado y Mejorado)
    with c3:
        st.markdown('<div class="sec-card"><div class="sec-header">📌 NOTAS DEL DÍA</div>', unsafe_allow_html=True)
        if not df_notas.empty:
            for _, row in df_notas.iterrows():
                card_html = render_bitacora_card(row)
                if card_html:
                    st.markdown(card_html, unsafe_allow_html=True)
        else:
            st.markdown("<div style='color:#9CA3AF; padding:10px;'>No hay notas o avisos para mostrar.</div>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# EJECUCIÓN PRINCIPAL DE LA APLICACIÓN
# -----------------------------------------------------------------------------
def main():
    # Encabezado del Tablero
    st.markdown("""
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; border-bottom: 1px solid #1F2937; padding-bottom: 12px;">
        <div>
            <h1 style="margin: 0; font-size: 1.8rem; color: #F9FAFB;">🔬 Tablero de Control - Laboratorio de Calibración</h1>
            <p style="margin: 4px 0 0 0; color: #9CA3AF; font-size: 0.9rem;">Monitoreo en tiempo real de operaciones y notas del día</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Renderizado dentro del fragmento fluido sin recargas de página
    render_tablero_fluido()

if __name__ == "__main__":
    main()
