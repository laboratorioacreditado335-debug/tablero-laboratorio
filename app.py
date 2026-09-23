from datetime import datetime
import time
import urllib.parse
import numpy as np
import pandas as pd
import streamlit as st

# ---------------------------------------------------------
# CONFIGURACIÓN DE PÁGINA Y ESTILOS MODO OSCURO INTEGRAL
# ---------------------------------------------------------
st.set_page_config(
    page_title="Tablero de Control - Laboratorio", page_icon="📊", layout="wide"
)

st.markdown(
    """
<style>
    header, [data-testid="stHeader"] { display: none !important; }
    .block-container { padding-top: 0.4rem !important; padding-bottom: 0.4rem !important; }

    .stApp { background-color: #0B1120; color: #F3F4F6; }
    
    /* COMPACTACIÓN DE TARJETAS KPI */
    .kpi-card {
        background-color: #111827;
        border: 1px solid #1F2937;
        border-radius: 8px;
        padding: 8px 12px;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.4);
    }
    .kpi-title {
        color: #9CA3AF;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.8px;
        text-transform: uppercase;
        margin-bottom: 2px;
    }
    .kpi-value { color: #FFFFFF; font-size: 24px; font-weight: 800; }

    /* TARJETAS DE ÓRDENES Y SECCIÓN INFERIOR SIN SCROLLBAR */
    .order-card {
        background-color: #1E293B;
        border-left: 4px solid #3B82F6;
        border-radius: 6px;
        padding: 6px 12px;
        margin-bottom: 6px;
        font-weight: 600;
        color: #F8FAFC;
        font-size: 13px;
    }

    /* TARJETA DE PROGRESO DE ETAPA POR ÓRDEN */
    .progress-order-card {
        background-color: #111827;
        border: 1px solid #1F2937;
        border-radius: 6px;
        padding: 6px 10px;
        margin-bottom: 6px;
    }

    div.stButton > button {
        background-color: #1E293B !important;
        color: #38BDF8 !important;
        border: 1px solid #3B82F6 !important;
        border-radius: 6px !important;
        font-weight: 700 !important;
        font-size: 12.5px !important;
        padding: 4px 12px !important;
        width: 100% !important;
        transition: all 0.2s ease-in-out !important;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3) !important;
    }
    div.stButton > button:hover {
        background-color: #2563EB !important;
        color: #FFFFFF !important;
        border-color: #60A5FA !important;
        box-shadow: 0 0 12px rgba(59, 130, 246, 0.6) !important;
        cursor: pointer !important;
    }

    /* ESTILO INTEGRADO PARA EL CAMPO DE BÚSQUEDA */
    div[data-baseweb="input"] {
        background-color: #111827 !important;
        border: 1px solid #3B82F6 !important;
        border-radius: 6px !important;
    }
    div[data-baseweb="input"] input {
        color: #F3F4F6 !important;
        font-size: 13px !important;
        padding: 4px 8px !important;
    }

    @keyframes pulse-correccion {
        0% { background-color: rgba(239, 68, 68, 0.12); }
        50% { background-color: rgba(239, 68, 68, 0.30); }
        100% { background-color: rgba(239, 68, 68, 0.12); }
    }
    .row-correccion {
        animation: pulse-correccion 2.2s infinite !important;
        border-left: 5px solid #EF4444 !important;
    }

    ::-webkit-scrollbar { width: 5px; height: 5px; }
    ::-webkit-scrollbar-track { background: #0B1120; }
    ::-webkit-scrollbar-thumb { background: #1F2937; border-radius: 4px; }
    ::-webkit-scrollbar-thumb:hover { background: #374151; }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""",
    unsafe_allow_html=True,
)

SPREADSHEET_ID = "1bNDr35UasLS5zly1Sbq2ykbtmsTn9Fy4"

if "page_index" not in st.session_state:
    st.session_state.page_index = 0
if "last_switch_time" not in st.session_state:
    st.session_state.last_switch_time = time.time()
if "search_term" not in st.session_state:
    st.session_state.search_term = ""


# ---------------------------------------------------------
# FUNCIONES AUXILIARES Y PARSER ROBUSTO DE FECHAS
# ---------------------------------------------------------
def limpiar_texto(val):
    if pd.isna(val) or val is None:
        return ""
    val_str = str(val).strip()
    if val_str.endswith(".0"):
        val_str = val_str[:-2]
    return val_str


def leer_hoja_google(nombre_hoja, header_none=False):
    nombre_enc = urllib.parse.quote(nombre_hoja)
    nocache = int(time.time())
    url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet={nombre_enc}&_cb={nocache}"
    if header_none:
        return pd.read_csv(url, header=None)
    return pd.read_csv(url)


def parsear_fecha(val):
    if pd.isna(val) or val is None:
        return None
    if isinstance(val, (datetime, pd.Timestamp)):
        return val.date()

    val_str = str(val).strip()
    if (
        not val_str
        or val_str.lower() in ["nan", "none", "nat", "null"]
        or val_str.startswith("#")
    ):
        return None

    # Número de serie Excel (ej. 46288)
    try:
        num_val = float(val_str)
        if 30000 < num_val < 70000:
            dt = pd.to_datetime(num_val, unit="D", origin="1899-12-30")
            return dt.date()
    except (ValueError, TypeError):
        pass

    val_clean = val_str.split(" ")[0].strip()

    # M/D/YYYY o YYYY-MM-DD
    try:
        dt = pd.to_datetime(val_clean, dayfirst=False, errors="coerce")
        if pd.notna(dt):
            return dt.date()
    except Exception:
        pass

    # D/M/YYYY
    try:
        dt = pd.to_datetime(val_clean, dayfirst=True, errors="coerce")
        if pd.notna(dt):
            return dt.date()
    except Exception:
        pass

    return None


def calcular_progreso_orden(row):
    """
    Calcula el porcentaje de avance por etapas de una orden individual hacia CRM Salida:
    1. Registrada = 20%
    2. Aprobación Comercial = +20% (40%)
    3. Certificado Firmado = +20% (60%)
    4. CRM Certificado = +20% (80%)
    5. CRM Salida / Enviado = +20% (100%)
    """
    progreso = 20  # Base por estar registrada

    aprob = str(row.get("Aprob. Comercial", "")).strip().upper()
    cer = str(row.get("Cer firmado", "")).strip().upper()
    crm_cert = str(row.get("CRM cert.", "")).strip().upper()
    crm_sal = str(row.get("CRM salida", "")).strip().upper()
    env = str(row.get("Enviado", "")).strip().upper()

    if aprob in ["SI", "SÍ", "APROBADO", "OK"] or (
        aprob and aprob not in ["NO", "PENDIENTE", "NAN", "NONE", ""]
    ):
        progreso += 20

    if cer in ["SI", "SÍ"]:
        progreso += 20

    if crm_cert and crm_cert not in ["", "NAN", "NONE", "PENDIENTE", "NO"]:
        progreso += 20

    if (crm_sal and crm_sal not in ["", "NAN", "NONE", "PENDIENTE", "NO"]) or env in [
        "SI",
        "SÍ",
    ]:
        progreso += 20

    return min(100, progreso)


def cargar_datos_gsheets():
    try:
        df_proceso_raw = leer_hoja_google("C. Proceso órdenes", header_none=True)
        df_notas_raw = leer_hoja_google("NOTAS DEL DIA")

        df_proceso = pd.DataFrame()

        if df_proceso_raw is not None and not df_proceso_raw.empty:
            header_idx = None
            for idx, row in df_proceso_raw.iterrows():
                row_str = " ".join(row.dropna().astype(str)).upper()
                if "FECHA" in row_str and ("ORDEN" in row_str or "CER" in row_str):
                    header_idx = idx
                    break

            if header_idx is not None:
                df_proceso = df_proceso_raw.iloc[header_idx + 1 :].copy()
                df_proceso.columns = [
                    str(c).strip() for c in df_proceso_raw.iloc[header_idx].values
                ]
            else:
                df_proceso = df_proceso_raw.iloc[1:].copy()
                df_proceso.columns = [
                    str(c).strip() for c in df_proceso_raw.iloc[0].values
                ]

        df_notas = pd.DataFrame()
        if df_notas_raw is not None and not df_notas_raw.empty:
            header_n_idx = None
            for idx, row in df_notas_raw.iterrows():
                row_str = " ".join(row.dropna().astype(str)).upper()
                if (
                    "DESCRIPCIÓN" in row_str
                    or "DESCRIPCION" in row_str
                    or "TIPO" in row_str
                    or "NOTA" in row_str
                ):
                    header_n_idx = idx
                    break

            if header_n_idx is not None:
                df_notas = df_notas_raw.iloc[header_n_idx + 1 :].copy()
                df_notas.columns = df_notas_raw.iloc[header_n_idx].values
            else:
                df_notas = df_notas_raw.copy()

            df_notas.columns = [str(col).strip() for col in df_notas.columns]
            df_notas = df_notas.dropna(how="all")

        return df_proceso, df_notas, "Conectado correctamente"

    except Exception as e:
        return None, None, f"Error al conectar con Google Sheets: {str(e)}"


def render_dark_table(df_page):
    if df_page.empty:
        return "<div style='color: #9CA3AF; text-align: center; padding: 15px;'>Sin datos o registros coincidentes con la búsqueda.</div>"

    headers = list(df_page.columns)

    col_cer = next(
        (c for c in headers if "CER" in c.upper() and "FIRM" in c.upper()), None
    )
    col_crm_salida = next(
        (c for c in headers if "CRM" in c.upper() and "SALIDA" in c.upper()), None
    )
    col_orden = next((c for c in headers if "ORDEN" in c.upper()), None)

    html = '<div style="overflow-x: auto; border: 1px solid #1F2937; border-radius: 8px; background-color: #111827; margin-bottom: 6px;"><table style="width: 100%; border-collapse: collapse; color: #F3F4F6; font-size: 12.5px; text-align: left;"><thead><tr style="background-color: #1F2937; color: #9CA3AF; font-weight: 700; text-transform: uppercase; font-size: 10.5px; letter-spacing: 0.5px;">'

    for h in headers:
        html += f'<th style="padding: 6px 10px; border-bottom: 1px solid #374151;">{h}</th>'
    html += "</tr></thead><tbody>"

    for idx, row in df_page.iterrows():
        cer_val = (
            str(row[col_cer]).strip().upper()
            if col_cer and pd.notna(row[col_cer])
            else ""
        )
        crm_sal_val = (
            str(row[col_crm_salida]).strip()
            if col_crm_salida and pd.notna(row[col_crm_salida])
            else ""
        )

        es_correccion = "CORREC" in cer_val
        cer_es_si = cer_val in ["SI", "SÍ"]
        crm_vacio = crm_sal_val in [
            "",
            "nan",
            "none",
            "null",
            "None",
            "PENDIENTE",
            "Pendiente",
        ]
        es_atascada = cer_es_si and crm_vacio

        if es_correccion:
            tr_style = (
                'style="border-bottom: 1px solid #EF4444;" class="row-correccion"'
            )
        elif es_atascada:
            tr_style = 'style="border-bottom: 1px solid #F59E0B; background-color: rgba(245, 158, 11, 0.08); border-left: 4px solid #F59E0B;"'
        else:
            tr_style = 'style="border-bottom: 1px solid #1F2937;"'

        html += f"<tr {tr_style}>"
        for h in headers:
            val = limpiar_texto(row[h])

            if h == col_orden and es_atascada:
                badge = f'{val} <span style="background-color: rgba(245, 158, 11, 0.25); color: #FBBF24; border: 1px solid #F59E0B; padding: 1px 5px; border-radius: 6px; font-weight: 700; font-size: 9.5px; margin-left: 4px;" title="Certificado firmado pero sin registro de CRM Salida">⚠️ Atascada</span>'
            elif val.upper() in ["SI", "SÍ"]:
                badge = '<span style="background-color: rgba(16, 185, 129, 0.2); color: #A7F3D0; border: 1px solid #10B981; padding: 1px 6px; border-radius: 8px; font-weight: 700; font-size: 10px;">Si</span>'
            elif "APROBAC" in val.upper() or "PENDIENTE" in val.upper():
                badge = f'<span style="background-color: rgba(245, 158, 11, 0.2); color: #FDE68A; border: 1px solid #F59E0B; padding: 1px 6px; border-radius: 8px; font-weight: 600; font-size: 10px;">{val}</span>'
            elif "CORREC" in val.upper():
                badge = f'<span style="background-color: rgba(239, 68, 68, 0.35); color: #FCA5A5; border: 1px solid #EF4444; padding: 1px 6px; border-radius: 8px; font-weight: 800; font-size: 10px;">{val} ⚠️</span>'
            else:
                badge = val

            html += f'<td style="padding: 5px 10px;">{badge}</td>'
        html += "</tr>"

    html += "</tbody></table></div>"
    return html


def render_bitacora_card(prioridad_val, descripcion_val, estado_val):
    prioridad = (
        str(prioridad_val if pd.notna(prioridad_val) else "NORMAL")
        .strip()
        .upper()
    )
    descripcion = str(
        descripcion_val if pd.notna(descripcion_val) else ""
    ).strip()
    estado = (
        str(estado_val if pd.notna(estado_val) else "PENDIENTE").strip().upper()
    )

    priority_colors = {
        "URGENTE": "#EF4444",
        "REVISIÓN": "#F59E0B",
        "REVISION": "#F59E0B",
        "AVISO": "#3B82F6",
        "NORMAL": "#6B7280",
        "MANTENIMIENTO": "#10B981",
    }
    border_color = priority_colors.get(prioridad, "#3B82F6")

    status_styles = {
        "PENDIENTE": {
            "bg": "rgba(239, 68, 68, 0.2)",
            "text": "#FCA5A5",
            "border": "#EF4444",
        },
        "EN PROCESO": {
            "bg": "rgba(245, 158, 11, 0.2)",
            "text": "#FDE68A",
            "border": "#F59E0B",
        },
        "COMPLETADO": {
            "bg": "rgba(16, 185, 129, 0.2)",
            "text": "#A7F3D0",
            "border": "#10B981",
        },
    }
    s_style = status_styles.get(
        estado,
        {"bg": "rgba(107, 114, 128, 0.2)", "text": "#E5E7EB", "border": "#9CA3AF"},
    )

    return f'<div style="background: #111827; border-left: 4px solid {border_color}; border-radius: 6px; padding: 8px 12px; margin-bottom: 6px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3); display: flex; justify-content: space-between; align-items: center; gap: 10px;"><div style="color: #F3F4F6; font-size: 12.5px; font-weight: 500; line-height: 1.3; flex-grow: 1;">{descripcion}</div><div style="background-color: {s_style["bg"]}; color: {s_style["text"]}; border: 1px solid {s_style["border"]}; font-size: 10.5px; font-weight: 700; padding: 3px 8px; border-radius: 10px; letter-spacing: 0.5px; white-space: nowrap;">{estado}</div></div>'


# ---------------------------------------------------------
# TABLERO DE CONTROL DINÁMICO Y FLUIDO
# ---------------------------------------------------------
@st.fragment(run_every=5)
def render_tablero_fluido():
    df_main, df_bitacora, info_estado = cargar_datos_gsheets()

    cols_deseadas = [
        "Fecha",
        "# Orden",
        "Cer firmado",
        "Enviado",
        "CRM salida",
        "Aprob. Comercial",
        "CRM cert.",
    ]
    df_vista = pd.DataFrame()
    df_hoy = pd.DataFrame()

    ordenes_hoy = []
    total_hoy = 0

    hoy_dt = datetime.now().date()
    fecha_activa_str = hoy_dt.strftime("%d/%m/%Y")

    total_reg = 0
    total_firm = 0
    total_env = 0
    total_pend = 0

    if df_main is not None and not df_main.empty:
        # Mapeo de columnas dinámico
        mapa_cols = {}
        for col in df_main.columns:
            c_upper = str(col).upper()
            if "FECHA" in c_upper and "Fecha" not in mapa_cols.values():
                mapa_cols[col] = "Fecha"
            elif (
                ("ORDEN" in c_upper or "ORD" in c_upper)
                and "# Orden" not in mapa_cols.values()
            ):
                mapa_cols[col] = "# Orden"
            elif (
                "CER" in c_upper
                and "FIRM" in c_upper
                and "Cer firmado" not in mapa_cols.values()
            ):
                mapa_cols[col] = "Cer firmado"
            elif "ENV" in c_upper and "Enviado" not in mapa_cols.values():
                mapa_cols[col] = "Enviado"
            elif (
                "CRM" in c_upper
                and "SAL" in c_upper
                and "CRM salida" not in mapa_cols.values()
            ):
                mapa_cols[col] = "CRM salida"
            elif (
                ("APROB" in c_upper or "COMER" in c_upper)
                and "Aprob. Comercial" not in mapa_cols.values()
            ):
                mapa_cols[col] = "Aprob. Comercial"
            elif (
                "CRM" in c_upper
                and "CERT" in c_upper
                and "CRM cert." not in mapa_cols.values()
            ):
                mapa_cols[col] = "CRM cert."

        df_renamed = df_main.rename(columns=mapa_cols)

        if "Fecha" not in df_renamed.columns and len(df_renamed.columns) > 0:
            df_renamed.rename(columns={df_renamed.columns[0]: "Fecha"}, inplace=True)

        cols_existentes = [c for c in cols_deseadas if c in df_renamed.columns]
        df_vista = df_renamed[cols_existentes].copy()

        col_ord_main = (
            "# Orden"
            if "# Orden" in df_vista.columns
            else cols_existentes[min(1, len(cols_existentes) - 1)]
        )

        # 1. PROPAGACIÓN VERTICAL DE FECHAS (FFILL PARA CELDAS COMBINADAS EN EXCEL)
        if "Fecha" in df_vista.columns:
            df_vista["Fecha_Raw"] = df_vista["Fecha"].astype(str).str.strip()
            df_vista["Fecha_Raw"] = df_vista["Fecha_Raw"].replace(
                [
                    "",
                    "nan",
                    "none",
                    "null",
                    "nat",
                    "NaN",
                    "None",
                    "#ERROR!",
                    "#N/A",
                    "#VALOR!",
                ],
                np.nan,
            )
            df_vista["Fecha_Raw"] = df_vista["Fecha_Raw"].ffill()

        # 2. FILTRADO DE FILAS VÁLIDAS DE ÓRDENES
        df_vista[col_ord_main] = df_vista[col_ord_main].apply(limpiar_texto)
        df_vista = df_vista[
            df_vista[col_ord_main].notna()
            & (df_vista[col_ord_main] != "")
            & (
                ~df_vista[col_ord_main]
                .str.lower()
                .isin(["nan", "none", "null", "nat", "#orden"])
            )
            & (~df_vista[col_ord_main].str.startswith("#"))
        ].copy()

        if "Fecha_Raw" in df_vista.columns:
            df_vista["Fecha_dt"] = df_vista["Fecha_Raw"].apply(parsear_fecha)

            # Formato de visualización de fecha
            def formatear_fecha_mostrar(row):
                dt = row["Fecha_dt"]
                if pd.notna(dt) and dt is not None:
                    return dt.strftime("%d/%m/%Y")
                raw = str(row["Fecha_Raw"]).strip()
                return raw if raw and raw.lower() != "nan" else ""

            df_vista["Fecha"] = df_vista.apply(formatear_fecha_mostrar, axis=1)

            # Totales KPIs Globales
            total_reg = len(df_vista)
            if "Cer firmado" in df_vista.columns:
                total_firm = (
                    df_vista["Cer firmado"]
                    .astype(str)
                    .str.strip()
                    .str.upper()
                    .isin(["SI", "SÍ"])
                    .sum()
                )
            if "Enviado" in df_vista.columns:
                total_env = (
                    df_vista["Enviado"]
                    .astype(str)
                    .str.strip()
                    .str.upper()
                    .isin(["SI", "SÍ"])
                    .sum()
                )
            total_pend = max(0, total_reg - total_env)

            # OBTENER ÓRDENES DE HOY DESDE EXCEL (O ÚLTIMA FECHA DISPONIBLE)
            df_hoy = df_vista[df_vista["Fecha_dt"] == hoy_dt].copy()

            if df_hoy.empty and not df_vista["Fecha_dt"].dropna().empty:
                max_dt = df_vista["Fecha_dt"].dropna().max()
                df_hoy = df_vista[df_vista["Fecha_dt"] == max_dt].copy()
                fecha_activa_str = max_dt.strftime("%d/%m/%Y")
            else:
                fecha_activa_str = hoy_dt.strftime("%d/%m/%Y")

            ordenes_raw = df_hoy[col_ord_main].dropna().tolist()
            ordenes_hoy = list(dict.fromkeys(ordenes_raw))
            total_hoy = len(ordenes_hoy)

            # Ordenar por fecha descendente
            df_vista = df_vista.sort_values(
                by=["Fecha_dt", col_ord_main], ascending=[False, True]
            ).reset_index(drop=True)

            df_vista = df_vista.drop(
                columns=["Fecha_dt", "Fecha_Raw"], errors="ignore"
            )

    # 1. KPIs SUPERIORES
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(
            f'<div class="kpi-card"><div'
            ' class="kpi-title">REGISTRADAS</div><div'
            f' class="kpi-value">{total_reg}</div></div>',
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f'<div class="kpi-card"><div class="kpi-title">FIRMADAS ✏️</div><div'
            f' class="kpi-value">{total_firm}</div></div>',
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            f'<div class="kpi-card"><div class="kpi-title">ENVIADAS 📦</div><div'
            f' class="kpi-value">{total_env}</div></div>',
            unsafe_allow_html=True,
        )
    with col4:
        st.markdown(
            f'<div class="kpi-card"><div class="kpi-title">PENDIENTES ⌛</div><div'
            f' class="kpi-value">{total_pend}</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown("<div style='margin-bottom: 6px;'></div>", unsafe_allow_html=True)

    # 2. TABLA PRINCIPAL CON NAVEGACIÓN Y BUSCADOR
    if df_vista is not None and not df_vista.empty:
        col_btn1, col_btn2, col_search, col_info = st.columns([1.1, 1.1, 1.8, 2.5])

        with col_btn1:
            if st.button("⬆️ Subir"):
                st.session_state.page_index = max(0, st.session_state.page_index - 1)
                st.session_state.last_switch_time = time.time()
                st.rerun()

        with col_btn2:
            if st.button("⬇️ Bajar"):
                st.session_state.page_index += 1
                st.session_state.last_switch_time = time.time()
                st.rerun()

        with col_search:
            search_val = st.text_input(
                "Buscar Orden",
                value=st.session_state.get("search_term", ""),
                placeholder="🔍 Buscar N° Orden...",
                key="search_input_widget",
                label_visibility="collapsed",
            )
            st.session_state.search_term = search_val

        # FILTRADO POR BÚSQUEDA
        if st.session_state.search_term.strip():
            term = st.session_state.search_term.strip().lower()
            col_target = "# Orden" if "# Orden" in df_vista.columns else df_vista.columns[0]
            df_vista = df_vista[
                df_vista[col_target].astype(str).str.lower().str.contains(term, na=False)
            ]

        # PAGINACIÓN DE 10 ÓRDENES POR PÁGINA
        filas_por_pagina = 10
        total_filas = len(df_vista)
        total_paginas = max(1, (total_filas + filas_por_pagina - 1) // filas_por_pagina)

        ahora = time.time()

        # PÁGINA 1 DURA 180s (3 MIN), LAS DEMÁS PÁGINAS DURAN 90s
        tiempo_permanencia = 180 if st.session_state.page_index == 0 else 90

        if (ahora - st.session_state.last_switch_time) >= tiempo_permanencia and total_paginas > 1:
            st.session_state.page_index = (st.session_state.page_index + 1) % total_paginas
            st.session_state.last_switch_time = ahora

        if st.session_state.page_index >= total_paginas:
            st.session_state.page_index = 0

        with col_info:
            segundos_restantes = max(0, int(tiempo_permanencia - (ahora - st.session_state.last_switch_time)))
            st.caption(
                f"Pág. {st.session_state.page_index + 1}/{total_paginas} ({total_filas} registros)"
                f" | ⏱️ Auto-cambio en {segundos_restantes}s"
            )

        p_idx = st.session_state.page_index
        inicio = p_idx * filas_por_pagina
        fin = min(inicio + filas_por_pagina, total_filas)
        df_pagina = df_vista.iloc[inicio:fin]

        st.markdown(render_dark_table(df_pagina), unsafe_allow_html=True)

    else:
        st.error(f"⚠️ {info_estado}")

    st.markdown(
        "<hr style='border-color: #1F2937; margin: 8px 0;'>",
        unsafe_allow_html=True,
    )

    # 3. SECCIÓN INFERIOR (SIN BARRAS DE DESPLAZAMIENTO INTEGRANDO ESPACIO LIBRE)
    c_left, c_middle, c_right = st.columns([1, 1.2, 1.2])

    with c_left:
        st.markdown("<h4 style='margin:0 0 2px 0; font-size:14px; color:#F3F4F6;'>🚚 Programadas p/ Hoy</h4>", unsafe_allow_html=True)
        st.caption(f"🗓️ Fecha: **{fecha_activa_str}** | {total_hoy} agendadas")
        
        if ordenes_hoy:
            html_list = '<div style="display: flex; flex-direction: column; gap: 4px;">'
            for ord_num in ordenes_hoy:
                html_list += f'<div class="order-card">📦 Orden #: {ord_num}</div>'
            html_list += "</div>"
            st.markdown(html_list, unsafe_allow_html=True)
        else:
            st.info(f"Sin órdenes programadas hoy ({fecha_activa_str}).")

    with c_middle:
        st.markdown("<h4 style='margin:0 0 2px 0; font-size:14px; color:#F3F4F6;'>📈 Progreso por Etapas (CRM Salida)</h4>", unsafe_allow_html=True)
        
        progresos = []
        if df_hoy is not None and not df_hoy.empty:
            for _, r in df_hoy.iterrows():
                progresos.append((limpiar_texto(r.get('# Orden', '')), calcular_progreso_orden(r)))

        acumulado_general = int(np.mean([p[1] for p in progresos])) if progresos else 0
        st.caption(f"📊 Acumulado del Día: **{acumulado_general}%**")

        # Barra de Acumulado General del Día
        st.markdown(
            f"""
            <div style="background-color: #111827; border: 1px solid #1F2937; border-radius: 6px; padding: 10px 12px; margin-bottom: 8px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                    <span style="font-size: 11px; font-weight: 700; color: #9CA3AF; letter-spacing: 0.5px;">PROMEDIO GENERAL DEL DÍA</span>
                    <span style="font-size: 16px; font-weight: 800; color: #38BDF8;">{acumulado_general}%</span>
                </div>
                <div style="background-color: #1F2937; border-radius: 10px; height: 10px; width: 100%; overflow: hidden;">
                    <div style="background: linear-gradient(90deg, #3B82F6, #10B981); height: 100%; width: {acumulado_general}%; border-radius: 10px; transition: width 0.5s ease-in-out;"></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Listado de avance individual por orden
        if progresos:
            html_progresos = '<div style="display: flex; flex-direction: column; gap: 4px;">'
            for ord_num, pct in progresos:
                bar_color = "#10B981" if pct == 100 else ("#3B82F6" if pct >= 60 else "#F59E0B")
                html_progresos += f"""
                <div class="progress-order-card">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                        <span style="font-size: 12px; font-weight: 700; color: #F3F4F6;">Orden #{ord_num}</span>
                        <span style="font-size: 11.5px; font-weight: 800; color: {bar_color};">{pct}%</span>
                    </div>
                    <div style="background-color: #1F2937; border-radius: 6px; height: 6px; width: 100%; overflow: hidden;">
                        <div style="background-color: {bar_color}; height: 100%; width: {pct}%;"></div>
                    </div>
                </div>
                """
            html_progresos += '</div>'
            st.markdown(html_progresos, unsafe_allow_html=True)
        else:
            st.info("Sin registros de progreso hoy.")

    with c_right:
        st.markdown("<h4 style='margin:0 0 2px 0; font-size:14px; color:#F3F4F6;'>📌 Bitácora / Avisos del Día</h4>", unsafe_allow_html=True)
        st.caption("Avisos y notas registradas en tiempo real")
        
        if df_bitacora is None or df_bitacora.empty:
            st.info("Sin avisos en 'NOTAS DEL DIA'.")
        else:
            col_p = next((c for c in df_bitacora.columns if "TIPO" in str(c).upper() or "PRIORIDAD" in str(c).upper()), None)
            col_d = next((c for c in df_bitacora.columns if "DESCRIP" in str(c).upper() or "NOTA" in str(c).upper() or "AVISO" in str(c).upper()), None)
            col_e = next((c for c in df_bitacora.columns if "ESTADO" in str(c).upper()), None)

            avisos_html = '<div style="display: flex; flex-direction: column; gap: 4px;">'
            avisos_cont = 0
            for _, row in df_bitacora.iterrows():
                p_val = row[col_p] if col_p else "NORMAL"
                d_val = row[col_d] if col_d else ""
                e_val = row[col_e] if col_e else "PENDIENTE"

                if (
                    pd.notna(d_val)
                    and str(d_val).strip() != ""
                    and str(d_val).strip().lower() != "nan"
                ):
                    avisos_html += render_bitacora_card(p_val, d_val, e_val)
                    avisos_cont += 1
            avisos_html += "</div>"

            if avisos_cont > 0:
                st.markdown(avisos_html, unsafe_allow_html=True)
            else:
                st.info("No hay descripciones activas en la tabla de notas.")


render_tablero_fluido()
