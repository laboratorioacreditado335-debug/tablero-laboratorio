from datetime import datetime
import time
import urllib.parse
import numpy as np
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# ---------------------------------------------------------
# CONFIGURACIÓN DE PÁGINA Y ESTILOS MODO OSCURO (ESCALA 125% OPTIMIZADA)
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
    
    /* TARJETAS KPI ESCALADAS (ZOOM 125%) */
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

    /* CONTROLES Y BOTONES (ESCALA MÁS GRANDE Y LEGIBLE) */
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

    /* CAMPO DE BÚSQUEDA ESCALADO */
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

    /* ANIMACIÓN PARPADEO PARALELO CORRECCIÓN */
    @keyframes pulse-correccion {
        0% { background-color: rgba(239, 68, 68, 0.12); }
        50% { background-color: rgba(239, 68, 68, 0.30); }
        100% { background-color: rgba(239, 68, 68, 0.12); }
    }
    .row-correccion {
        animation: pulse-correccion 2.2s infinite !important;
        border-left: 4px solid #EF4444 !important;
    }

    ::-webkit-scrollbar { width: 5px; height: 5px; }
    ::-webkit-scrollbar-track { background: #0B1120; }
    ::-webkit-scrollbar-thumb { background: #1F2937; border-radius: 4px; }

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
if "manual_nav_bonus" not in st.session_state:
    st.session_state.manual_nav_bonus = 0
if "last_alarm_id" not in st.session_state:
    st.session_state.last_alarm_id = None


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
    """
    Lee una pestaña de Google Sheets en formato CSV.
    Se incluye `keep_default_na=False` para evitar que las iniciales 'NA'
    (Nicolás Arévalo) sean convertidas automáticamente a valores nulos (NaN).
    """
    nombre_enc = urllib.parse.quote(nombre_hoja)
    nocache = int(time.time())
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


def tiene_valor_valido(val):
    """Verifica si una celda contiene un registro válido no vacío."""
    if pd.isna(val) or val is None:
        return False
    v = str(val).strip().upper()
    if v in [
        "",
        "NAN",
        "NONE",
        "NULL",
        "NAT",
        "#ERROR!",
        "#N/A",
        "#VALOR!",
    ]:
        return False
    return True


def calcular_progreso_orden(row):
    """
    Calcula el porcentaje exacto de avance (4 hitos de 25% cada uno):
    1. Registrada en el día = 25% (Base por existir)
    2. Certificado Firmado = +25% (ESTRICTAMENTE 'SI' / 'SÍ')
    3. Enviado = +25% (ESTRICTAMENTE 'SI' / 'SÍ')
    4. CRM Salida = +25% (ESTRICTAMENTE 'SI' / 'SÍ')
    """
    progreso = 25  # Hito 1: Registrada (25%)

    cer = str(row.get("Cer firmado", row.get("CER FIRMADO", ""))).strip().upper()
    env = str(row.get("Enviado", row.get("ENVIADO", ""))).strip().upper()
    crm_sal = str(row.get("CRM salida", row.get("CRM SALIDA", ""))).strip().upper()

    if cer in ["SI", "SÍ"]:
        progreso += 25

    if env in ["SI", "SÍ"]:
        progreso += 25

    if crm_sal in ["SI", "SÍ"]:
        progreso += 25

    return min(100, progreso)


def cargar_datos_gsheets():
    try:
        df_proceso_raw = leer_hoja_google("C. Proceso órdenes", header_none=True)
        # Leemos NOTAS DEL DIA sin cabecera para ubicar exactamente la celda D2 (fila index 1, columna index 3)
        df_notas_raw = leer_hoja_google("NOTAS DEL DIA", header_none=True)

        alarm_trigger_val = None
        if df_notas_raw is not None and not df_notas_raw.empty:
            try:
                if df_notas_raw.shape[0] > 1 and df_notas_raw.shape[1] > 3:
                    v_d2 = str(df_notas_raw.iloc[1, 3]).strip()
                    if v_d2 and v_d2.lower() not in ["nan", "none", "null", ""]:
                        alarm_trigger_val = v_d2
            except Exception:
                pass

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
            df_notas = df_notas.replace("", np.nan).dropna(how="all")

        return df_proceso, df_notas, "Conectado correctamente", alarm_trigger_val

    except Exception as e:
        return None, None, f"Error al conectar con Google Sheets: {str(e)}", None


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
            # Columna de Responsables ajustada a un ancho menor
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
                # Manejo dinámico de textos diferentes a "SI" en Envíos, CRM Salida o Estados
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

    return f'<div style="background: #111827; border-left: 3px solid {border_color}; border-radius: 5px; padding: 5px 8px; margin-bottom: 3px; display: flex; justify-content: space-between; align-items: center; gap: 8px;"><div style="color: #F3F4F6; font-size: 12px; font-weight: 500; line-height: 1.2; flex-grow: 1;">{descripcion}</div><div style="background-color: {s_style["bg"]}; color: {s_style["text"]}; border: 1px solid {s_style["border"]}; font-size: 10px; font-weight: 700; padding: 2px 6px; border-radius: 6px; white-space: nowrap;">{estado}</div></div>'


# ---------------------------------------------------------
# TABLERO DE CONTROL DINÁMICO Y FLUIDO
# ---------------------------------------------------------
@st.fragment(run_every=5)
def render_tablero_fluido():
    df_main, df_bitacora, info_estado, alarm_val = cargar_datos_gsheets()

    # CONTROL DE ALARMA SONORA ROBUSTO (MULTINAVEGADOR)
    if alarm_val is not None:
        if st.session_state.last_alarm_id is None:
            st.session_state.last_alarm_id = alarm_val
        elif st.session_state.last_alarm_id != alarm_val:
            st.session_state.last_alarm_id = alarm_val
            components.html(
                """
                <script>
                (function() {
                    try {
                        const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
                        
                        function playBell() {
                            const now = audioCtx.currentTime;
                            
                            // Nota 1 (Campana principal C5)
                            const osc1 = audioCtx.createOscillator();
                            const gain1 = audioCtx.createGain();
                            osc1.type = 'sine';
                            osc1.frequency.setValueAtTime(523.25, now);
                            gain1.gain.setValueAtTime(0.5, now);
                            gain1.gain.exponentialRampToValueAtTime(0.0001, now + 1.2);
                            osc1.connect(gain1);
                            gain1.connect(audioCtx.destination);
                            osc1.start(now);
                            osc1.stop(now + 1.2);

                            // Nota 2 (Armónico agudo G5)
                            const osc2 = audioCtx.createOscillator();
                            const gain2 = audioCtx.createGain();
                            osc2.type = 'sine';
                            osc2.frequency.setValueAtTime(783.99, now + 0.12);
                            gain2.gain.setValueAtTime(0.6, now + 0.12);
                            gain2.gain.exponentialRampToValueAtTime(0.0001, now + 1.8);
                            osc2.connect(gain2);
                            gain2.connect(audioCtx.destination);
                            osc2.start(now + 0.12);
                            osc2.stop(now + 1.8);
                        }

                        if (audioCtx.state === 'suspended') {
                            audioCtx.resume().then(() => playBell()).catch(() => playBell());
                        } else {
                            playBell();
                        }
                    } catch(e) {
                        console.error("Error reproduciendo audio:", e);
                    }
                })();
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

        # Fallback por posición si Responsables no ha sido mapeado
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
        col_btn1, col_btn2, col_search, col_info = st.columns([1, 1, 1.8, 2.5])

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
            search_val = st.text_input(
                "Buscar Orden",
                value=st.session_state.get("search_term", ""),
                placeholder="🔍 Buscar N° Orden...",
                key="search_input_widget",
                label_visibility="collapsed",
            )
            st.session_state.search_term = search_val

        if st.session_state.search_term.strip():
            term = st.session_state.search_term.strip().lower()
            col_target = "# Orden" if "# Orden" in df_vista.columns else df_vista.columns[0]
            df_vista = df_vista[
                df_vista[col_target].astype(str).str.lower().str.contains(term, na=False)
            ]

        # CALCULOS DE PAGINACIÓN Y TIEMPOS INTELIGENTES
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
            duracion_base = 180  # 3 minutos fijos para la primera página
        else:
            duracion_base = max(15, int(60 * (cant_items_pagina / filas_por_pagina)))

        duracion_total = duracion_base + st.session_state.get("manual_nav_bonus", 0)

        ahora = time.time()
        tiempo_transcurrido = ahora - st.session_state.last_switch_time

        if tiempo_transcurrido >= duracion_total and total_paginas > 1:
            st.session_state.page_index = (st.session_state.page_index + 1) % total_paginas
            st.session_state.last_switch_time = me
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

    else:
        st.error(f"⚠️ {info_estado}")

    st.markdown(
        "<hr style='border-color: #1F2937; margin: 3px 0;'>",
        unsafe_allow_html=True,
    )

    # 3. SECCIÓN INFERIOR COMPACTA Y AMPLIFICADA
    c_left, c_middle, c_right = st.columns([1.2, 1.1, 1.2])

    with c_left:
        st.markdown("<h4 style='margin:0 0 1px 0; font-size:13.5px; color:#F3F4F6;'>🚚 Programados del Día</h4>", unsafe_allow_html=True)
        st.caption(f"🗓️ Fecha: **{fecha_activa_str}** | {total_hoy} órdenes")
        
        progresos = []
        if df_hoy is not None and not df_hoy.empty:
            for _, r in df_hoy.iterrows():
                ord_num = limpiar_texto(r.get('# Orden', ''))
                if ord_num:
                    pct = calcular_progreso_orden(r)
                    progresos.append((ord_num, pct))

        if progresos:
            acumulado_general = int(np.mean([p[1] for p in progresos]))
            
            st.markdown(
                f'<div style="background-color: #111827; border: 1px solid #1F2937; border-radius: 5px; padding: 4px 8px; margin-bottom: 4px;">'
                f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2px;">'
                f'<span style="font-size: 10.5px; font-weight: 700; color: #9CA3AF;">PROMEDIO DÍA</span>'
                f'<span style="font-size: 12.5px; font-weight: 800; color: #38BDF8;">{acumulado_general}%</span>'
                f'</div>'
                f'<div style="background-color: #1F2937; border-radius: 4px; height: 6px; width: 100%; overflow: hidden;">'
                f'<div style="background: linear-gradient(90deg, #3B82F6, #10B981); height: 100%; width: {acumulado_general}%;"></div>'
                f'</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

            html_progresos = '<div style="display: flex; flex-direction: column; gap: 3px;">'
            for ord_num, pct in progresos:
                bar_color = "#10B981" if pct == 100 else ("#3B82F6" if pct >= 50 else "#F59E0B")
                html_progresos += (
                    f'<div class="progress-order-card">'
                    f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2px;">'
                    f'<span style="font-size: 11.5px; font-weight: 700; color: #F3F4F6;">📦 Orden #{ord_num}</span>'
                    f'<span style="font-size: 11px; font-weight: 800; color: {bar_color};">{pct}%</span>'
                    f'</div>'
                    f'<div style="background-color: #1F2937; border-radius: 3px; height: 5px; width: 100%; overflow: hidden;">'
                    f'<div style="background-color: {bar_color}; height: 100%; width: {pct}%;"></div>'
                    f'</div>'
                    f'</div>'
                )
            html_progresos += '</div>'
            st.markdown(html_progresos, unsafe_allow_html=True)
        else:
            st.info(f"Sin órdenes programadas hoy ({fecha_activa_str}).")

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
            col_p = next((c for c in df_bitacora.columns if "TIPO" in str(c).upper() or "PRIORIDAD" in str(c).upper()), None)
            col_d = next((c for c in df_bitacora.columns if "DESCRIP" in str(c).upper() or "NOTA" in str(c).upper() or "AVISO" in str(c).upper()), None)
            col_e = next((c for c in df_bitacora.columns if "ESTADO" in str(c).upper()), None)

            avisos_html = '<div style="display: flex; flex-direction: column; gap: 3px;">'
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
