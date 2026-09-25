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
# LISTA DE INVOLUCRADOS (EMISORES Y RECEPTORES)
# ---------------------------------------------------------
LISTA_EMISORES = [
    "Jeison Altamar",
    "Nicolas Arevalo",
    "Jhojan Pasachoa",
    "Sonia Gonzales"
]

LISTA_RECEPTORES = [
    "Todos",
    "Jeison Altamar",
    "Nicolas Arevalo",
    "Jhojan Pasachoa",
    "Sonia Gonzales"
]

# ---------------------------------------------------------
# CONFIGURACIÓN DE PÁGINA
# ---------------------------------------------------------
st.set_page_config(
    page_title="Tablero de Control - Laboratorio", page_icon="📊", layout="wide"
)

# ---------------------------------------------------------
# ESTADO GLOBAL COMPARTIDO (Servidor / Entre Usuarios)
# ---------------------------------------------------------
@st.cache_resource
def obtener_estado_global():
    return {
        "mensajes_bitacora": [],       # Historial estructurado de chat de bitácora
        "cargado_gsheet": False,       # Bandera de lectura inicial desde Google Sheets
    }

ESTADO_GLOBAL = obtener_estado_global()

# ESTADOS DE SESIÓN LOCALES
if "page_index" not in st.session_state:
    st.session_state.page_index = 0
if "last_switch_time" not in st.session_state:
    st.session_state.last_switch_time = time.time()
if "search_input" not in st.session_state:
    st.session_state.search_input = ""
if "manual_nav_bonus" not in st.session_state:
    st.session_state.manual_nav_bonus = 0
if "sound_enabled" not in st.session_state:
    st.session_state.sound_enabled = True
if "notif_enabled" not in st.session_state:
    st.session_state.notif_enabled = True
if "session_start_time" not in st.session_state:
    st.session_state.session_start_time = time.time()

if "prog_day_page" not in st.session_state:
    st.session_state.prog_day_page = 0
if "prog_day_last_switch" not in st.session_state:
    st.session_state.prog_day_last_switch = time.time()
if "alert_filter" not in st.session_state:
    st.session_state.alert_filter = "TODAS"


# ---------------------------------------------------------
# ESTILOS MODO OSCURO + COMPACTACIÓN UI SIN PERDER LA GRACIA
# ---------------------------------------------------------
st.markdown(
    """
<style>
    /* OCULTAR ENCABEZADOS Y AJUSTAR CONTENEDOR PRINCIPAL */
    header, [data-testid="stHeader"] { display: none !important; }
    .block-container { 
        padding-top: 0.3rem !important; 
        padding-bottom: 0.2rem !important; 
        padding-left: 0.8rem !important;
        padding-right: 0.8rem !important;
    }

    .stApp { background-color: #0B1120; color: #F3F4F6; font-size: 13.5px; }

    /* FIX DE VISIBILIDAD EN INPUTS, TEXTAREAS Y SELECTBOXES */
    input, textarea, select {
        color: #FFFFFF !important;
        background-color: #1F2937 !important;
    }
    .stTextInput input, .stTextArea textarea {
        color: #FFFFFF !important;
        background-color: #1F2937 !important;
        border: 1px solid #374151 !important;
        border-radius: 6px !important;
        padding: 4px 8px !important;
    }
    div[data-baseweb="select"] > div {
        background-color: #1F2937 !important;
        color: #FFFFFF !important;
        border: 1px solid #374151 !important;
        min-height: 32px !important;
    }
    div[data-baseweb="popover"] *, div[role="listbox"] * {
        background-color: #111827 !important;
        color: #FFFFFF !important;
    }

    /* BANNER SUPERIOR DE ALERTA CRÍTICA */
    @keyframes pulse-banner {
        0% { box-shadow: 0 0 10px rgba(239, 68, 68, 0.5); }
        50% { box-shadow: 0 0 25px rgba(239, 68, 68, 0.95); }
        100% { box-shadow: 0 0 10px rgba(239, 68, 68, 0.5); }
    }
    .top-urgent-banner {
        background: linear-gradient(90deg, #DC2626 0%, #991B1B 100%);
        color: #FFFFFF;
        padding: 5px 12px;
        border-radius: 6px;
        margin-bottom: 6px;
        font-weight: 800;
        text-align: center;
        font-size: 13px;
        letter-spacing: 0.5px;
        border: 1px solid #EF4444;
        animation: pulse-banner 1.5s infinite;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    /* TARJETAS KPI */
    .kpi-card {
        background-color: #111827;
        border: 1px solid #1F2937;
        border-radius: 6px;
        padding: 4px 8px;
        text-align: center;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.4);
    }
    .kpi-title {
        color: #9CA3AF;
        font-size: 10.5px;
        font-weight: 700;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        margin-bottom: 1px;
    }
    .kpi-value { color: #FFFFFF; font-size: 20px; font-weight: 800; line-height: 1.1; }

    /* TARJETAS DE PROGRESO DE ETAPA */
    .progress-order-card {
        background-color: #111827;
        border: 1px solid #1F2937;
        border-radius: 4px;
        padding: 3px 6px;
        margin-bottom: 2px;
    }

    /* CONTROLES Y BOTONES GENERALES ESTÁNDAR */
    div.stButton > button {
        background-color: #1E293B !important;
        color: #38BDF8 !important;
        border: 1px solid #3B82F6 !important;
        border-radius: 5px !important;
        font-weight: 700 !important;
        font-size: 11px !important;
        padding: 1px 5px !important;
        width: 100% !important;
        height: 28px !important;
        transition: all 0.2s ease-in-out !important;
    }
    div.stButton > button:hover {
        background-color: #2563EB !important;
        color: #FFFFFF !important;
        border-color: #60A5FA !important;
        cursor: pointer !important;
        box-shadow: 0 0 8px rgba(59, 130, 246, 0.5) !important;
    }

    /* BOTONES ESTILO INTERRUPTOR / PILL TOGGLES */
    .pill-toggle-blue div.stButton > button {
        background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%) !important;
        color: #FFFFFF !important;
        border: 1px solid #60A5FA !important;
        border-radius: 30px !important;
        font-size: 10.5px !important;
        font-weight: 800 !important;
        padding: 1px 8px !important;
        height: 26px !important;
        box-shadow: 0 2px 8px rgba(37, 99, 235, 0.4) !important;
    }
    .pill-toggle-blue div.stButton > button:hover {
        background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%) !important;
        box-shadow: 0 0 12px rgba(59, 130, 246, 0.7) !important;
    }

    .pill-toggle-green div.stButton > button {
        background: linear-gradient(135deg, #10B981 0%, #059669 100%) !important;
        color: #FFFFFF !important;
        border: 1px solid #34D399 !important;
        border-radius: 30px !important;
        font-size: 10.5px !important;
        font-weight: 800 !important;
        padding: 1px 8px !important;
        height: 26px !important;
        box-shadow: 0 2px 8px rgba(16, 185, 129, 0.4) !important;
    }
    .pill-toggle-green div.stButton > button:hover {
        background: linear-gradient(135deg, #34D399 0%, #10B981 100%) !important;
        box-shadow: 0 0 12px rgba(52, 211, 153, 0.7) !important;
    }

    .pill-toggle-red div.stButton > button {
        background: linear-gradient(135deg, #EF4444 0%, #DC2626 100%) !important;
        color: #FFFFFF !important;
        border: 1px solid #F87171 !important;
        border-radius: 30px !important;
        font-size: 10.5px !important;
        font-weight: 800 !important;
        padding: 1px 8px !important;
        height: 26px !important;
        box-shadow: 0 2px 8px rgba(239, 68, 68, 0.4) !important;
    }
    .pill-toggle-red div.stButton > button:hover {
        background: linear-gradient(135deg, #F87171 0%, #EF4444 100%) !important;
        box-shadow: 0 0 12px rgba(248, 113, 113, 0.7) !important;
    }

    /* SELECTOR SEGMENTADO MODO OSCURO (RADIO BUTTONS) */
    div[data-testid="stRadio"] > div {
        display: flex;
        flex-direction: row;
        background-color: #111827;
        border: 1px solid #374151;
        border-radius: 6px;
        padding: 2px;
        gap: 3px;
    }
    div[data-testid="stRadio"] label {
        flex: 1;
        text-align: center;
        background-color: #1F2937;
        border-radius: 4px;
        padding: 2px 4px !important;
        font-size: 10.5px !important;
        font-weight: 700 !important;
        color: #D1D5DB !important;
        cursor: pointer;
        transition: all 0.2s ease;
    }

    /* ESTILOS DE MÓDULO CHAT / BITÁCORA REDUCIDO */
    .chat-container {
        max-height: 480px;
        overflow-y: auto;
        padding-right: 3px;
        display: flex;
        flex-direction: column;
        gap: 4px;
    }

    .msg-card-normal {
        background: #111827;
        border-left: 3px solid #10B981;
        border-radius: 5px;
        padding: 5px 8px;
        border-top: 1px solid #1F2937;
        border-right: 1px solid #1F2937;
        border-bottom: 1px solid #1F2937;
    }

    .msg-card-auditoria {
        background: #161D2F;
        border-left: 3px solid #F59E0B;
        border: 1px solid #F59E0B;
        border-radius: 5px;
        padding: 5px 8px;
        box-shadow: 0 0 6px rgba(245, 158, 11, 0.15);
    }

    /* ESTADOS URGENCIA 4 MINUTOS */
    .msg-card-urgente-verde {
        background: linear-gradient(180deg, #064E3B 0%, #111827 100%);
        border: 1.5px solid #10B981;
        border-radius: 5px;
        padding: 5px 8px;
    }

    .msg-card-urgente-naranja {
        background: linear-gradient(180deg, #78350F 0%, #111827 100%);
        border: 1.5px solid #F59E0B;
        border-radius: 5px;
        padding: 5px 8px;
    }

    @keyframes pulse-urgente {
        0% { border-color: #EF4444; box-shadow: 0 0 4px rgba(239, 68, 68, 0.4); }
        50% { border-color: #FCA5A5; box-shadow: 0 0 12px rgba(239, 68, 68, 0.8); }
        100% { border-color: #EF4444; box-shadow: 0 0 4px rgba(239, 68, 68, 0.4); }
    }

    .msg-card-urgente-rojo {
        background: linear-gradient(180deg, #450A0A 0%, #111827 100%);
        border: 1.5px solid #EF4444;
        animation: pulse-urgente 1.2s infinite;
        border-radius: 5px;
        padding: 5px 8px;
    }

    .msg-card-atendido {
        background: #0D1520;
        border-left: 3px solid #10B981;
        border: 1px solid #1F2937;
        border-radius: 5px;
        padding: 5px 8px;
        opacity: 0.9;
    }

    .badge-prio-normal {
        background-color: rgba(16, 185, 129, 0.2);
        color: #A7F3D0;
        border: 1px solid #10B981;
        font-size: 9px;
        font-weight: 700;
        padding: 0px 4px;
        border-radius: 3px;
    }

    .badge-prio-auditoria {
        background-color: rgba(245, 158, 11, 0.25);
        color: #FDE68A;
        border: 1px solid #F59E0B;
        font-size: 9px;
        font-weight: 800;
        padding: 0px 4px;
        border-radius: 3px;
    }

    /* ESTILO DE RESPUESTAS */
    .reply-box {
        background: #1F2937;
        border-left: 2px solid #3B82F6;
        border-radius: 3px;
        padding: 3px 6px;
        margin-top: 3px;
        font-size: 11px;
    }

    /* ANIMACIÓN PARPADEO TABLA CORRECCIÓN */
    @keyframes pulse-correccion {
        0% { background-color: rgba(239, 68, 68, 0.12); }
        50% { background-color: rgba(239, 68, 68, 0.30); }
        100% { background-color: rgba(239, 68, 68, 0.12); }
    }
    .row-correccion {
        animation: pulse-correccion 2.2s infinite !important;
        border-left: 4px solid #EF4444 !important;
    }

    /* SCROLLBARS */
    ::-webkit-scrollbar { width: 5px; height: 5px; }
    ::-webkit-scrollbar-track { background: #111827; border-radius: 4px; }
    ::-webkit-scrollbar-thumb { background: #374151; border-radius: 4px; }
    ::-webkit-scrollbar-thumb:hover { background: #3B82F6; }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""",
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# SISTEMA DE NOTIFICACIONES DE ESCRITORIO PROFESIONAL
# ---------------------------------------------------------
def solicitar_permisos_notificaciones_js():
    components.html(
        """
        <script>
        (function() {
            var parentWin = window.parent || window;
            var navNotif = parentWin.Notification || window.Notification;
            if (navNotif) {
                navNotif.requestPermission().then(function(perm) {
                    if (perm === "granted") {
                        alert("✅ Notificaciones del sistema y sonido activados correctamente.");
                    } else {
                        alert("⚠️ Debes permitir las notificaciones en el navegador para recibir las alertas flotantes.");
                    }
                });
            }
            try {
                var AudioCtx = parentWin.AudioContext || parentWin.webkitAudioContext;
                if (AudioCtx) {
                    var ctx = new AudioCtx();
                    if (ctx.state === 'suspended') ctx.resume();
                }
            } catch(e) {}
        })();
        </script>
        """,
        height=0,
        width=0,
    )


def emitir_notificacion_y_audio_js(msg_id, emisor, receptor, prioridad, contenido, sound_enabled, notif_enabled=True):
    if not notif_enabled:
        return

    contenido_esc = contenido.replace('"', '\\"').replace('\n', ' ')
    emisor_esc = emisor.replace('"', '\\"')
    receptor_esc = receptor.replace('"', '\\"')

    components.html(
        f"""
        <script>
        (function() {{
            var parentWin = window.parent || window;
            var navNotif = parentWin.Notification || window.Notification;

            if (!parentWin._processedMsgs) {{
                parentWin._processedMsgs = {{}};
            }}

            var msgId = "{msg_id}";
            var prioridad = "{prioridad}";
            var emisor = "{emisor_esc}";
            var receptor = "{receptor_esc}";
            var contenido = "{contenido_esc}";
            var soundEnabled = {str(sound_enabled).lower()};

            if (msgId && !parentWin._processedMsgs[msgId]) {{
                parentWin._processedMsgs[msgId] = true;

                // 1. NOTIFICACIÓN COMPACTA EN UNA LÍNEA (EVITA DESBORDAMIENTO DE NOMBRES)
                if (navNotif && navNotif.permission === "granted") {{
                    var titulo = (prioridad === 'Urgente') ? "🚨 ALERTA DE LABORATORIO" : "💬 BITÁCORA DE CONTROL";
                    var cuerpo = emisor + " ➔ " + receptor + "\\n📝 " + contenido;
                    var icono = (prioridad === 'Urgente') 
                        ? "https://cdn-icons-png.flaticon.com/512/1827/1827504.png"
                        : "https://cdn-icons-png.flaticon.com/512/3718/3718167.png";

                    try {{
                        var notif = new navNotif(titulo, {{
                            body: cuerpo,
                            icon: icono,
                            tag: msgId,
                            renotify: true,
                            requireInteraction: (prioridad === 'Urgente')
                        }});
                    }} catch(e) {{ console.error("Error en notificación:", e); }}
                }}

                // 2. AUDIO DE ALERTA URGENTE
                if (prioridad === "Urgente" && soundEnabled) {{
                    try {{
                        var AudioCtx = parentWin.AudioContext || parentWin.webkitAudioContext;
                        if (AudioCtx) {{
                            var ctx = new AudioCtx();
                            if (ctx.state === 'suspended') {{
                                ctx.resume();
                            }}
                            var now = ctx.currentTime;
                            var freqs = [880, 1200, 880, 1200, 1500];
                            freqs.forEach(function(freq, i) {{
                                var t = now + (i * 0.14);
                                var osc = ctx.createOscillator();
                                var gain = ctx.createGain();
                                osc.type = 'sawtooth';
                                osc.frequency.setValueAtTime(freq, t);
                                gain.gain.setValueAtTime(0.5, t);
                                gain.gain.exponentialRampToValueAtTime(0.001, t + 0.12);
                                osc.connect(gain);
                                gain.connect(ctx.destination);
                                osc.start(t);
                                osc.stop(t + 0.13);
                            }});
                        }}
                    }} catch(e) {{ console.error("Error al reproducir audio:", e); }}
                }}
            }}
        }})();
        </script>
        """,
        height=0,
        width=0,
    )


# ---------------------------------------------------------
# FUNCIONES AUXILIARES Y PARSER
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
    if not val_str or val_str.lower() in ["nan", "none", "nat", "null"] or val_str.startswith("#"):
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


def calcular_progreso_orden(row):
    progreso = 25
    cer = str(row.get("Cer firmado", row.get("CER FIRMADO", ""))).strip().upper()
    env = str(row.get("Enviado", row.get("ENVIADO", ""))).strip().upper()

    faltantes = []
    if cer in ["SI", "SÍ"]:
        progreso += 25
    else:
        faltantes.append("CER Firmado")

    if env in ["SI", "SÍ"]:
        progreso += 25
    else:
        faltantes.append("Enviado")

    crm_sal = str(row.get("CRM salida", row.get("CRM SALIDA", ""))).strip().upper()
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
                df_proceso.columns = [str(c).strip() for c in df_proceso_raw.iloc[header_idx].values]
            else:
                df_proceso = df_proceso_raw.iloc[1:].copy()
                df_proceso.columns = [str(c).strip() for c in df_proceso_raw.iloc[0].values]

        df_notas = pd.DataFrame()
        if df_notas_raw is not None and not df_notas_raw.empty:
            header_n_idx = None
            for idx, row in df_notas_raw.iterrows():
                row_str = " ".join(row.dropna().astype(str)).upper()
                if any(k in row_str for k in ["DESCRIPCIÓN", "DESCRIPCION", "PRIORIDA", "TIPO", "NOTA"]):
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
        return "<div style='color: #9CA3AF; text-align: center; padding: 8px; font-size: 12px;'>Sin datos o registros coincidentes.</div>"

    headers = list(df_page.columns)

    col_resp = next((c for c in headers if "RESP" in c.upper()), None)
    col_cer = next((c for c in headers if "CER" in c.upper() and "FIRM" in c.upper()), None)
    col_env = next((c for c in headers if "ENV" in c.upper()), None)
    col_crm_salida = next((c for c in headers if "CRM" in c.upper() and "SALIDA" in c.upper()), None)
    col_orden = next((c for c in headers if "ORDEN" in c.upper()), None)

    html = '<div style="overflow-x: auto; border: 1px solid #1F2937; border-radius: 6px; background-color: #111827; margin-bottom: 4px;"><table style="width: 100%; border-collapse: collapse; color: #F3F4F6; font-size: 12px; text-align: left;"><thead><tr style="background-color: #1F2937; color: #9CA3AF; font-weight: 700; text-transform: uppercase; font-size: 10.5px; letter-spacing: 0.5px;">'

    for h in headers:
        if h == col_resp:
            html += f'<th style="padding: 4px 4px; border-bottom: 1px solid #374151; width: 75px; text-align: center; white-space: nowrap;">{h}</th>'
        else:
            html += f'<th style="padding: 4px 6px; border-bottom: 1px solid #374151;">{h}</th>'
    html += "</tr></thead><tbody>"

    for idx, row in df_page.iterrows():
        cer_val = str(row[col_cer]).strip().upper() if col_cer and pd.notna(row[col_cer]) else ""
        crm_sal_val = str(row[col_crm_salida]).strip().upper() if col_crm_salida and pd.notna(row[col_crm_salida]) else ""

        es_correccion = "CORREC" in cer_val
        cer_es_si = cer_val in ["SI", "SÍ"]
        crm_vacio = crm_sal_val not in ["SI", "SÍ"]
        es_atascada = cer_es_si and crm_vacio

        if es_correccion:
            tr_style = 'style="border-bottom: 1px solid #EF4444;" class="row-correccion"'
        elif es_atascada:
            tr_style = 'style="border-bottom: 1px solid #F59E0B; background-color: rgba(245, 158, 11, 0.08); border-left: 3px solid #F59E0B;"'
        else:
            tr_style = 'style="border-bottom: 1px solid #1F2937;"'

        html += f"<tr {tr_style}>"
        for h in headers:
            val = limpiar_texto(row[h])
            val_upper = val.upper()

            td_style = "padding: 3px 6px;"

            if h == col_resp:
                td_style = "padding: 3px 4px; text-align: center; width: 75px; white-space: nowrap;"
                badge = f'<span style="color: #38BDF8; font-weight: 700; font-size: 11px;">{val}</span>'
            elif h == col_orden and es_atascada:
                badge = f'{val} <span style="background-color: rgba(245, 158, 11, 0.25); color: #FBBF24; border: 1px solid #F59E0B; padding: 0px 4px; border-radius: 3px; font-weight: 700; font-size: 9.5px;" title="Atascada">⚠️</span>'
            elif val_upper in ["SI", "SÍ"]:
                badge = '<span style="background-color: rgba(16, 185, 129, 0.2); color: #A7F3D0; border: 1px solid #10B981; padding: 0px 5px; border-radius: 3px; font-weight: 700; font-size: 10px;">Si</span>'
            elif val != "":
                if any(k in val_upper for k in ["CORREC", "ERROR", "RECHAZ", "CANCEL"]):
                    badge = f'<span style="background-color: rgba(239, 68, 68, 0.25); color: #FCA5A5; border: 1px solid #EF4444; padding: 0px 5px; border-radius: 3px; font-weight: 700; font-size: 10px;">{val} ⚠️</span>'
                elif h in [col_env, col_crm_salida, col_cer] or any(k in val_upper for k in ["APROBAC", "PENDIENTE", "P.", "FIRMAR", "REVISAR"]):
                    badge = f'<span style="background-color: rgba(245, 158, 11, 0.2); color: #FDE68A; border: 1px solid #F59E0B; padding: 0px 5px; border-radius: 3px; font-weight: 600; font-size: 10px;">{val}</span>'
                else:
                    badge = val
            else:
                badge = ""

            html += f'<td style="{td_style}">{badge}</td>'
        html += "</tr>"

    html += "</tbody></table></div>"
    return html


# ---------------------------------------------------------
# RENDERIZADO DE NOVEDADES (COMPACTO Y COMPLETO)
# ---------------------------------------------------------
def render_chat_message_html(msg, cycle_sec=0, cycle_num=0):
    emisor = msg.get("emisor", "Jeison Altamar")
    receptor = msg.get("receptor", "Todos")
    prioridad = msg.get("prioridad", "Normal")
    contenido = msg.get("contenido", "")
    fecha_hora = msg.get("fecha_hora", "")
    estado = msg.get("estado", "Pendiente")
    usuario_enterado = msg.get("usuario_enterado", None)
    fecha_enterado = msg.get("fecha_enterado", None)
    respuestas = msg.get("respuestas", [])

    # RESPUESTAS HILADAS
    respuestas_html = ""
    if respuestas:
        respuestas_html += "<div style='margin-top: 3px; display: flex; flex-direction: column; gap: 2px;'>"
        for r in respuestas:
            respuestas_html += f'''
            <div class="reply-box">
                <div style="display: flex; justify-content: space-between; font-size: 9px; color: #9CA3AF; margin-bottom: 1px;">
                    <strong style="color: #60A5FA;">💬 {r.get("usuario")}</strong>
                    <span>{r.get("fecha_hora")}</span>
                </div>
                <div style="color: #E5E7EB; font-size: 11px; line-height: 1.2;">{r.get("texto")}</div>
            </div>
            '''
        respuestas_html += "</div>"

    if prioridad == "Urgente":
        if estado == "Pendiente":
            min_exp = int(cycle_sec // 60)
            sec_exp = int(cycle_sec % 60)
            c_num_str = f" | C#{cycle_num + 1}" if cycle_num > 0 else ""

            if cycle_sec < 120:
                card_class = "msg-card-urgente-verde"
                prio_badge = f'<span style="background: rgba(16, 185, 129, 0.25); color: #A7F3D0; border: 1px solid #10B981; font-size: 9px; font-weight: 800; padding: 1px 4px; border-radius: 3px;">🟢 URGENTE ({min_exp}m {sec_exp:02d}s{c_num_str})</span>'
            elif cycle_sec < 180:
                card_class = "msg-card-urgente-naranja"
                prio_badge = f'<span style="background: rgba(245, 158, 11, 0.25); color: #FDE68A; border: 1px solid #F59E0B; font-size: 9px; font-weight: 800; padding: 1px 4px; border-radius: 3px;">🟡 ADVERTENCIA ({min_exp}m {sec_exp:02d}s{c_num_str})</span>'
            else:
                card_class = "msg-card-urgente-rojo"
                prio_badge = f'<span style="background: rgba(239, 68, 68, 0.35); color: #FCA5A5; border: 1px solid #EF4444; font-size: 9px; font-weight: 800; padding: 1px 4px; border-radius: 3px;">🔴 CRÍTICO ({min_exp}m {sec_exp:02d}s{c_num_str})</span>'

            return f'''
            <div class="{card_class}">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2px;">
                    {prio_badge}
                    <span style="font-size: 9.5px; color: #F3F4F6; font-weight: 700;">⏱️ {fecha_hora}</span>
                </div>
                <div style="font-size: 10.5px; color: #9CA3AF; margin-bottom: 2px;">
                    <strong style="color: #F3F4F6;">{emisor}</strong> ➔ <strong style="color: #F3F4F6;">{receptor}</strong>
                </div>
                <div style="color: #FFFFFF; font-size: 11.5px; font-weight: 700; line-height: 1.25; margin-bottom: 2px;">
                    🚨 {contenido}
                </div>
                {respuestas_html}
            </div>
            '''
        else:
            return f'''
            <div class="msg-card-atendido">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2px;">
                    <span style="background: rgba(16, 185, 129, 0.2); color: #A7F3D0; border: 1px solid #10B981; font-size: 9px; font-weight: 800; padding: 1px 4px; border-radius: 3px;">
                        ✓ REALIZADO
                    </span>
                    <span style="font-size: 9.5px; color: #9CA3AF;">{fecha_hora}</span>
                </div>
                <div style="font-size: 10.5px; color: #9CA3AF; margin-bottom: 2px;">
                    <strong style="color: #D1D5DB;">{emisor}</strong> ➔ <strong style="color: #D1D5DB;">{receptor}</strong>
                </div>
                <div style="color: #E5E7EB; font-size: 11.5px; font-weight: 500; line-height: 1.2;">
                    {contenido}
                </div>
                <div style="font-size: 9px; color: #34D399; margin-top: 2px; font-weight: 600;">
                    ✅ Realizado por: <strong>{usuario_enterado}</strong> ({fecha_enterado})
                </div>
                {respuestas_html}
            </div>
            '''

    elif prioridad == "Auditoría":
        if estado == "Atendido":
            return f'''
            <div class="msg-card-atendido">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2px;">
                    <span style="background: rgba(16, 185, 129, 0.2); color: #A7F3D0; border: 1px solid #10B981; font-size: 9px; font-weight: 800; padding: 1px 4px; border-radius: 3px;">
                        ✓ AUDITADO
                    </span>
                    <span style="font-size: 9.5px; color: #9CA3AF;">{fecha_hora}</span>
                </div>
                <div style="font-size: 10.5px; color: #9CA3AF; margin-bottom: 2px;">
                    <strong style="color: #D1D5DB;">{emisor}</strong> ➔ <strong style="color: #D1D5DB;">{receptor}</strong>
                </div>
                <div style="color: #E5E7EB; font-size: 11.5px; font-weight: 500; line-height: 1.2;">
                    {contenido}
                </div>
                <div style="font-size: 9px; color: #34D399; margin-top: 2px; font-weight: 600;">
                    ✅ Auditado por: <strong>{usuario_enterado}</strong> ({fecha_enterado})
                </div>
                {respuestas_html}
            </div>
            '''
        else:
            return f'''
            <div class="msg-card-auditoria">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2px;">
                    <span class="badge-prio-auditoria">AUDITORÍA</span>
                    <span style="font-size: 9.5px; color: #9CA3AF;">{fecha_hora}</span>
                </div>
                <div style="font-size: 10.5px; color: #9CA3AF; margin-bottom: 2px;">
                    <strong style="color: #D1D5DB;">{emisor}</strong> ➔ <strong style="color: #D1D5DB;">{receptor}</strong>
                </div>
                <div style="color: #E5E7EB; font-size: 11.5px; font-weight: 500; line-height: 1.2;">
                    {contenido}
                </div>
                {respuestas_html}
            </div>
            '''

    else:  # Normal
        if estado == "Atendido":
            return f'''
            <div class="msg-card-atendido">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2px;">
                    <span style="background: rgba(16, 185, 129, 0.2); color: #A7F3D0; border: 1px solid #10B981; font-size: 9px; font-weight: 800; padding: 1px 4px; border-radius: 3px;">
                        ✓ REALIZADO
                    </span>
                    <span style="font-size: 9.5px; color: #9CA3AF;">{fecha_hora}</span>
                </div>
                <div style="font-size: 10.5px; color: #9CA3AF; margin-bottom: 2px;">
                    <strong style="color: #D1D5DB;">{emisor}</strong> ➔ <strong style="color: #D1D5DB;">{receptor}</strong>
                </div>
                <div style="color: #E5E7EB; font-size: 11.5px; font-weight: 500; line-height: 1.2;">
                    {contenido}
                </div>
                <div style="font-size: 9px; color: #34D399; margin-top: 2px; font-weight: 600;">
                    ✅ Realizado por: <strong>{usuario_enterado}</strong> ({fecha_enterado})
                </div>
                {respuestas_html}
            </div>
            '''
        else:
            return f'''
            <div class="msg-card-normal">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2px;">
                    <span class="badge-prio-normal">NORMAL</span>
                    <span style="font-size: 9.5px; color: #9CA3AF;">{fecha_hora}</span>
                </div>
                <div style="font-size: 10.5px; color: #9CA3AF; margin-bottom: 2px;">
                    <strong style="color: #D1D5DB;">{emisor}</strong> ➔ <strong style="color: #D1D5DB;">{receptor}</strong>
                </div>
                <div style="color: #E5E7EB; font-size: 11.5px; font-weight: 500; line-height: 1.2;">
                    {contenido}
                </div>
                {respuestas_html}
            </div>
            '''


# ---------------------------------------------------------
# INTERFAZ PRINCIPAL
# ---------------------------------------------------------
df_proceso, df_notas, status_msg = cargar_datos_gsheets()

# ENCABEZADO CON TOGGLES SOLICITADOS
col_head1, col_head2, col_head3 = st.columns([0.6, 0.2, 0.2])

with col_head1:
    st.markdown("<h3 style='margin: 0; color: #F3F4F6;'>📌 Bitácora / Chat de Laboratorio</h3>", unsafe_allow_html=True)

with col_head2:
    st.session_state.notif_enabled = st.toggle("🔔 Notificaciones", value=st.session_state.notif_enabled)

with col_head3:
    st.session_state.sound_enabled = st.toggle("🔊 Sonido", value=st.session_state.sound_enabled)

st.divider()

# LAYOUT DUAL
col_left, col_right = st.columns([1.1, 0.9])

with col_left:
    st.markdown("##### 📊 Control de Órdenes")

    if df_proceso is not None and not df_proceso.empty:
        st.session_state.search_input = st.text_input(
            "🔎 Buscar por Orden, Responsable o Estado:", value=st.session_state.search_input, key="input_search_main"
        )

        df_filtered = df_proceso.copy()
        if st.session_state.search_input:
            term = st.session_state.search_input.upper()
            df_filtered = df_filtered[
                df_filtered.apply(lambda row: term in " ".join(row.astype(str)).upper(), axis=1)
            ]

        items_per_page = 10
        total_pages = max(1, int(np.ceil(len(df_filtered) / items_per_page)))
        
        col_p1, col_p2 = st.columns([0.5, 0.5])
        with col_p1:
            st.caption(f"Página {st.session_state.page_index + 1} de {total_pages} ({len(df_filtered)} reg.)")
        with col_p2:
            if total_pages > 1:
                page_sel = st.selectbox("Página:", list(range(1, total_pages + 1)), index=st.session_state.page_index)
                st.session_state.page_index = page_sel - 1

        start_idx = st.session_state.page_index * items_per_page
        df_page = df_filtered.iloc[start_idx : start_idx + items_per_page]

        st.markdown(render_dark_table(df_page), unsafe_allow_html=True)
    else:
        st.warning("Cargando datos...")

with col_right:
    st.markdown("##### 📝 Novedades Operativas")

    with st.form("form_publicar_novedad", clear_on_submit=True):
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            emisor_sel = st.selectbox("De:", LISTA_EMISORES, index=0)
        with col_f2:
            receptor_sel = st.selectbox("Para:", LISTA_RECEPTORES, index=0)

        prio_sel = st.radio("Prioridad del Mensaje:", ["Normal", "Auditoría", "Urgente"], horizontal=True)
        texto_msg = st.text_area("Contenido / Novedad:", height=60, placeholder="Escribe el mensaje aquí...")

        btn_publicar = st.form_submit_button("🚀 Publicar Novedad")

        if btn_publicar and texto_msg.strip():
            nuevo_id = f"msg_{int(time.time()*1000)}"
            nuevo_msg = {
                "id": nuevo_id,
                "emisor": emisor_sel,
                "receptor": receptor_sel,
                "prioridad": prio_sel,
                "contenido": texto_msg.strip(),
                "fecha_hora": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                "timestamp": time.time(),
                "estado": "Pendiente",
                "usuario_enterado": None,
                "fecha_enterado": None,
                "respuestas": [],
            }
            ESTADO_GLOBAL["mensajes_bitacora"].insert(0, nuevo_msg)
            emitir_notificacion_y_audio_js(
                nuevo_id,
                emisor_sel,
                receptor_sel,
                prio_sel,
                texto_msg.strip(),
                st.session_state.sound_enabled,
                st.session_state.notif_enabled,
            )
            st.rerun()

    # CONTENEDOR DE CHAT DE NOVEDADES
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)

    msgs = ESTADO_GLOBAL["mensajes_bitacora"]
    if not msgs:
        st.caption("No hay novedades registradas hoy.")

    for i, msg in enumerate(msgs):
        now_ts = time.time()
        elapsed = now_ts - msg.get("timestamp", now_ts)
        cycle_sec = elapsed % 240
        cycle_num = int(elapsed // 240)

        st.markdown(render_chat_message_html(msg, cycle_sec, cycle_num), unsafe_allow_html=True)

        col_m1, col_m2, col_m3 = st.columns([0.4, 0.3, 0.3])

        if msg.get("estado") == "Pendiente":
            with col_m1:
                user_action = st.selectbox("Usuario:", LISTA_EMISORES, key=f"user_act_{msg['id']}")
            with col_m2:
                if st.button("✅ Realizado", key=f"btn_done_{msg['id']}"):
                    msg["estado"] = "Atendido"
                    msg["usuario_enterado"] = user_action
                    msg["fecha_enterado"] = datetime.now().strftime("%H:%M:%S")
                    st.rerun()
        else:
            with col_m1:
                st.caption(f"Atendido por {msg.get('usuario_enterado')}")

        with col_m3:
            if st.button("🗑️ Borrar", key=f"btn_del_{msg['id']}"):
                ESTADO_GLOBAL["mensajes_bitacora"].remove(msg)
                st.rerun()

        with st.expander("💬 Responder a esta novedad", expanded=False):
            col_r1, col_r2 = st.columns([0.4, 0.6])
            with col_r1:
                user_reply = st.selectbox("Tu Nombre:", LISTA_EMISORES, key=f"u_rep_{msg['id']}")
            with col_r2:
                text_reply = st.text_input("Respuesta...", key=f"t_rep_{msg['id']}")

            if st.button("Enviar Respuesta", key=f"btn_send_rep_{msg['id']}") and text_reply.strip():
                msg["respuestas"].append(
                    {
                        "usuario": user_reply,
                        "texto": text_reply.strip(),
                        "fecha_hora": datetime.now().strftime("%H:%M"),
                    }
                )
                st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)
