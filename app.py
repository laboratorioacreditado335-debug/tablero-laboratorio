import urllib.parse
from datetime import datetime
import time
import pandas as pd
import streamlit as st

# ==========================================
# 1. CONFIGURACIÓN DE PÁGINA
# ==========================================
st.set_page_config(
    page_title="Tablero de Control - Laboratorio",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ==========================================
# HELPER PARA COMPRIMIR Y LIMPIAR HTML
# ==========================================
def clean_html(html_str: str) -> str:
    """
    Elimina los espacios/sangrías iniciales de cada línea en cadenas HTML.
    Esto evita que Streamlit interprete el HTML como bloque de código Markdown (<pre><code>).
    """
    return "".join(line.strip() for line in html_str.splitlines())


# ==========================================
# 2. ESTILOS CSS PERSONALIZADOS (MODO OSCURO)
# ==========================================
CSS_STYLES = clean_html("""
<style>
    /* Ocultar elementos nativos de Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Fondo General */
    .stApp {
        background-color: #0B1120;
        color: #F3F4F6;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Contenedor Principal */
    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 1rem;
        padding-left: 1.5rem;
        padding-right: 1.5rem;
        max-width: 100%;
    }

    /* Tarjetas de KPI */
    .kpi-card {
        background-color: #111827;
        border: 1px solid #1F2937;
        border-radius: 10px;
        padding: 12px 16px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
        text-align: center;
        transition: transform 0.2s;
    }
    .kpi-card:hover {
        transform: translateY(-2px);
    }
    .kpi-title {
        font-size: 11px;
        font-weight: 700;
        color: #9CA3AF;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        margin-bottom: 4px;
    }
    .kpi-value {
        font-size: 26px;
        font-weight: 800;
        line-height: 1.1;
    }

    /* Badges de Estado */
    .badge {
        display: inline-block;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 11px;
        font-weight: 700;
        text-align: center;
    }
    .badge-atascada {
        background-color: #7F1D1D;
        color: #FCA5A5;
        border: 1px solid #991B1B;
        animation: pulse-red 2s infinite;
    }
    .badge-aprobacion {
        background-color: #78350F;
        color: #FDE68A;
        border: 1px solid #92400E;
    }
    .badge-correccion {
        background-color: #831843;
        color: #FBCFE8;
        border: 1px solid #9D174D;
        animation: pulse-pink 2s infinite;
    }
    .badge-ok {
        background-color: #065F46;
        color: #A7F3D0;
        border: 1px solid #047857;
    }
    .badge-proceso {
        background-color: #1E3A8A;
        color: #BFDBFE;
        border: 1px solid #1E40AF;
    }

    /* Animaciones de Alerta */
    @keyframes pulse-red {
        0% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.5); }
        70% { box-shadow: 0 0 0 6px rgba(239, 68, 68, 0); }
        100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
    }
    @keyframes pulse-pink {
        0% { box-shadow: 0 0 0 0 rgba(236, 72, 153, 0.5); }
        70% { box-shadow: 0 0 0 6px rgba(236, 72, 153, 0); }
        100% { box-shadow: 0 0 0 0 rgba(236, 72, 153, 0); }
    }

    /* Bitácora Cards */
    .bitacora-card {
        background-color: #111827;
        border-left: 4px solid #3B82F6;
        border-top: 1px solid #1F2937;
        border-right: 1px solid #1F2937;
        border-bottom: 1px solid #1F2937;
        border-radius: 6px;
        padding: 10px;
        margin-bottom: 8px;
        font-size: 12px;
    }
    .bitacora-card.alta { border-left-color: #EF4444; }
    .bitacora-card.media { border-left-color: #F59E0B; }
    .bitacora-card.baja { border-left-color: #10B981; }

    /* Personalización de Inputs de Streamlit */
    div[data-baseweb="input"] {
        background-color: #111827 !important;
        border-color: #374151 !important;
        color: #F3F4F6 !important;
        border-radius: 6px !important;
    }
    div[data-baseweb="select"] > div {
        background-color: #111827 !important;
        border-color: #374151 !important;
        color: #F3F4F6 !important;
    }
</style>
""")

st.markdown(CSS_STYLES, unsafe_allow_html=True)


# ==========================================
# 3. LECTURA Y PROCESAMIENTO DE GOOGLE SHEETS
# ==========================================
def obtener_spreadsheet_id():
    """Busca defensivamente el SPREADSHEET_ID en st.secrets o estructuras anidadas."""
    try:
        if "SPREADSHEET_ID" in st.secrets:
            return st.secrets["SPREADSHEET_ID"]
        for key in st.secrets:
            if isinstance(st.secrets[key], dict) and "SPREADSHEET_ID" in st.secrets[key]:
                return st.secrets[key]["SPREADSHEET_ID"]
    except Exception:
        pass
    return None


def cargar_datos_gsheets():
    try:
        spreadsheet_id = obtener_spreadsheet_id()

        if not spreadsheet_id:
            st.error(
                "⚠️ La clave SPREADSHEET_ID no está configurada en st.secrets de Streamlit Cloud. "
                "Por favor añádela en la pestaña Settings > Secrets de tu app."
            )
            return pd.DataFrame(), pd.DataFrame(), "# Orden"

        url_proceso = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/gviz/tq?tqx=out:csv&sheet={urllib.parse.quote('C. Proceso órdenes')}"

        # Cargar hoja principal
        df_proceso = pd.read_csv(url_proceso)
        if df_proceso.empty:
            return pd.DataFrame(), pd.DataFrame(), "# Orden"

        df_proceso.columns = df_proceso.columns.str.strip()

        # Limpieza de celdas combinadas de fecha
        if "Fecha" in df_proceso.columns:
            df_proceso["Fecha"] = df_proceso["Fecha"].ffill()

        # Mapeo y limpieza de la columna de orden
        if "# Orden" in df_proceso.columns:
            col_ord = "# Orden"
        elif len(df_proceso.columns) > 1:
            col_ord = df_proceso.columns[1]
        else:
            col_ord = df_proceso.columns[0]

        def limpiar_orden(val):
            if pd.isna(val) or val == "":
                return ""
            val_str = str(val).strip()
            if val_str.endswith(".0"):
                val_str = val_str[:-2]
            return val_str

        df_proceso[col_ord] = df_proceso[col_ord].apply(limpiar_orden)

        # Parseo defensivo de fechas
        def parse_fecha(val):
            if pd.isna(val) or val == "" or str(val).strip().lower() in ["nan", "none", "null"]:
                return None
            val_str = str(val).strip()

            # Intentar número serial de Excel
            try:
                num_val = float(val_str)
                if num_val > 30000:
                    return pd.to_datetime("1899-12-30") + pd.to_timedelta(num_val, unit="D")
            except (ValueError, TypeError):
                pass

            # Intentar formatos habituales de texto
            for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y"):
                try:
                    return pd.to_datetime(val_str, format=fmt)
                except (ValueError, TypeError):
                    continue
            return pd.to_datetime(val_str, errors="coerce")

        if "Fecha" in df_proceso.columns:
            df_proceso["Fecha_dt"] = df_proceso["Fecha"].apply(parse_fecha)
        else:
            df_proceso["Fecha_dt"] = pd.NaT

        # Cargar hoja secundaria NOTAS DEL DIA
        url_notas = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/gviz/tq?tqx=out:csv&sheet={urllib.parse.quote('NOTAS DEL DIA')}"
        try:
            df_notas = pd.read_csv(url_notas)
            df_notas.columns = df_notas.columns.str.strip()
        except Exception:
            df_notas = pd.DataFrame()

        return df_proceso, df_notas, col_ord

    except Exception as e:
        st.error(f"Error al conectar con Google Sheets: {e}")
        return pd.DataFrame(), pd.DataFrame(), "# Orden"


# ==========================================
# 4. COMPONENTES REUTILIZABLES HTML
# ==========================================
def render_dark_table(df_display, col_ord_name):
    """Genera la tabla HTML interactiva respetando los estilos del tablero."""
    rows_html = ""
    for _, row in df_display.iterrows():
        def clean_val(v):
            if pd.isna(v) or str(v).strip().lower() in ["nan", "none", "null"]:
                return ""
            return str(v).strip()

        fecha = clean_val(row.get("Fecha", ""))
        orden = clean_val(row.get(col_ord_name, ""))
        cer_firm = clean_val(row.get("Cer firmado", ""))
        enviado = clean_val(row.get("Enviado", ""))
        crm_salida = clean_val(row.get("CRM salida", ""))
        aprob_com = clean_val(row.get("Aprob. Comercial", ""))
        crm_cert = clean_val(row.get("CRM cert.", ""))

        cer_upper = cer_firm.upper()
        env_upper = enviado.upper()

        if "CORRECCI" in cer_upper or "CORRECCI" in env_upper:
            badge = '<span class="badge badge-correccion">⚠️ Corrección</span>'
        elif cer_upper in ["SI", "SÍ"] and env_upper not in ["SI", "SÍ"]:
            badge = '<span class="badge badge-atascada">🚨 Atascada</span>'
        elif aprob_com.upper() in ["PENDIENTE", "REVISIÓN", "REVISION", "P. APROBACIÓN", "P. APROBACION"]:
            badge = '<span class="badge badge-aprobacion">⏳ Aprobación</span>'
        elif env_upper in ["SI", "SÍ"]:
            badge = '<span class="badge badge-ok">✅ Completada</span>'
        else:
            badge = '<span class="badge badge-proceso">⚙️ En Proceso</span>'

        rows_html += f"""
        <tr style="border-bottom: 1px solid #1F2937; transition: background-color 0.15s;" onmouseover="this.style.backgroundColor='#1E293B'" onmouseout="this.style.backgroundColor='transparent'">
            <td style="padding: 9px 14px; color: #9CA3AF;">{fecha}</td>
            <td style="padding: 9px 14px; font-weight: 700; color: #60A5FA;">{orden}</td>
            <td style="padding: 9px 14px;">{cer_firm}</td>
            <td style="padding: 9px 14px;">{enviado}</td>
            <td style="padding: 9px 14px; color: #9CA3AF;">{crm_salida}</td>
            <td style="padding: 9px 14px; color: #9CA3AF;">{aprob_com}</td>
            <td style="padding: 9px 14px; color: #9CA3AF;">{crm_cert}</td>
            <td style="padding: 9px 14px;">{badge}</td>
        </tr>
        """

    full_html = f"""
    <div style="overflow-x: auto; border: 1px solid #1F2937; border-radius: 8px; background-color: #111827; margin-bottom: 8px;">
        <table style="width: 100%; border-collapse: collapse; color: #F3F4F6; font-size: 13px; text-align: left;">
            <thead>
                <tr style="background-color: #1F2937; color: #9CA3AF; font-weight: 700; text-transform: uppercase; font-size: 11px; letter-spacing: 0.5px;">
                    <th style="padding: 10px 14px; border-bottom: 1px solid #374151;">Fecha</th>
                    <th style="padding: 10px 14px; border-bottom: 1px solid #374151;"># Orden</th>
                    <th style="padding: 10px 14px; border-bottom: 1px solid #374151;">Cert. Firmado</th>
                    <th style="padding: 10px 14px; border-bottom: 1px solid #374151;">Enviado</th>
                    <th style="padding: 10px 14px; border-bottom: 1px solid #374151;">CRM Salida</th>
                    <th style="padding: 10px 14px; border-bottom: 1px solid #374151;">Aprob. Comercial</th>
                    <th style="padding: 10px 14px; border-bottom: 1px solid #374151;">CRM Cert.</th>
                    <th style="padding: 10px 14px; border-bottom: 1px solid #374151;">Estado Alerta</th>
                </tr>
            </thead>
            <tbody>
                {rows_html}
            </tbody>
        </table>
    </div>
    """
    return clean_html(full_html)


def render_bitacora_card(prioridad, mensaje, hora=""):
    prioridad_cls = prioridad.lower()
    html_card = f"""
    <div class="bitacora-card {prioridad_cls}">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
            <span style="font-weight: 700; color: #F3F4F6;">📌 Prioridad: {prioridad.upper()}</span>
            <span style="font-size: 10px; color: #9CA3AF;">{hora}</span>
        </div>
        <div style="color: #D1D5DB;">{mensaje}</div>
    </div>
    """
    return clean_html(html_card)


# ==========================================
# 5. FRAGMENTO DE ACTUALIZACIÓN EN TIEMPO REAL
# ==========================================
@st.fragment(run_every=5)
def render_tablero_fluido():
    df_proceso, df_notas, col_ord_main = cargar_datos_gsheets()

    if df_proceso.empty:
        st.info("Conectando con Google Sheets y sincronizando datos...")
        return

    hoy_dt = pd.to_datetime(datetime.today().strftime("%Y-%m-%d"))

    # ------------------------------------------
    # CÁLCULOS KPI GENERALES
    # ------------------------------------------
    total_registradas = len(df_proceso)

    col_firm = "Cer firmado" if "Cer firmado" in df_proceso.columns else None
    if col_firm:
        total_firmadas = (
            df_proceso[col_firm]
            .astype(str)
            .str.upper()
            .str.contains("SI|SÍ")
            .sum()
        )
    else:
        total_firmadas = 0

    col_env = "Enviado" if "Enviado" in df_proceso.columns else None
    if col_env:
        total_enviadas = (
            df_proceso[col_env]
            .astype(str)
            .str.upper()
            .str.contains("SI|SÍ")
            .sum()
        )
    else:
        total_enviadas = 0

    if col_firm and col_env:
        total_pendientes = (
            (df_proceso[col_firm].astype(str).str.upper().str.contains("SI|SÍ"))
            & (~df_proceso[col_env].astype(str).str.upper().str.contains("SI|SÍ"))
        ).sum()
    else:
        total_pendientes = 0

    # ------------------------------------------
    # HEADER Y SECCIÓN KPIs SUPERIORES
    # ------------------------------------------
    col_h1, col_h2 = st.columns([3, 1])
    with col_h1:
        st.markdown(
            clean_html("""
            <h2 style='margin:0; font-weight:800; color:#F3F4F6;'>🔬 TABLERO DE CONTROL DE CALIBRACIÓN</h2>
            <p style='margin:0; font-size:12px; color:#9CA3AF;'>Monitoreo de flujo de trabajo | Actualización fluida activa</p>
            """),
            unsafe_allow_html=True,
        )
    with col_h2:
        st.markdown(
            clean_html(f"""
            <div style='text-align: right; font-size: 11px; color: #6B7280; margin-top: 5px;'>
                Última sincro: <b>{datetime.now().strftime('%H:%M:%S')}</b>
            </div>
            """),
            unsafe_allow_html=True,
        )

    st.markdown("<div style='margin-bottom: 12px;'></div>", unsafe_allow_html=True)

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        st.markdown(
            clean_html(f'<div class="kpi-card"><div class="kpi-title">REGISTRADAS</div><div class="kpi-value" style="color:#60A5FA;">{total_registradas}</div></div>'),
            unsafe_allow_html=True,
        )
    with kpi2:
        st.markdown(
            clean_html(f'<div class="kpi-card"><div class="kpi-title">FIRMADA Y REVISADA</div><div class="kpi-value" style="color:#F59E0B;">{total_firmadas}</div></div>'),
            unsafe_allow_html=True,
        )
    with kpi3:
        st.markdown(
            clean_html(f'<div class="kpi-card"><div class="kpi-title">ENVIADAS</div><div class="kpi-value" style="color:#10B981;">{total_enviadas}</div></div>'),
            unsafe_allow_html=True,
        )
    with kpi4:
        st.markdown(
            clean_html(f'<div class="kpi-card"><div class="kpi-title">PENDIENTES / ATASCADAS</div><div class="kpi-value" style="color:#EF4444;">{total_pendientes}</div></div>'),
            unsafe_allow_html=True,
        )

    st.markdown("<div style='margin-bottom: 16px;'></div>", unsafe_allow_html=True)

    # ------------------------------------------
    # FILTRO Y BUSCADOR DE ORDEN
    # ------------------------------------------
    df_vista = df_proceso.copy()

    f_col1, b_col1, b_col2, b_col3 = st.columns([2.5, 0.9, 0.9, 2.2])

    with f_col1:
        query_orden = st.text_input(
            "Buscar Orden",
            placeholder="🔍 Buscar por N° de Orden...",
            key="input_search_orden",
            label_visibility="collapsed",
        )

    if query_orden and query_orden.strip():
        str_query = query_orden.strip().lower()
        df_vista = df_vista[
            df_vista[col_ord_main]
            .astype(str)
            .str.lower()
            .str.contains(str_query, na=False)
        ]

    # ------------------------------------------
    # PAGINACIÓN Y ESTADO DE SESIÓN
    # ------------------------------------------
    filas_por_pagina = 8
    total_filas = len(df_vista)
    total_paginas = max(1, (total_filas + filas_por_pagina - 1) // filas_por_pagina)

    if "pagina_actual" not in st.session_state:
        st.session_state.pagina_actual = 1
    if "last_page_rotation" not in st.session_state:
        st.session_state.last_page_rotation = time.time()

    # Auto-rotación cada 90 segundos
    if time.time() - st.session_state.last_page_rotation > 90:
        st.session_state.pagina_actual = (
            st.session_state.pagina_actual % total_paginas
        ) + 1
        st.session_state.last_page_rotation = time.time()

    if st.session_state.pagina_actual > total_paginas:
        st.session_state.pagina_actual = 1

    with b_col1:
        if st.button("◀ Ant.", use_container_width=True):
            st.session_state.pagina_actual = max(
                1, st.session_state.pagina_actual - 1
            )
            st.session_state.last_page_rotation = time.time()
    with b_col2:
        if st.button("Sig. ▶", use_container_width=True):
            st.session_state.pagina_actual = min(
                total_paginas, st.session_state.pagina_actual + 1
            )
            st.session_state.last_page_rotation = time.time()
    with b_col3:
        st.markdown(
            clean_html(f"""
            <div style='text-align: right; padding-top: 6px; font-size: 12px; color: #9CA3AF;'>
                Página <b>{st.session_state.pagina_actual}</b> de <b>{total_paginas}</b> ({total_filas} registros)
            </div>
            """),
            unsafe_allow_html=True,
        )

    # Rebanado del DataFrame para paginación
    start_idx = (st.session_state.pagina_actual - 1) * filas_por_pagina
    end_idx = start_idx + filas_por_pagina
    df_pagina = df_vista.iloc[start_idx:end_idx].copy()

    # Formateo visual de fechas
    df_pagina["Fecha"] = df_pagina["Fecha_dt"].apply(
        lambda d: d.strftime("%d/%m/%Y") if pd.notna(d) and d is not None else ""
    )

    # Renderizado de la tabla HTML (Limpiada con clean_html)
    st.markdown(
        render_dark_table(df_pagina, col_ord_main), unsafe_allow_html=True
    )

    st.markdown("<div style='margin-bottom: 12px;'></div>", unsafe_allow_html=True)

    # ------------------------------------------
    # SECCIÓN INFERIOR (3 COLUMNAS)
    # ------------------------------------------
    col_bot1, col_bot2, col_bot3 = st.columns(3)

    # --- COLUMNA 1: PROGRAMADAS P/ HOY ---
    with col_bot1:
        st.markdown(
            "<h4 style='font-size: 14px; font-weight: 700; color: #F3F4F6; margin-bottom: 8px;'>📅 PROGRAMADAS P/ HOY</h4>",
            unsafe_allow_html=True,
        )
        df_hoy = df_vista[df_vista["Fecha_dt"] == hoy_dt]
        if not df_hoy.empty:
            ordenes_hoy_list = [
                str(o) for o in df_hoy[col_ord_main].dropna().unique() if str(o) != ""
            ]
            html_prog = "<div style='background-color: #111827; border: 1px solid #1F2937; border-radius: 8px; padding: 10px; max-height: 180px; overflow-y: auto;'>"
            for ord_item in ordenes_hoy_list:
                html_prog += f"<div style='padding: 4px 8px; border-bottom: 1px solid #1F2937; font-size: 12px; color: #60A5FA; font-weight: 600;'>📦 Orden #{ord_item}</div>"
            html_prog += "</div>"
            st.markdown(clean_html(html_prog), unsafe_allow_html=True)
        else:
            st.markdown(
                clean_html("<div style='background-color: #111827; border: 1px solid #1F2937; border-radius: 8px; padding: 12px; color: #9CA3AF; font-size: 12px; text-align: center;'>No hay órdenes agendadas para hoy.</div>"),
                unsafe_allow_html=True,
            )

    # --- COLUMNA 2: META DEL DÍA ---
    with col_bot2:
        st.markdown(
            "<h4 style='font-size: 14px; font-weight: 700; color: #F3F4F6; margin-bottom: 8px;'>🎯 META Y AVANCE DEL DÍA</h4>",
            unsafe_allow_html=True,
        )

        df_hoy_meta = df_proceso[df_proceso["Fecha_dt"] == hoy_dt]

        enviadas_count = 0
        crm_count = 0
        firmadas_count = 0
        pendientes_count = 0
        scores_hoy = []

        if not df_hoy_meta.empty:
            for _, row in df_hoy_meta.iterrows():
                env_v = str(row.get("Enviado", "")).strip().upper()
                cer_v = str(row.get("Cer firmado", "")).strip().upper()
                crm_v = str(row.get("CRM salida", "")).strip().upper()
                aprob_v = str(row.get("Aprob. Comercial", "")).strip().upper()

                if env_v in ["SI", "SÍ"]:
                    score = 100
                    enviadas_count += 1
                elif crm_v not in ["", "NAN", "NONE", "NULL", "PENDIENTE"] or aprob_v in ["SI", "SÍ", "APROBADO"]:
                    score = 70
                    crm_count += 1
                elif cer_v in ["SI", "SÍ"]:
                    score = 40
                    firmadas_count += 1
                else:
                    score = 15
                    pendientes_count += 1

                scores_hoy.append(score)

            porcentaje_global_hoy = (
                int(sum(scores_hoy) / len(scores_hoy)) if scores_hoy else 0
            )
            total_ordenes_hoy = len(scores_hoy)
        else:
            porcentaje_global_hoy = 0
            total_ordenes_hoy = 0

        meta_html = f"""
        <div style="background-color: #111827; border: 1px solid #1F2937; border-radius: 8px; padding: 12px 14px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                <span style="font-size: 11px; font-weight: 700; color: #9CA3AF; letter-spacing: 0.5px;">AVANCE GENERAL DE HOY</span>
                <span style="font-size: 20px; font-weight: 800; color: #10B981;">{porcentaje_global_hoy}%</span>
            </div>
            
            <div style="background-color: #1F2937; border-radius: 10px; height: 10px; width: 100%; overflow: hidden; margin-bottom: 10px;">
                <div style="background: linear-gradient(90deg, #3B82F6 0%, #10B981 100%); height: 100%; width: {porcentaje_global_hoy}%; border-radius: 10px; transition: width 0.5s ease-in-out;"></div>
            </div>

            <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 6px; font-size: 11px;">
                <div style="background: #1E293B; padding: 5px 8px; border-radius: 5px; color: #A7F3D0; border-left: 3px solid #10B981;">
                    <b>📦 Enviadas (100%):</b> {enviadas_count}/{total_ordenes_hoy}
                </div>
                <div style="background: #1E293B; padding: 5px 8px; border-radius: 5px; color: #FDE68A; border-left: 3px solid #F59E0B;">
                    <b>📑 Listo CRM (70%):</b> {crm_count}
                </div>
                <div style="background: #1E293B; padding: 5px 8px; border-radius: 5px; color: #60A5FA; border-left: 3px solid #3B82F6;">
                    <b>✏️ Firmadas (40%):</b> {firmadas_count}
                </div>
                <div style="background: #1E293B; padding: 5px 8px; border-radius: 5px; color: #9CA3AF; border-left: 3px solid #6B7280;">
                    <b>⏳ En Proceso (15%):</b> {pendientes_count}
                </div>
            </div>
        </div>
        """
        st.markdown(clean_html(meta_html), unsafe_allow_html=True)

    # --- COLUMNA 3: BITÁCORA / AVISOS DEL DÍA ---
    with col_bot3:
        st.markdown(
            "<h4 style='font-size: 14px; font-weight: 700; color: #F3F4F6; margin-bottom: 8px;'>📋 BITÁCORA / AVISOS DEL DÍA</h4>",
            unsafe_allow_html=True,
        )
        if not df_notas.empty:
            html_notas = "<div style='max-height: 180px; overflow-y: auto;'>"
            for _, nota in df_notas.iterrows():
                prio = str(nota.get("Prioridad", "media")).strip()
                msg = str(nota.get("Nota", nota.get("Mensaje", ""))).strip()
                hora = str(nota.get("Hora", "")).strip()
                if msg:
                    html_notas += render_bitacora_card(prio, msg, hora)
            html_notas += "</div>"
            st.markdown(clean_html(html_notas), unsafe_allow_html=True)
        else:
            st.markdown(
                render_bitacora_card(
                    "baja", "Sistema operando normalmente sin novedades registradas.", "08:00 AM"
                ),
                unsafe_allow_html=True,
            )


# ==========================================
# 6. PUNTO DE ENTRADA PRINCIPAL
# ==========================================
if __name__ == "__main__":
    render_tablero_fluido()
