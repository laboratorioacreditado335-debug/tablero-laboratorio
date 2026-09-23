import time
import datetime
import pandas as pd
import streamlit as st
from streamlit_gsheets import GSheetsConnection

# -----------------------------------------------------------------------------
# 1. CONFIGURACIÓN DE LA PÁGINA Y ESTILOS CSS BASE
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Tablero de Control - Laboratorio de Calibración",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

def inject_custom_css():
    st.markdown("""
    <style>
        /* Fondo global en modo oscuro personalizado */
        .stApp {
            background-color: #0B1120;
            color: #F3F4F6;
            font-family: 'Inter', system-ui, -apple-system, sans-serif;
        }

        /* Ocultar elementos nativos innecesarios */
        #MainMenu, header, footer {visibility: hidden;}

        /* Estilos de Tarjetas KPI */
        .kpi-card {
            background-color: #111827;
            border: 1px solid #1F2937;
            border-radius: 10px;
            padding: 16px;
            text-align: center;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
        }
        .kpi-title {
            color: #9CA3AF;
            font-size: 0.85rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 4px;
        }
        .kpi-value {
            font-size: 2rem;
            font-weight: 700;
            color: #F9FAFB;
        }

        /* Tabla oscura */
        .dark-table-container {
            background-color: #111827;
            border: 1px solid #1F2937;
            border-radius: 10px;
            padding: 12px;
            margin-bottom: 20px;
        }
        .dark-table {
            width: 100%;
            border-collapse: collapse;
            color: #E5E7EB;
            font-size: 0.9rem;
        }
        .dark-table th {
            background-color: #1F2937;
            color: #9CA3AF;
            text-align: left;
            padding: 10px 12px;
            font-weight: 600;
            border-bottom: 2px solid #374151;
        }
        .dark-table td {
            padding: 10px 12px;
            border-bottom: 1px solid #1F2937;
        }
        .dark-table tr:hover {
            background-color: #1E293B;
        }

        /* Animación de Parpadeo para Alertas */
        @keyframes blink {
            0% { opacity: 1.0; }
            50% { opacity: 0.3; }
            100% { opacity: 1.0; }
        }
        .badge-blink {
            animation: blink 1.5s infinite;
        }

        /* Badges de Tabla Principal */
        .badge {
            padding: 4px 8px;
            border-radius: 6px;
            font-size: 0.75rem;
            font-weight: 600;
            display: inline-block;
        }
        .badge-atascada { background-color: #7F1D1D; color: #FECACA; border: 1px solid #EF4444; }
        .badge-aprobacion { background-color: #78350F; color: #FDE68A; border: 1px solid #F59E0B; }
        .badge-correccion { background-color: #1E3A8A; color: #BFDBFE; border: 1px solid #3B82F6; }

        /* Estilos de Sección Inferior / Tarjetas de Bitácora */
        .section-card {
            background-color: #111827;
            border: 1px solid #1F2937;
            border-radius: 10px;
            padding: 16px;
            height: 100%;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
        }
        .section-header {
            font-size: 1.1rem;
            font-weight: 700;
            color: #F3F4F6;
            margin-bottom: 12px;
            border-bottom: 1px solid #374151;
            padding-bottom: 8px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        /* Badges Dinámicos para la Bitácora segun colores de Excel */
        .bitacora-item {
            border-radius: 8px;
            padding: 12px;
            margin-bottom: 10px;
            border-left: 5px solid #3B82F6;
            background-color: #1E293B;
            transition: transform 0.1s ease;
        }
        .bitacora-item:hover {
            transform: translateX(2px);
        }
        .bitacora-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 6px;
        }
        .bitacora-desc {
            color: #E5E7EB;
            font-size: 0.88rem;
            line-height: 1.35;
        }
        
        /* Prioridades basadas en Excel */
        .prio-urgente { background-color: #451A1A; border-left-color: #EF4444; }
        .prio-normal { background-color: #1E293B; border-left-color: #3B82F6; }
        .prio-revision { background-color: #452700; border-left-color: #F97316; }
        .prio-auditoria { background-color: #3B0764; border-left-color: #A855F7; }

        .tag-prio {
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.7rem;
            font-weight: 700;
            letter-spacing: 0.03em;
        }
        .tag-urgente { background-color: #7F1D1D; color: #FCA5A5; border: 1px solid #EF4444; }
        .tag-normal { background-color: #1E3A8A; color: #BFDBFE; border: 1px solid #3B82F6; }
        .tag-revision { background-color: #7C2D12; color: #FFEDD5; border: 1px solid #F97316; }
        .tag-auditoria { background-color: #581C87; color: #F3E8FF; border: 1px solid #A855F7; }

        .tag-estado {
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.7rem;
            font-weight: 700;
        }
        .estado-pendiente { background-color: #7F1D1D; color: #FECACA; }
        .estado-realizado { background-color: #14532D; color: #86EFAC; }
    </style>
    """, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. LECTURA Y PROCESAMIENTO DE DATOS (GOOGLE SHEETS)
# -----------------------------------------------------------------------------
@st.cache_data(ttl=5)
def cargar_datos_gsheets():
    """
    Carga las dos pestañas necesarias de Google Sheets con tratamiento de errores
    y limpieza de formatos (foward-fill de fechas, parseo de seriales Excel, limpia .0).
    """
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        
        # 1. Cargar Órdenes
        df_ordenes = conn.read(worksheet="C. Proceso órdenes", ttl="5s")
        if df_ordenes is not None and not df_ordenes.empty:
            # Limpieza de seriales / columnas vacías
            df_ordenes = df_ordenes.dropna(how="all")
            
            # Resolver celdas combinadas en Fecha
            if 'Fecha' in df_ordenes.columns:
                df_ordenes['Fecha'] = df_ordenes['Fecha'].ffill()
            
            # Limpiar número de orden (eliminar sufijo .0 si existe)
            if 'Orden' in df_ordenes.columns:
                df_ordenes['Orden'] = df_ordenes['Orden'].astype(str).apply(
                    lambda x: x.split('.')[0] if str(x).endswith('.0') else str(x)
                )
        else:
            df_ordenes = pd.DataFrame()

        # 2. Cargar Bitácora / Notas del Día
        df_notas = conn.read(worksheet="NOTAS DEL DIA", ttl="5s")
        if df_notas is not None and not df_notas.empty:
            df_notas = df_notas.dropna(how="all")
            # Renombrar columnas si vienen con espacios
            df_notas.columns = [str(col).strip() for col in df_notas.columns]
        else:
            df_notas = pd.DataFrame()

        return df_ordenes, df_notas

    except Exception as e:
        # Fallback de seguridad en caso de error de conexión
        return pd.DataFrame(), pd.DataFrame()

# -----------------------------------------------------------------------------
# 3. COMPONENTES DE INTERFAZ Y RENDERIZADO
# -----------------------------------------------------------------------------

def render_kpis(df):
    """Muestra los 4 KPIs superiores con conteos actualizados."""
    registradas = len(df) if not df.empty else 0
    firmadas = len(df[df['Estado'] == 'FIRMADA']) if not df.empty and 'Estado' in df.columns else 0
    enviadas = len(df[df['Estado'] == 'ENVIADA']) if not df.empty and 'Estado' in df.columns else 0
    pendientes = len(df[df['Estado'] == 'PENDIENTE']) if not df.empty and 'Estado' in df.columns else 0

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f'''
            <div class="kpi-card">
                <div class="kpi-title">📋 Registradas</div>
                <div class="kpi-value" style="color: #60A5FA;">{registradas}</div>
            </div>
        ''', unsafe_allow_html=True)
    with col2:
        st.markdown(f'''
            <div class="kpi-card">
                <div class="kpi-title">✍️ Firmadas</div>
                <div class="kpi-value" style="color: #34D399;">{firmadas}</div>
            </div>
        ''', unsafe_allow_html=True)
    with col3:
        st.markdown(f'''
            <div class="kpi-card">
                <div class="kpi-title">🚀 Enviadas</div>
                <div class="kpi-value" style="color: #A78BFA;">{enviadas}</div>
            </div>
        ''', unsafe_allow_html=True)
    with col4:
        st.markdown(f'''
            <div class="kpi-card">
                <div class="kpi-title">⏳ Pendientes</div>
                <div class="kpi-value" style="color: #FBBF24;">{pendientes}</div>
            </div>
        ''', unsafe_allow_html=True)

def render_dark_table(df, pagina_actual=1, filas_por_pagina=8):
    """Renderiza la tabla principal paginada con Badges condicionales y animaciones."""
    if df.empty:
        st.info("No hay datos de órdenes disponibles actualmente.")
        return 1

    total_filas = len(df)
    total_paginas = max(1, (total_filas + filas_por_pagina - 1) // filas_por_pagina)
    pagina_actual = min(pagina_actual, total_paginas)

    inicio = (pagina_actual - 1) * filas_por_pagina
    fin = inicio + filas_por_pagina
    df_pagina = df.iloc[inicio:fin]

    html_code = '<div class="dark-table-container"><table class="dark-table">'
    html_code += '''
        <thead>
            <tr>
                <th>ORDEN</th>
                <th>CLIENTE</th>
                <th>EQUIPO</th>
                <th>FECHA</th>
                <th>ESTADO</th>
                <th>ALERTA / NOTA</th>
            </tr>
        </thead>
        <tbody>
    '''

    for _, row in df_pagina.iterrows():
        orden = str(row.get('Orden', 'N/A'))
        cliente = str(row.get('Cliente', 'N/A'))
        equipo = str(row.get('Equipo', 'N/A'))
        fecha = str(row.get('Fecha', 'N/A'))
        estado = str(row.get('Estado', 'N/A'))
        alerta = str(row.get('Alerta', '')).strip()

        # Determinar badge condicional
        badge_html = ""
        alerta_upper = alerta.upper()
        if "ATASCADA" in alerta_upper:
            badge_html = '<span class="badge badge-atascada badge-blink">⚠️ ATASCADA</span>'
        elif "APROBAC" in alerta_upper:
            badge_html = '<span class="badge badge-aprobacion">⏳ APROBACIÓN</span>'
        elif "CORRECC" in alerta_upper:
            badge_html = '<span class="badge badge-correccion">✏️ CORRECCIÓN</span>'
        else:
            badge_html = f'<span>{alerta}</span>'

        html_code += f'''
            <tr>
                <td><strong>{orden}</strong></td>
                <td>{cliente}</td>
                <td>{equipo}</td>
                <td>{fecha}</td>
                <td>{estado}</td>
                <td>{badge_html}</td>
            </tr>
        '''

    html_code += f'''
        </tbody>
        </table>
        <div style="text-align: right; font-size: 0.8rem; color: #9CA3AF; margin-top: 8px;">
            Página {pagina_actual} de {total_paginas} ({total_filas} registros)
        </div>
    </div>
    '''
    st.markdown(html_code, unsafe_allow_html=True)
    return total_paginas

def render_programadas_hoy(df):
    """Muestra la lista de órdenes agendadas para el día de hoy."""
    html = '<div class="section-card"><div class="section-header">📅 Programadas p/ Hoy</div>'
    
    if not df.empty and 'Programada' in df.columns:
        df_hoy = df[df['Programada'] == True] if df['Programada'].dtype == bool else df[df['Programada'].astype(str).str.upper() == 'SI']
        if not df_hoy.empty:
            html += '<ul style="list-style-type: none; padding-left: 0; margin: 0;">'
            for _, row in df_hoy.head(5).iterrows():
                orden = row.get('Orden', 'N/A')
                cliente = row.get('Cliente', 'Cliente N/A')
                html += f'<li style="padding: 6px 0; border-bottom: 1px solid #1F2937;">📌 <strong>{orden}</strong> - {cliente}</li>'
            html += '</ul>'
        else:
            html += '<p style="color: #9CA3AF; font-size: 0.85rem;">No hay órdenes programadas para hoy.</p>'
    else:
        html += '<p style="color: #9CA3AF; font-size: 0.85rem;">Sin información de programación.</p>'
    
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

def render_meta_dia(df):
    """Muestra la meta del día con contador y porcentaje de cumplimiento."""
    meta = 10
    cumplidos = len(df[df['Estado'] == 'ENVIADA']) if not df.empty and 'Estado' in df.columns else 0
    porcentaje = min(100, int((cumplidos / meta) * 100)) if meta > 0 else 0

    html = f'''
    <div class="section-card">
        <div class="section-header">🎯 Meta del Día</div>
        <div style="text-align: center; margin: 15px 0;">
            <div style="font-size: 2.2rem; font-weight: 800; color: #34D399;">{cumplidos} / {meta}</div>
            <div style="color: #9CA3AF; font-size: 0.85rem;">Despachos Realizados</div>
        </div>
        <div style="background-color: #1F2937; border-radius: 10px; height: 12px; width: 100%; overflow: hidden;">
            <div style="background-color: #10B981; width: {porcentaje}%; height: 100%;"></div>
        </div>
        <div style="text-align: right; font-size: 0.8rem; color: #9CA3AF; margin-top: 4px;">{porcentaje}% completado</div>
    </div>
    '''
    st.markdown(html, unsafe_allow_html=True)

def render_bitacora_card(df_notas):
    """
    Renderiza la sección 'Bitácora y Avisos del Día' detectando automáticamente
    las prioridades (URGENTE, NORMAL, REVISIÓN, AUDITORÍA) y estados (PENDIENTE, REALIZADO)
    para asignar el color exacto definido en el Excel original.
    """
    html = '''
    <div class="section-card">
        <div class="section-header">
            <span>📝 Bitácora y Avisos del Día</span>
            <span style="font-size: 0.75rem; color: #9CA3AF; font-weight: normal;">Gestión Diaria</span>
        </div>
    '''

    if not df_notas.empty:
        col_prio = [c for c in df_notas.columns if 'PRIORIDAD' in c.upper() or 'PO' in c.upper()]
        col_desc = [c for c in df_notas.columns if 'DESCRIPCION' in c.upper() or 'DESCRIPCIÓN' in c.upper() or 'NOTA' in c.upper()]
        col_est = [c for c in df_notas.columns if 'ESTADO' in c.upper()]

        c_prio = col_prio[0] if col_prio else df_notas.columns[0]
        c_desc = col_desc[0] if col_desc else (df_notas.columns[1] if len(df_notas.columns) > 1 else df_notas.columns[0])
        c_est = col_est[0] if col_est else (df_notas.columns[2] if len(df_notas.columns) > 2 else df_notas.columns[0])

        for _, row in df_notas.iterrows():
            prioridad_raw = str(row.get(c_prio, '')).strip()
            descripcion = str(row.get(c_desc, '')).strip()
            estado_raw = str(row.get(c_est, '')).strip()

            if not descripcion or pd.isna(descripcion) or descripcion.lower() == 'nan':
                continue

            # Mapeo de estilos según la prioridad
            p_upper = prioridad_raw.upper()
            if "URGENTE" in p_upper:
                item_class = "prio-urgente"
                tag_prio_class = "tag-urgente"
            elif "NORMAL" in p_upper:
                item_class = "prio-normal"
                tag_prio_class = "tag-normal"
            elif "REVISI" in p_upper or "REVISÓN" in p_upper:
                item_class = "prio-revision"
                tag_prio_class = "tag-revision"
            elif "AUDITOR" in p_upper:
                item_class = "prio-auditoria"
                tag_prio_class = "tag-auditoria"
            else:
                item_class = "prio-normal"
                tag_prio_class = "tag-normal"

            # Mapeo de estado
            e_upper = estado_raw.upper()
            if "PENDIENTE" in e_upper:
                tag_estado_class = "estado-pendiente"
            elif "REALIZADO" in e_upper or "COMPLETADO" in e_upper:
                tag_estado_class = "estado-realizado"
            else:
                tag_estado_class = "estado-pendiente"

            html += f'''
            <div class="bitacora-item {item_class}">
                <div class="bitacora-header">
                    <span class="tag-prio {tag_prio_class}">{prioridad_raw if prioridad_raw else "NOTA"}</span>
                    <span class="tag-estado {tag_estado_class}">{estado_raw if estado_raw else "PENDIENTE"}</span>
                </div>
                <div class="bitacora-desc">{descripcion}</div>
            </div>
            '''
    else:
        html += '<p style="color: #9CA3AF; font-size: 0.85rem;">No hay notas ni avisos registrados para hoy.</p>'

    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 4. FRAGMENTO DE ACTUALIZACIÓN EN TIEMPO REAL (SIN RECARGA COMPLETA DE PÁGINA)
# -----------------------------------------------------------------------------
@st.fragment(run_every=5)
def render_tablero_fluido():
    """Fragmento que se ejecuta cada 5 segundos vía WebSockets sin parpadeo de pantalla."""
    
    # Inicialización de estado de sesión para paginación automática
    if 'pagina_actual' not in st.session_state:
        st.session_state['pagina_actual'] = 1
    if 'ultimo_cambio_pagina' not in st.session_state:
        st.session_state['ultimo_cambio_pagina'] = time.time()

    # Cargar datos desde Google Sheets
    df_ordenes, df_notas = cargar_datos_gsheets()

    # Inyectar estilos CSS
    inject_custom_css()

    # Encabezado con hora actual
    hora_actual = datetime.datetime.now().strftime("%H:%M:%S")
    st.markdown(f'''
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
            <div>
                <h1 style="margin: 0; font-size: 1.8rem; font-weight: 800; color: #F9FAFB;">🔬 Tablero de Control - Laboratorio</h1>
                <p style="margin: 0; color: #9CA3AF; font-size: 0.9rem;">Monitoreo en Tiempo Real de Calibraciones y Despachos</p>
            </div>
            <div style="background-color: #111827; border: 1px solid #1F2937; padding: 6px 14px; border-radius: 8px; font-weight: 600; color: #60A5FA;">
                🟢 EN VIVO &nbsp;|&nbsp; {hora_actual}
            </div>
        </div>
    ''', unsafe_allow_html=True)

    # 1. KPIs Superiores
    render_kpis(df_ordenes)
    st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True)

    # Rotación automática de páginas cada 90 segundos
    tiempo_transcurrido = time.time() - st.session_state['ultimo_cambio_pagina']
    if tiempo_transcurrido >= 90:
        st.session_state['pagina_actual'] += 1
        st.session_state['ultimo_cambio_pagina'] = time.time()

    # 2. Tabla Principal Paginada
    total_paginas = render_dark_table(df_ordenes, pagina_actual=st.session_state['pagina_actual'], filas_por_pagina=8)
    
    # Reset de página si sobrepasa el total
    if st.session_state['pagina_actual'] > total_paginas:
        st.session_state['pagina_actual'] = 1

    # 3. Sección Inferior (3 Columnas de Layout)
    col1, col2, col3 = st.columns(3)
    
    with col1:
        render_programadas_hoy(df_ordenes)

    with col2:
        render_meta_dia(df_ordenes)

    with col3:
        render_bitacora_card(df_notas)

# -----------------------------------------------------------------------------
# 5. PUNTO DE ENTRADA PRINCIPAL
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    render_tablero_fluido()
