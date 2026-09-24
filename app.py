from datetime import datetime
import time
import urllib.parse
import numpy as np
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# ---------------------------------------------------------
# ID DEL GOOGLE SHEET
# ---------------------------------------------------------
SPREADSHEET_ID = "1CvPEtDspm7g3T7yXDluEUD7kGyWH5abNAP1nkalX6sI"

# ---------------------------------------------------------
# CONFIGURACIÓN DE PÁGINA Y ESTILOS MODO OSCURO
# ---------------------------------------------------------
st.set_page_config(
    page_title="Tablero de Control - Laboratorio", page_icon="📊", layout="wide"
)

st.markdown(
    """
<style>
    /* OCULTAR ENCABEZADOS Y AJUSTAR CONTENEDOR PRINCIPAL */
    header, [data-testid="stHeader"] { display: none !important; }
    .block-container { 
        padding-top: 0.2rem !important; 
        padding-bottom: 0.2rem !important; 
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }

    .stApp { background-color: #0B1120; color: #F3F4F6; font-size: 14px; }
    
    /* TARJETAS KPI ESCALADAS */
    .kpi-card {
        background-color: #111827;
        border: 1px solid #1F2937;
        border-radius: 6px;
        padding: 6px 10px;
        text-align: center;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.4);
    }
    .kpi-title {
        color: #9CA3AF;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        margin-bottom: 1px;
    }
    .kpi-value { color: #FFFFFF; font-size: 22px; font-weight: 800; line-height: 1.1; }

    /* TARJETAS DE PROGRESO DE ETAPA POR ÓRDEN */
    .progress-order-card {
        background-color: #111827;
        border: 1px solid #1F2937;
        border-radius: 5px;
        padding: 5px 8px;
        margin-bottom: 3px;
    }

    /* CONTROLES Y BOTONES */
    div.stButton > button {
        background-color: #1E293B !important;
        color: #38BDF8 !important;
        border: 1px solid #3B82F6 !important;
        border-radius: 5px !important;
        font-weight: 700 !important;
        font-size: 12.5px !important;
        padding: 2px 8px !important;
        width: 100% !important;
        height: 34px !important;
        transition: all 0.2s ease-in-out !important;
    }
    div.stButton > button:hover {
        background-color: #2563EB !important;
        color: #FFFFFF !important;
        border-color: #60A5FA !important;
        cursor: pointer !important;
    }

    /* CAMPO DE BÚSQUEDA */
    div[data-baseweb="input"] {
        background-color: #111827 !important;
        border: 1px solid #3B82F6 !important;
        border-radius: 5px !important;
        height: 34px !important;
    }
    div[data-baseweb="input"] input {
        color: #F3F4F6 !important;
        font-size: 13px !important;
        padding: 2px 8px !important;
    }

    /* ANIMACIÓN PARPADEO CORRECCIÓN */
    @keyframes pulse-correccion {
        0% { background-color: rgba(239, 68, 68, 0.12); }
        50% { background-color: rgba(239, 68, 68, 0.30); }
        100% { background-color: rgba(239, 68, 68, 0.12); }
    }
    .row-correccion {
        animation: pulse-correccion 2.2s infinite !important;
        border-left: 4px solid #EF4444 !important;
    }

    /* PERSONALIZACIÓN DE BARRAS DE DESPLAZAMIENTO (SCROLLBARS) */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: #111827; border-radius: 4px; }
    ::-webkit-scrollbar-thumb { background: #374151; border-radius: 4px; }
    ::-webkit-scrollbar-thumb:hover { background: #3B82F6; }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""",
    unsafe_allow_html=True,
)

# ESTADOS DE SESIÓN
if "page_index" not in st.session_state:
    st.session_state.page_index = 0
if "last_switch_time" not in st.session_state:
    st.session_state.last_switch_time = time.time()
if "search_term" not in st.session_state:
    st.session_state.search_term = ""
if "manual_nav_bonus" not in st.session_state:
    st.session_state.manual_nav_bonus = 0
if "known_urgents" not in st.session_state:
    st.session_state.known_urgents = None
if "last_search_time" not in st.session_state:
    st.session_state.last_search_time = time.time()
if "last_search_val" not in st.session_state:
    st.session_state.last_search_val = ""

# NUEVOS ESTADOS DE SESIÓN PARA LAS MODIFICACIONES SOLICITADAS
if "acknowledged_urgents" not in st.session_state:
    st.session_state.acknowledged_urgents = set()
if "urgent_start_times" not in st.session_state:
    st.session_state.urgent_start_times = {}
if "prog_day_page" not in st.session_state:
    st.session_state.prog_day_page = 0
if "prog_day_last_switch" not in st.session_state:
    st.session_state.prog_day_last_switch = time.time()


# ---------------------------------------------------------
# FUNCIONES AUXILIARES Y PARSER DE DATOS
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
    nocache = int(time.time() * 1000)
    url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet={nombre_enc}&_cb={nocache}"
    if header_none:
        return pd.read_csv(url, header=None, keep_default_na=False)
    return pd.read_csv(url, keep_default_na=False)


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

    try:
        num_val = float(val_str)
        if 30000 < num_val < 70000:
            dt = pd.to_datetime(num_val, unit="D", origin="1899-12-30")
            return dt.date()
    except (ValueError, TypeError):
        pass

    val_clean = val_str.split(" ")[0].strip()

    try:
        dt = pd.to_datetime(val_clean, dayfirst=False, errors="coerce")
        if pd.notna(dt):
            return dt.date()
    except Exception:
        pass

    try:
        dt = pd.to_datetime(val_clean, dayfirst=True, errors="coerce")
        if pd.notna(dt):
            return dt.date()
    except Exception:
        pass

    return None


# MODIFICACIÓN 4: DETALLE DEL PASO FALTANTE EN ÓRDENES
def calcular_progreso_orden(row):
    progreso = 25
    cer = str(row.get("Cer firmado", row.get("CER FIRMADO", ""))).strip().upper()
    env = str(row.get("Enviado", row.get("ENVIADO", ""))).strip().upper()
    crm_sal = str(row.get("CRM salida", row.get("CRM SALIDA", ""))).strip().upper()

    faltantes = []
    if cer in ["SI", "SÍ"]:
        progreso += 25
    else:
        faltantes.append("CER Firmado")

    if env in ["SI", "SÍ"]:
        progreso += 25
    else:
        faltantes.append("Enviado")

    if crm_sal in ["SI", "SÍ"]:
        progreso += 25
    else:
        faltantes.append("CRM Salida")

    texto_falta = f"Falta: {', '.join(faltantes)}" if faltantes else "¡Completo! 🎉"
    return min(100, progreso), texto_falta


def cargar_datos_gsheets():
    try:
        df_proceso_raw = leer_hoja_google("C. Proceso órdenes", header_none=True)
        df_notas_raw = leer_hoja_google("NOTAS DEL DIA", header_none=True)

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
                    or "PRIORIDA" in row_str
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
            df_notas = df_notas.replace("", np.nan).dropna(how="all")

        return df_proceso, df_notas, "Conectado correctamente"

    except Exception as e:
        return None, None, f"Error al conectar con Google Sheets: {str(e)}"


def render_dark_table(df_page):
    if df_page.empty:
        return "<div style='color: #9CA3AF; text-align: center; padding: 10px; font-size: 13px;'>Sin datos o registros coincidentes.</div>"

    headers = list(df_page.columns)

    col_resp = next((c for c in headers if "RESP" in c.upper()), None)
    col_cer = next(
        (c for c in headers if "CER" in c.upper() and "FIRM" in c.upper()), None
    )
    col_env = next((c for c in headers if "ENV" in c.upper()), None)
    col_crm_salida = next(
        (c for c in headers if "CRM" in c.upper() and "SALIDA" in c.upper()), None
    )
    col_orden = next((c for c in headers if "ORDEN" in c.upper()), None)

    html = '<div style="overflow-x: auto; border: 1px solid #1F2937; border-radius: 6px; background-color: #111827; margin-bottom: 4px;"><table style="width: 100%; border-collapse: collapse; color: #F3F4F6; font-size: 12.5px; text-align: left;"><thead><tr style="background-color: #1F2937; color: #9CA3AF; font-weight: 700; text-transform: uppercase; font-size: 11px; letter-spacing: 0.5px;">'

    for h in headers:
        if h == col_resp:
            html += f'<th style="padding: 5px 4px; border-bottom: 1px solid #374151; width: 75px; text-align: center; white-space: nowrap;">{h}</th>'
        else:
            html += f'<th style="padding: 5px 8px; border-bottom: 1px solid #374151;">{h}</th>'
    html += "</tr></thead><tbody>"

    for idx, row in df_page.iterrows():
        cer_val = (
            str(row[col_cer]).strip().upper()
            if col_cer and pd.notna(row[col_cer])
            else ""
        )
        crm_sal_val = (
            str(row[col_crm_salida]).strip().upper()
            if col_crm_salida and pd.notna(row[col_crm_salida])
            else ""
        )

        es_correccion = "CORREC" in cer_val
        cer_es_si = cer_val in ["SI", "SÍ"]
        crm_vacio = crm_sal_val not in ["SI", "SÍ"]
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
            val_upper = val.upper()

            td_style = "padding: 4px 8px;"

            if h == col_resp:
                td_style = "padding: 4px 4px; text-align: center; width: 75px; white-space: nowrap;"
                badge = f'<span style="color: #38BDF8; font-weight: 700; font-size: 11.5px;">{val}</span>'
            elif h == col_orden and es_atascada:
                badge = f'{val} <span style="background-color: rgba(245, 158, 11, 0.25); color: #FBBF24; border: 1px solid #F59E0B; padding: 1px 5px; border-radius: 4px; font-weight: 700; font-size: 10px;" title="Certificado firmado pero sin registro de CRM Salida">⚠️ Atascada</span>'
            elif val_upper in ["SI", "SÍ"]:
                badge = '<span style="background-color: rgba(16, 185, 129, 0.2); color: #A7F3D0; border: 1px solid #10B981; padding: 1px 6px; border-radius: 4px; font-weight: 700; font-size: 10.5px;">Si</span>'
            elif val != "":
                if (
                    "CORREC" in val_upper
                    or "ERROR" in val_upper
                    or "RECHAZ" in val_upper
                    or "CANCEL" in val_upper
                ):
                    badge = f'<span style="background-color: rgba(239, 68, 68, 0.25); color: #FCA5A5; border: 1px solid #EF4444; padding: 1px 6px; border-radius: 4px; font-weight: 700; font-size: 10.5px;">{val} ⚠️</span>'
                elif (
                    h in [col_env, col_crm_salida, col_cer]
                    or "APROBAC" in val_upper
                    or "PENDIENTE" in val_upper
                    or val_upper.startswith("P.")
                    or "FIRMAR" in val_upper
                    or "REVISAR" in val_upper
                ):
                    badge = f'<span style="background-color: rgba(245, 158, 11, 0.2); color: #FDE68A; border: 1px solid #F59E0B; padding: 1px 6px; border-radius: 4px; font-weight: 600; font-size: 10.5px;">{val}</span>'
                else:
                    badge = val
            else:
                badge = ""

            html += f'<td style="{td_style}">{badge}</td>'
        html += "</tr>"

    html += "</tbody></table></div>"
    return html


# MODIFICACIÓN 3: TARJETA DE BITÁCORA CON BARRA DINÁMICA DE TIEMPO
def render_bitacora_card(prioridad_val, descripcion_val, estado_val, is_ack=False):
    prioridad = (
        str(prioridad_val if pd.notna(prioridad_val) else "NORMAL").strip().upper()
    )
    descripcion = str(
        descripcion_val if pd.notna(descripcion_val) else ""
    ).strip()
    
    if is_ack and prioridad == "URGENTE":
        estado = "EN PROCESO"
    else:
        estado = str(estado_val if pd.notna(estado_val) else "PENDIENTE").strip().upper()

    priority_colors = {
        "URGENTE": "#EF4444",
        "AUDITORÍA": "#A855F7",
        "AUDITORIA": "#A855F7",
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
        "PENDIEN": {
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

    # BARRA VIVA DE TIEMPO SI ES URGENTE
    bar_html = ""
    if prioridad == "URGENTE":
        start_t = st.session_state.urgent_start_times.get(descripcion, time.time())
        elapsed_min = int((time.time() - start_t) // 60)
        pct_bar = min(100, int((elapsed_min / 15.0) * 100))
        
        if elapsed_min < 5:
            bar_color = "#10B981"
            txt_t = f"⏱️ Hace {elapsed_min} min"
        elif elapsed_min < 10:
            bar_color = "#F59E0B"
            txt_t = f"⏱️ Hace {elapsed_min} min"
        else:
            bar_color = "#EF4444"
            txt_t = f"🚨 {elapsed_min} min sin atender"

        bar_html = f"""
        <div style="margin-top: 4px;">
            <div style="display: flex; justify-content: space-between; align-items: center; font-size: 9.5px; color: {bar_color}; font-weight: 700; margin-bottom: 1px;">
                <span>{txt_t}</span>
                <span>{pct_bar}%</span>
            </div>
            <div style="background-color: #1F2937; border-radius: 3px; height: 4px; width: 100%; overflow: hidden;">
                <div style="background-color: {bar_color}; height: 100%; width: {pct_bar}%;"></div>
            </div>
        </div>
        """

    return f'<div style="background: #111827; border-left: 3px solid {border_color}; border-radius: 5px; padding: 5px 8px; margin-bottom: 3px;"><div style="display: flex; justify-content: space-between; align-items: center; gap: 8px;"><div style="color: #F3F4F6; font-size: 12px; font-weight: 500; line-height: 1.2; flex-grow: 1;">{descripcion}</div><div style="background-color: {s_style["bg"]}; color: {s_style["text"]}; border: 1px solid {s_style["border"]}; font-size: 10px; font-weight: 700; padding: 2px 6px; border-radius: 6px; white-space: nowrap;">{estado}</div></div>{bar_html}</div>'


# ---------------------------------------------------------
# TABLERO DE CONTROL DINÁMICO (REFRESCO CADA 5 SEGUNDOS)
# ---------------------------------------------------------
@st.fragment(run_every=5)
def render_tablero_fluido():
    df_main, df_bitacora, info_estado = cargar_datos_gsheets()

    # DETECCION Y CONTROL DE TIEMPO PARA NOTAS 'URGENTE'
    urgentes_no_enteradas = []
    if df_bitacora is not None and not df_bitacora.empty:
        col_p = next(
            (c for c in df_bitacora.columns if "PRIORI" in str(c).upper() or "PO" in str(c).upper() or "TIPO" in str(c).upper()), None
        )
        col_d = next(
            (c for c in df_bitacora.columns if "DESCRIP" in str(c).upper() or "NOTA" in str(c).upper() or "AVISO" in str(c).upper()), None
        )

        if col_p and col_d:
            for _, row in df_bitacora.iterrows():
                prio_val = str(row[col_p]).strip().upper()
                desc_val = str(row[col_d]).strip()
                if prio_val == "URGENTE" and desc_val:
                    if desc_val not in st.session_state.urgent_start_times:
                        st.session_state.urgent_start_times[desc_val] = time.time()
                    
                    # SI NO SE HA DADO CLICK EN "ENTERADO", SIGUE PENDIENTE DE ALARMA
                    if desc_val not in st.session_state.acknowledged_urgents:
                        urgentes_no_enteradas.append(desc_val)

    # MODIFICACIÓN 2: ALARMA CONTINUA MIENTRAS EXISTAN NOTAS SIN DARSES 'ENTERADO'
    if urgentes_no_enteradas:
        texto_alerta = " / ".join(urgentes_no_enteradas).replace("'", "\\'").replace("\n", " ")
        components.html(
            f"""
            <script>
            (function() {{
                function sonarAlertaLoop() {{
                    try {{
                        var AudioContext = window.AudioContext || window.webkitAudioContext;
                        if (!AudioContext) return;
                        var ctx = new AudioContext();
                        if (ctx.state === 'suspended') {{ ctx.resume(); }}

                        var tiempos = [0, 0.2, 0.4];
                        tiempos.forEach(function(t) {{
                            var osc = ctx.createOscillator();
                            var gain = ctx.createGain();
                            osc.type = 'sawtooth';
                            osc.frequency.setValueAtTime(980, ctx.currentTime + t);
                            gain.gain.setValueAtTime(0.3, ctx.currentTime + t);
                            gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + t + 0.15);
                            osc.connect(gain);
                            gain.connect(ctx.destination);
                            osc.start(ctx.currentTime + t);
                            osc.stop(ctx.currentTime + t + 0.15);
                        }});
                    }} catch(e) {{ console.log(e); }}
                }}
                sonarAlertaLoop();
            }})();
            </script>
            """,
            height=0,
            width=0,
        )

    # UNLOCKER DE AUDIO INVISIBLE GLOBAL
    components.html(
        """
        <script>
        window.top.document.addEventListener('click', function() {
            try {
                var AudioContext = window.AudioContext || window.webkitAudioContext;
                if (AudioContext) {
                    var ctx = new AudioContext();
                    ctx.resume();
                }
            } catch(e) {}
        }, { once: true });
        </script>
        """,
        height=0,
        width=0,
    )

    cols_deseadas = [
        "Fecha",
        "# Orden",
        "Responsables",
        "Cer firmado",
        "Enviado",
        "CRM salida",
        "Aprob. Comercial",
        "CRM cert.",
    ]
    df_vista = pd.DataFrame()
    df_hoy = pd.DataFrame()
    df_anteriores_incompletas = pd.DataFrame()

    total_hoy = 0
    hoy_dt = datetime.now().date()
    fecha_activa_str = hoy_dt.strftime("%d/%m/%Y")

    total_reg = 0
    total_firm = 0
    total_env = 0
    total_pend = 0

    if df_main is not None and not df_main.empty:
        mapa_cols = {}
        cols_raw = list(df_main.columns)

        for idx, col in enumerate(cols_raw):
            c_upper = str(col).upper().strip()
            if "FECHA" in c_upper and "Fecha" not in mapa_cols.values():
                mapa_cols[col] = "Fecha"
            elif (("ORDEN" in c_upper or "ORD" in c_upper) and "# Orden" not in mapa_cols.values()):
                mapa_cols[col] = "# Orden"
            elif (("RESP" in c_upper or "RESPONSABLE" in c_upper or "ENCARGADO" in c_upper) and "Responsables" not in mapa_cols.values()):
                mapa_cols[col] = "Responsables"
            elif ("CER" in c_upper and "FIRM" in c_upper) and "Cer firmado" not in mapa_cols.values():
                mapa_cols[col] = "Cer firmado"
            elif "ENV" in c_upper and "Enviado" not in mapa_cols.values():
                mapa_cols[col] = "Enviado"
            elif ("CRM" in c_upper and "SAL" in c_upper) and "CRM salida" not in mapa_cols.values():
                mapa_cols[col] = "CRM salida"
            elif (("APROB" in c_upper or "COMER" in c_upper) and "Aprob. Comercial" not in mapa_cols.values()):
                mapa_cols[col] = "Aprob. Comercial"
            elif ("CRM" in c_upper and "CERT" in c_upper) and "CRM cert." not in mapa_cols.values():
                mapa_cols[col] = "CRM cert."

        if "Responsables" not in mapa_cols.values() and len(cols_raw) >= 3:
            col_pos2 = cols_raw[2]
            if col_pos2 not in mapa_cols:
                mapa_cols[col_pos2] = "Responsables"

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

            def formatear_fecha_mostrar(row):
                dt = row["Fecha_dt"]
                if pd.notna(dt) and dt is not None:
                    return dt.strftime("%d/%m/%Y")
                raw = str(row["Fecha_Raw"]).strip()
                return raw if raw and raw.lower() != "nan" else ""

            df_vista["Fecha"] = df_vista.apply(formatear_fecha_mostrar, axis=1)

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

            df_hoy = df_vista[df_vista["Fecha_dt"] == hoy_dt].copy()

            # BÚSQUEDA DE INCOMPLETAS ANTERIORES PARA LA PÁGINA 2 RELÁMPAGO
            df_anteriores = df_vista[df_vista["Fecha_dt"] < hoy_dt].copy()
            incompletas_list = []
            for _, r_ant in df_anteriores.iterrows():
                pct_ant, _ = calcular_progreso_orden(r_ant)
                if pct_ant < 100:
                    incompletas_list.append(r_ant)
            if incompletas_list:
                df_anteriores_incompletas = pd.DataFrame(incompletas_list)

            if df_hoy.empty and not df_vista["Fecha_dt"].dropna().empty:
                max_dt = df_vista["Fecha_dt"].dropna().max()
                df_hoy = df_vista[df_vista["Fecha_dt"] == max_dt].copy()
                fecha_activa_str = max_dt.strftime("%d/%m/%Y")
            else:
                fecha_activa_str = hoy_dt.strftime("%d/%m/%Y")

            total_hoy = len(df_hoy)

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
            f'<div class="kpi-card"><div class="kpi-title">REGISTRADAS</div><div class="kpi-value">{total_reg}</div></div>',
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f'<div class="kpi-card"><div class="kpi-title">FIRMADAS ✏️</div><div class="kpi-value">{total_firm}</div></div>',
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            f'<div class="kpi-card"><div class="kpi-title">ENVIADAS 📦</div><div class="kpi-value">{total_env}</div></div>',
            unsafe_allow_html=True,
        )
    with col4:
        st.markdown(
            f'<div class="kpi-card"><div class="kpi-title">PENDIENTES ⌛</div><div class="kpi-value">{total_pend}</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown("<div style='margin-bottom: 2px;'></div>", unsafe_allow_html=True)

    # 2. TABLA PRINCIPAL CON CONTROLES Y BUSCADOR
    if df_vista is not None and not df_vista.empty:
        col_btn1, col_btn2, col_search, col_info = st.columns([0.8, 0.8, 2.0, 2.4])

        with col_btn1:
            if st.button("⬆️ Subir"):
                st.session_state.page_index = max(0, st.session_state.page_index - 1)
                st.session_state.last_switch_time = time.time()
                st.session_state.manual_nav_bonus = 30
                st.rerun()

        with col_btn2:
            if st.button("⬇️ Bajar"):
                st.session_state.page_index += 1
                st.session_state.last_switch_time = time.time()
                st.session_state.manual_nav_bonus = 30
                st.rerun()

        with col_search:
            ahora_search = time.time()
            if st.session_state.get("search_term", ""):
                if ahora_search - st.session_state.get("last_search_time", ahora_search) >= 180:
                    st.session_state.search_term = ""
                    st.session_state.last_search_val = ""
                    if "search_input_widget" in st.session_state:
                        st.session_state.search_input_widget = ""
                    st.rerun()

            search_val = st.text_input(
                "Buscar Orden",
                value=st.session_state.get("search_term", ""),
                placeholder="🔍 Buscar N° Orden...",
                key="search_input_widget",
                label_visibility="collapsed",
            )

            if search_val != st.session_state.get("last_search_val", ""):
                st.session_state.last_search_val = search_val
                st.session_state.last_search_time = time.time()
                st.session_state.search_term = search_val

        if st.session_state.search_term.strip():
            term = st.session_state.search_term.strip().lower()
            col_target = "# Orden" if "# Orden" in df_vista.columns else df_vista.columns[0]
            df_vista = df_vista[
                df_vista[col_target].astype(str).str.lower().str.contains(term, na=False)
            ]

        # CALCULOS DE PAGINACIÓN
        filas_por_pagina = 10
        total_filas = len(df_vista)
        total_paginas = max(1, (total_filas + filas_por_pagina - 1) // filas_por_pagina)

        if st.session_state.page_index >= total_paginas:
            st.session_state.page_index = 0

        p_idx = st.session_state.page_index
        inicio = p_idx * filas_por_pagina
        fin = min(inicio + filas_por_pagina, total_filas)
        df_pagina = df_vista.iloc[inicio:fin]
        cant_items_pagina = len(df_pagina)

        if p_idx == 0:
            duracion_base = 180
        else:
            duracion_base = max(15, int(60 * (cant_items_pagina / filas_por_pagina)))

        duracion_total = duracion_base + st.session_state.get("manual_nav_bonus", 0)

        ahora = time.time()
        tiempo_transcurrido = ahora - st.session_state.last_switch_time

        if tiempo_transcurrido >= duracion_total and total_paginas > 1:
            st.session_state.page_index = (st.session_state.page_index + 1) % total_paginas
            st.session_state.last_switch_time = time.time()
            st.session_state.manual_nav_bonus = 0
            st.rerun()

        with col_info:
            segundos_restantes = max(0, int(duracion_total - tiempo_transcurrido))
            bonus_str = " (+30s manual)" if st.session_state.get("manual_nav_bonus", 0) > 0 else ""
            st.caption(
                f"Pág. {p_idx + 1}/{total_paginas} ({total_filas} reg.)"
                f" | ⏱️ Rotación: {segundos_restantes}s{bonus_str}"
            )

        st.markdown(render_dark_table(df_pagina), unsafe_allow_html=True)

        # MODIFICACIÓN 1: DESPLAZAMIENTO RÁPIDO CON NÚMEROS DE PÁGINA
        if total_paginas > 1:
            btn_cols = st.columns(min(total_paginas, 12))
            for i in range(min(total_paginas, 12)):
                with btn_cols[i]:
                    label = f"• {i+1} •" if i == st.session_state.page_index else f"{i+1}"
                    if st.button(label, key=f"num_page_btn_{i}"):
                        st.session_state.page_index = i
                        st.session_state.last_switch_time = time.time()
                        st.session_state.manual_nav_bonus = 30
                        st.rerun()

    else:
        st.error(f"⚠️ {info_estado}")

    st.markdown(
        "<hr style='border-color: #1F2937; margin: 3px 0;'>",
        unsafe_allow_html=True,
    )

    # 3. SECCIÓN INFERIOR COMPACTA
    c_left, c_middle, c_right = st.columns([1.2, 1.1, 1.2])

    with c_left:
        # MODIFICACIÓN 5: PÁGINA 2 RELÁMPAGO (5s) PARA INCOMPLETAS ANTERIORES
        has_anteriores_inc = not df_anteriores_incompletas.empty
        now_p = time.time()
        dt_p = now_p - st.session_state.prog_day_last_switch

        if has_anteriores_inc:
            if st.session_state.prog_day_page == 0 and dt_p >= 20:  # 20s en Hoy
                st.session_state.prog_day_page = 1
                st.session_state.prog_day_last_switch = now_p
            elif st.session_state.prog_day_page == 1 and dt_p >= 5: # 5s relámpago en Incompletas
                st.session_state.prog_day_page = 0
                st.session_state.prog_day_last_switch = now_p

        if st.session_state.prog_day_page == 1 and has_anteriores_inc:
            df_prog_render = df_anteriores_incompletas
            sub_caption = f"⚠️ **Pág 2/2:** Incompletas Anteriores (Vista 5s)"
        else:
            st.session_state.prog_day_page = 0
            df_prog_render = df_hoy
            sub_caption = f"🗓️ **Pág 1/2:** Hoy ({fecha_activa_str}) | {total_hoy} órdenes"

        st.markdown("<h4 style='margin:0 0 1px 0; font-size:13.5px; color:#F3F4F6;'>🚚 Programados del Día</h4>", unsafe_allow_html=True)
        st.caption(sub_caption)
        
        progresos = []
        if df_prog_render is not None and not df_prog_render.empty:
            for _, r in df_prog_render.iterrows():
                ord_num = limpiar_texto(r.get('# Orden', ''))
                if ord_num:
                    pct, txt_falta = calcular_progreso_orden(r)
                    progresos.append((ord_num, pct, txt_falta))

        if progresos:
            acumulado_general = int(np.mean([p[1] for p in progresos]))
            
            st.markdown(
                f'<div style="background-color: #111827; border: 1px solid #1F2937; border-radius: 5px; padding: 4px 8px; margin-bottom: 4px;">'
                f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2px;">'
                f'<span style="font-size: 10.5px; font-weight: 700; color: #9CA3AF;">PROMEDIO VISTA</span>'
                f'<span style="font-size: 12.5px; font-weight: 800; color: #38BDF8;">{acumulado_general}%</span>'
                f'</div>'
                f'<div style="background-color: #1F2937; border-radius: 4px; height: 6px; width: 100%; overflow: hidden;">'
                f'<div style="background: linear-gradient(90deg, #3B82F6, #10B981); height: 100%; width: {acumulado_general}%;"></div>'
                f'</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

            # MODIFICACIÓN 4: DESPLEGADO COMPLETO Y DETALLE DE PASO FALTANTE
            html_progresos = '<div style="display: flex; flex-direction: column; gap: 3px;">'
            for ord_num, pct, txt_falta in progresos:
                bar_color = "#10B981" if pct == 100 else ("#3B82F6" if pct >= 50 else "#F59E0B")
                html_progresos += (
                    f'<div class="progress-order-card">'
                    f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2px;">'
                    f'<span style="font-size: 11.5px; font-weight: 700; color: #F3F4F6;">📦 Orden #{ord_num}</span>'
                    f'<span style="font-size: 11px; font-weight: 800; color: {bar_color};">{pct}%</span>'
                    f'</div>'
                    f'<div style="background-color: #1F2937; border-radius: 3px; height: 5px; width: 100%; overflow: hidden; margin-bottom: 2px;">'
                    f'<div style="background-color: {bar_color}; height: 100%; width: {pct}%;"></div>'
                    f'</div>'
                    f'<div style="font-size: 9.5px; color: #9CA3AF; font-weight: 600;">{txt_falta}</div>'
                    f'</div>'
                )
            html_progresos += '</div>'
            st.markdown(html_progresos, unsafe_allow_html=True)
        else:
            st.info("Sin órdenes en esta vista.")

    with c_middle:
        st.markdown("<h4 style='margin:0 0 1px 0; font-size:13.5px; color:#F3F4F6;'>📋 Asignaciones del Día</h4>", unsafe_allow_html=True)
        st.caption("Tareas y responsabilidades diarias")
        
        st.markdown(
            '<div style="background-color: #111827; border: 1px dashed #374151; border-radius: 5px; padding: 12px 10px; text-align: center; color: #9CA3AF; margin-top: 2px;">'
            '<div style="font-size: 18px; margin-bottom: 2px;">📋</div>'
            '<div style="font-size: 12px; font-weight: 600; color: #D1D5DB;">Sin asignaciones pendientes</div>'
            '<div style="font-size: 10.5px; margin-top: 1px; color: #6B7280;">Espacio listo para próxima integración</div>'
            '</div>',
            unsafe_allow_html=True,
        )

    with c_right:
        st.markdown("<h4 style='margin:0 0 1px 0; font-size:13.5px; color:#F3F4F6;'>📌 Bitácora / Avisos del Día</h4>", unsafe_allow_html=True)
        st.caption("Notas registradas en tiempo real")
        
        if df_bitacora is None or df_bitacora.empty:
            st.info("Sin avisos en 'NOTAS DEL DIA'.")
        else:
            col_p = next((c for c in df_bitacora.columns if "PRIORI" in str(c).upper() or "PO" in str(c).upper() or "TIPO" in str(c).upper()), None)
            col_d = next((c for c in df_bitacora.columns if "DESCRIP" in str(c).upper() or "NOTA" in str(c).upper() or "AVISO" in str(c).upper()), None)
            col_e = next((c for c in df_bitacora.columns if "ESTADO" in str(c).upper()), None)

            if col_p and col_p in df_bitacora.columns:
                prio_map = {
                    "URGENTE": 1,
                    "AUDITORÍA": 2,
                    "AUDITORIA": 2,
                    "REVISIÓN": 3,
                    "REVISION": 3,
                    "AVISO": 4,
                    "MANTENIMIENTO": 5,
                    "NORMAL": 6,
                }
                df_bitacora["_prio_sort"] = df_bitacora[col_p].apply(
                    lambda x: prio_map.get(str(x).strip().upper(), 99)
                )
                df_bitacora = df_bitacora.sort_values(by="_prio_sort").drop(columns=["_prio_sort"])

            # RENDERIZADO CON BOTÓN 'ENTERADO' Y BARRAS VIVAS DE TIEMPO
            for idx_b, r in df_bitacora.iterrows():
                p_val = r[col_p] if col_p else "NORMAL"
                d_val = str(r[col_d] if col_d else "").strip()
                e_val = r[col_e] if col_e else "PENDIENTE"
                
                is_ack = d_val in st.session_state.acknowledged_urgents
                
                st.markdown(render_bitacora_card(p_val, d_val, e_val, is_ack=is_ack), unsafe_allow_html=True)
                
                # MODIFICACIÓN 2: BOTÓN ENTERADO SILENCIADOR
                if str(p_val).strip().upper() == "URGENTE" and not is_ack:
                    if st.button("✅ Enterado", key=f"btn_ack_{idx_b}"):
                        st.session_state.acknowledged_urgents.add(d_val)
                        st.rerun()


render_tablero_fluido()
