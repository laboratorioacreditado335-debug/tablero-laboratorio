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
    /* Ocultar la barra superior de Streamlit */
    header, [data-testid="stHeader"] {
        display: none !important;
    }
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
    }

    .stApp {
        background-color: #0B1120;
        color: #F3F4F6;
    }
    
    .kpi-card {
        background-color: #111827;
        border: 1px solid #1F2937;
        border-radius: 8px;
        padding: 16px;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.4);
    }
    .kpi-title {
        color: #9CA3AF;
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 1px;
        text-transform: uppercase;
        margin-bottom: 4px;
    }
    .kpi-value {
        color: #FFFFFF;
        font-size: 28px;
        font-weight: 800;
    }

    .order-card {
        background-color: #1E293B;
        border-left: 4px solid #3B82F6;
        border-radius: 6px;
        padding: 10px 14px;
        margin-bottom: 8px;
        font-weight: 600;
        color: #F8FAFC;
        font-size: 13.5px;
    }

    /* ESTILO RESALTADO PARA NAVEGACIÓN */
    div.stButton > button {
        background-color: #1E293B !important;
        color: #38BDF8 !important;
        border: 1px solid #3B82F6 !important;
        border-radius: 6px !important;
        font-weight: 700 !important;
        font-size: 13px !important;
        padding: 6px 16px !important;
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

    /* ANIMACIÓN Y PARPADEO PARA FILAS CON "CORRECCIONES" */
    @keyframes pulse-correccion {
        0% { background-color: rgba(239, 68, 68, 0.12); }
        50% { background-color: rgba(239, 68, 68, 0.30); }
        100% { background-color: rgba(239, 68, 68, 0.12); }
    }
    .row-correccion {
        animation: pulse-correccion 2.2s infinite !important;
        border-left: 5px solid #EF4444 !important;
    }

    /* Scrollbar personalizada */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }
    ::-webkit-scrollbar-track {
        background: #0B1120;
    }
    ::-webkit-scrollbar-thumb {
        background: #1F2937;
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #374151;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""",
    unsafe_allow_html=True,
)

# ID del archivo de Google Sheets
SPREADSHEET_ID = "1bNDr35UasLS5zly1Sbq2ykbtmsTn9Fy4"

# Inicializar estados de sesión para navegación suave sin recarga de pantalla
if "page_index" not in st.session_state:
  st.session_state.page_index = 0
if "last_switch_time" not in st.session_state:
  st.session_state.last_switch_time = time.time()


# ---------------------------------------------------------
# FUNCIONES AUXILIARES Y LECTURA INSTANTÁNEA
# ---------------------------------------------------------
def limpiar_numero(val):
  """Elimina .0 de los números de orden y formatos numéricos."""
  if pd.isna(val) or val is None:
    return ""
  val_str = str(val).strip()
  if val_str.endswith(".0"):
    val_str = val_str[:-2]
  return val_str


def leer_hoja_google(nombre_hoja):
  """Lectura directa sin caché para actualización instantánea."""
  nombre_enc = urllib.parse.quote(nombre_hoja)
  nocache = int(time.time())
  url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet={nombre_enc}&_cb={nocache}"
  return pd.read_csv(url)


def parsear_fecha(val):
  if pd.isna(val) or val is None:
    return None
  if isinstance(val, (datetime, pd.Timestamp)):
    return val.date()
  val_str = str(val).strip()
  if val_str in ["", "nan", "None", "NAT", "NaT"]:
    return None

  try:
    num_val = float(val_str)
    if 35000 < num_val < 65000:
      dt = pd.to_datetime(num_val, unit="D", origin="1899-12-30")
      return dt.date()
  except (ValueError, TypeError):
    pass

  val_clean = val_str.split(" ")[0]
  dt = pd.to_datetime(val_clean, dayfirst=True, errors="coerce")
  if pd.isna(dt):
    dt = pd.to_datetime(val_clean, errors="coerce")

  return dt.date() if pd.notna(dt) else None


def cargar_datos_gsheets():
  try:
    df_proceso_raw = leer_hoja_google("C. Proceso órdenes")
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
        df_proceso.columns = df_proceso_raw.iloc[header_idx].values
      else:
        df_proceso = df_proceso_raw.copy()

      df_proceso.columns = [str(col).strip() for col in df_proceso.columns]

      if "Fecha" in df_proceso.columns:
        df_proceso["Fecha"] = df_proceso["Fecha"].apply(
            lambda x: np.nan
            if pd.isna(x) or str(x).strip() in ["", "nan", "None", "NaN"]
            else x
        )
        df_proceso["Fecha"] = df_proceso["Fecha"].ffill()

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
    return "<div style='color: #9CA3AF; text-align: center; padding: 20px;'>Sin datos registrados en Google Sheets.</div>"

  headers = list(df_page.columns)

  col_cer = next(
      (c for c in headers if "CER" in c.upper() and "FIRM" in c.upper()), None
  )
  col_crm_salida = next(
      (c for c in headers if "CRM" in c.upper() and "SALIDA" in c.upper()), None
  )
  col_orden = next((c for c in headers if "ORDEN" in c.upper()), None)

  html = '<div style="overflow-x: auto; border: 1px solid #1F2937; border-radius: 8px; background-color: #111827; margin-bottom: 10px;"><table style="width: 100%; border-collapse: collapse; color: #F3F4F6; font-size: 13.5px; text-align: left;"><thead><tr style="background-color: #1F2937; color: #9CA3AF; font-weight: 700; text-transform: uppercase; font-size: 11px; letter-spacing: 0.5px;">'

  for h in headers:
    html += f'<th style="padding: 12px 16px; border-bottom: 1px solid #374151;">{h}</th>'
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
    crm_vacio = crm_sal_val in ["", "nan", "none", "null", "None"]
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
      val = limpiar_numero(row[h])

      if h == col_orden and es_atascada:
        badge = f'{val} <span style="background-color: rgba(245, 158, 11, 0.25); color: #FBBF24; border: 1px solid #F59E0B; padding: 2px 7px; border-radius: 8px; font-weight: 700; font-size: 10.5px; margin-left: 6px;" title="Certificado firmado pero sin registro de CRM Salida">⚠️ Atascada</span>'
      elif h == col_crm_salida and es_atascada and not val:
        badge = '<span style="color: #F59E0B; font-weight: 700; font-size: 11px;">⚠️ Pendiente salida</span>'
      elif val.upper() in ["SI", "SÍ"]:
        badge = '<span style="background-color: rgba(16, 185, 129, 0.2); color: #A7F3D0; border: 1px solid #10B981; padding: 2px 8px; border-radius: 10px; font-weight: 700; font-size: 11px;">Si</span>'
      elif "APROBAC" in val.upper():
        badge = f'<span style="background-color: rgba(245, 158, 11, 0.2); color: #FDE68A; border: 1px solid #F59E0B; padding: 2px 8px; border-radius: 10px; font-weight: 600; font-size: 11px;">{val}</span>'
      elif "CORREC" in val.upper():
        badge = f'<span style="background-color: rgba(239, 68, 68, 0.35); color: #FCA5A5; border: 1px solid #EF4444; padding: 2px 8px; border-radius: 10px; font-weight: 800; font-size: 11px;">{val} ⚠️</span>'
      else:
        badge = val

      html += f'<td style="padding: 10px 16px;">{badge}</td>'
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
      "AUDITORÍA": "#8B5CF6",
      "AUDITORIA": "#8B5CF6",
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
      "CANCELADO": {
          "bg": "rgba(107, 114, 128, 0.2)",
          "text": "#D1D5DB",
          "border": "#6B7280",
      },
  }
  s_style = status_styles.get(
      estado,
      {"bg": "rgba(107, 114, 128, 0.2)", "text": "#E5E7EB", "border": "#9CA3AF"},
  )

  return f'<div style="background: #111827; border-left: 5px solid {border_color}; border-radius: 8px; padding: 12px 16px; margin-bottom: 10px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3); display: flex; justify-content: space-between; align-items: center; gap: 12px;"><div style="color: #F3F4F6; font-size: 13.5px; font-weight: 500; line-height: 1.4; flex-grow: 1;">{descripcion}</div><div style="background-color: {s_style["bg"]}; color: {s_style["text"]}; border: 1px solid {s_style["border"]}; font-size: 11px; font-weight: 700; padding: 4px 10px; border-radius: 12px; letter-spacing: 0.5px; white-space: nowrap;">{estado}</div></div>'


# ---------------------------------------------------------
# TABLERO DE CONTROL (FRAGMENTO SUAVE SIN RECARGA DE NAVEGADOR)
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

  ordenes_hoy = []
  total_hoy = 0
  cumplidos_hoy = 0
  porcentaje_hoy = 0

  hoy_dt = datetime.now().date()
  fecha_activa_str = hoy_dt.strftime("%d/%m/%Y")

  total_reg = 0
  total_firm = 0
  total_env = 0
  total_pend = 0

  if df_main is not None and not df_main.empty:
    cols_existentes = [c for c in cols_deseadas if c in df_main.columns]

    if "# Orden" not in cols_existentes:
      col_ord_alt = next(
          (c for c in df_main.columns if "ORDEN" in str(c).upper()), None
      )
      if col_ord_alt:
        cols_existentes.append(col_ord_alt)

    if "Aprob. Comercial" not in cols_existentes:
      col_aprob_alt = next(
          (
              c
              for c in df_main.columns
              if "APROB" in str(c).upper() and "COMER" in str(c).upper()
          ),
          None,
      )
      if col_aprob_alt and col_aprob_alt not in cols_existentes:
        cols_existentes.append(col_aprob_alt)

    df_vista = df_main[cols_existentes].copy()
    col_ord_main = (
        "# Orden" if "# Orden" in df_vista.columns else cols_existentes[1]
    )

    # Limpieza de números de orden
    df_vista[col_ord_main] = df_vista[col_ord_main].apply(limpiar_numero)

    df_vista = df_vista[
        df_vista[col_ord_main].notna()
        & (df_vista[col_ord_main].astype(str).str.strip() != "")
        & (
            ~df_vista[col_ord_main]
            .astype(str)
            .str.strip()
            .str.lower()
            .isin(["nan", "none", "null"])
        )
    ].copy()

    if "Fecha" in df_vista.columns:
      df_vista["Fecha_dt"] = df_vista["Fecha"].apply(parsear_fecha)

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

      df_hoy = df_vista[df_vista["Fecha_dt"] == hoy_dt]
      if not df_hoy.empty:
        for o in df_hoy[col_ord_main].dropna().tolist():
          o_s = limpiar_numero(o)
          if o_s and o_s.lower() != "nan":
            ordenes_hoy.append(o_s)

      total_hoy = len(ordenes_hoy)

      if total_hoy > 0 and not df_vista.empty:
        df_vista_temp = df_vista.copy()

        for ord_n in ordenes_hoy:
          match_row = df_vista_temp[df_vista_temp[col_ord_main] == ord_n]
          if not match_row.empty:
            if "Enviado" in match_row.columns and str(
                match_row["Enviado"].values[0]
            ).strip().upper() in ["SI", "SÍ"]:
              cumplidos_hoy += 1
            elif "Cer firmado" in match_row.columns and str(
                match_row["Cer firmado"].values[0]
            ).strip().upper() in ["SI", "SÍ"]:
              cumplidos_hoy += 1

        porcentaje_hoy = int((cumplidos_hoy / total_hoy) * 100)

      df_vista["Fecha"] = df_vista["Fecha_dt"].apply(
          lambda d: d.strftime("%d/%m/%Y")
          if pd.notna(d) and d is not None
          else ""
      )
      df_vista = df_vista.drop(columns=["Fecha_dt"], errors="ignore")

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

  st.markdown("<br>", unsafe_allow_html=True)

  # 2. CONTROL DE PAGINACIÓN Y ROTACIÓN CADA 90 SEGUNDOS (EN SESIÓN)
  if df_vista is not None and not df_vista.empty:
    filas_por_pagina = 8
    total_filas = len(df_vista)
    total_paginas = max(
        1, (total_filas + filas_por_pagina - 1) // filas_por_pagina
    )

    ahora = time.time()

    # Cambio automático de página tras 90 segundos inactivo
    if (
        ahora - st.session_state.last_switch_time
    ) >= 90 and total_paginas > 1:
      st.session_state.page_index = (
          st.session_state.page_index + 1
      ) % total_paginas
      st.session_state.last_switch_time = ahora

    if st.session_state.page_index >= total_paginas:
      st.session_state.page_index = 0

    b_col1, b_col2, b_col3 = st.columns([1.2, 1.2, 3.6])
    with b_col1:
      if st.button("⬆️ Subir / Anterior"):
        st.session_state.page_index = (
            st.session_state.page_index - 1
        ) % total_paginas
        st.session_state.last_switch_time = time.time()
        st.rerun()

    with b_col2:
      if st.button("⬇️ Bajar / Siguiente"):
        st.session_state.page_index = (
            st.session_state.page_index + 1
        ) % total_paginas
        st.session_state.last_switch_time = time.time()
        st.rerun()

    with b_col3:
      segundos_restantes = max(
          0, int(90 - (ahora - st.session_state.last_switch_time))
      )
      st.caption(
          f"Página {st.session_state.page_index + 1} de {total_paginas}"
          f" (Mostrando {filas_por_pagina} registros) | ⏱️ Cambio automático"
          f" en {segundos_restantes}s"
      )

    p_idx = st.session_state.page_index
    inicio = p_idx * filas_por_pagina
    fin = min(inicio + filas_por_pagina, total_filas)
    df_pagina = df_vista.iloc[inicio:fin]

    st.markdown(render_dark_table(df_pagina), unsafe_allow_html=True)

  else:
    st.error(f"⚠️ {info_estado}")

  st.markdown(
      "<hr style='border-color: #1F2937; margin: 25px 0;'>",
      unsafe_allow_html=True,
  )

  # 3. SECCIÓN INFERIOR
  c_left, c_middle, c_right = st.columns([1, 1, 1.2])

  with c_left:
    st.markdown("### 🚚 Programadas p/ Hoy")
    st.caption(
        f"🗓️ Fecha actual: **{fecha_activa_str}** | {total_hoy} órdenes"
        " agendadas"
    )
    if ordenes_hoy:
      html_list = (
          '<div style="max-height: 280px; overflow-y: auto; padding-right:'
          ' 4px;">'
      )
      for ord_num in ordenes_hoy:
        html_list += f'<div class="order-card">📦 Orden #: {ord_num}</div>'
      html_list += "</div>"
      st.markdown(html_list, unsafe_allow_html=True)
    else:
      st.info(f"No hay órdenes programadas para hoy ({fecha_activa_str}).")

  with c_middle:
    st.markdown("### 🎯 Meta del Día")
    st.markdown(
        f"""
        <div style="background-color: #111827; border: 1px solid #1F2937; border-radius: 6px; padding: 14px 16px; margin-bottom: 15px; display: flex; justify-content: space-between; align-items: center;">
            <span style="font-size: 11px; font-weight: 700; color: #9CA3AF; letter-spacing: 0.5px;">DESPACHOS CUMPLIDOS</span>
            <span style="font-size: 15px; font-weight: 800; color: #60A5FA;">{cumplidos_hoy} de {total_hoy} ({porcentaje_hoy}%)</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

  with c_right:
    st.markdown("### 📌 Bitácora / Avisos del Día")
    if df_bitacora is None or df_bitacora.empty:
      st.info(
          "No hay avisos ni notas registradas en la hoja 'NOTAS DEL DIA'."
      )
    else:
      col_p = next(
          (
              c
              for c in df_bitacora.columns
              if "TIPO" in str(c).upper() or "PRIORIDAD" in str(c).upper()
          ),
          None,
      )
      col_d = next(
          (
              c
              for c in df_bitacora.columns
              if "DESCRIP" in str(c).upper()
              or "NOTA" in str(c).upper()
              or "AVISO" in str(c).upper()
          ),
          None,
      )
      col_e = next(
          (c for c in df_bitacora.columns if "ESTADO" in str(c).upper()), None
      )

      avisos_html = (
          '<div style="max-height: 280px; overflow-y: auto; padding-right:'
          ' 4px;">'
      )
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


# Ejecutar el tablero fluido
render_tablero_fluido()