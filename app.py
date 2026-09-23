import streamlit as st
import pandas as pd
import streamlit.components.v1 as components

st.set_page_config(
    page_title="Monitor de NOTAS DEL DIA",
    page_icon="🔔",
    layout="wide"
)

# 1. URL de la hoja pública de Google Sheets en formato CSV
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSm9m8T3i1JgC6K80_9G5hTq-Q-1k5uI_xS6c7z4N1t8a/pub?gid=0&single=true&output=csv"

# Inicializar estado de sesión
if "last_alarm_id" not in st.session_state:
    st.session_state.last_alarm_id = None
if "play_sound" not in st.session_state:
    st.session_state.play_sound = False

st.title("🔔 Monitor de Alarmas - NOTAS DEL DIA")

# Función para reproducir tono usando Web Audio API
def render_audio_player(trigger_sound: bool = False):
    html_code = f"""
    <div style="background-color: #1e222d; padding: 15px; border-radius: 8px; text-align: center; color: white;">
        <button id="btn-sound" onclick="playBeep()" style="
            background-color: #ff4b4b; 
            color: white; 
            border: none; 
            padding: 10px 20px; 
            border-radius: 5px; 
            font-weight: bold; 
            cursor: pointer;
            font-size: 16px;">
            🔊 Activar / Probar Alarma
        </button>
        <p id="status-text" style="margin-top: 8px; font-size: 13px; color: #888;">
            Haz clic para autorizar el sonido en tu navegador
        </p>
    </div>

    <script>
    function playBeep() {{
        try {{
            const AudioContext = window.AudioContext || window.webkitAudioContext;
            const ctx = new AudioContext();
            
            if (ctx.state === 'suspended') {{
                ctx.resume();
            }}

            // Ráfaga de 4 tonos de alarma alta frecuencia (880Hz / 1760Hz)
            for (let i = 0; i < 4; i++) {{
                const osc = ctx.createOscillator();
                const gain = ctx.createGain();
                
                osc.type = 'sawtooth';
                osc.frequency.setValueAtTime(880, ctx.currentTime + i * 0.25);
                osc.frequency.setValueAtTime(1760, ctx.currentTime + i * 0.25 + 0.1);
                
                gain.gain.setValueAtTime(0.3, ctx.currentTime + i * 0.25);
                gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + i * 0.25 + 0.2);
                
                osc.connect(gain);
                gain.connect(ctx.destination);
                
                osc.start(ctx.currentTime + i * 0.25);
                osc.stop(ctx.currentTime + i * 0.25 + 0.2);
            }}

            document.getElementById('status-text').innerText = '✅ Sonido activado correctamente';
            document.getElementById('status-text').style.color = '#4CAF50';
        }} catch (e) {{
            console.error("Error al reproducir audio:", e);
        }}
    }}

    // Si Python ordena sonar, ejecutar beep automáticamente
    if ({'true' if trigger_sound else 'false'}) {{
        playBeep();
    }}
    </script>
    """
    components.html(html_code, height=100)

# Cargar datos desde Google Sheets
@st.cache_data(ttl=10)
def fetch_data():
    return pd.read_csv(SHEET_CSV_URL, header=None)

try:
    df_raw = fetch_data()
    
    # Extraer celda D2 (Fila 2, Columna 4 -> Índice 1, 3)
    alarm_val = None
    if df_raw.shape[0] > 1 and df_raw.shape[1] > 3:
        val = str(df_raw.iloc[1, 3]).strip()
        if val and val.lower() not in ["nan", "none", "null", ""]:
            alarm_val = val

    # Control de disparo de alarma
    trigger_alarm = False
    if alarm_val:
        if st.session_state.last_alarm_id is None:
            st.session_state.last_alarm_id = alarm_val
            trigger_alarm = True
        elif st.session_state.last_alarm_id != alarm_val:
            st.session_state.last_alarm_id = alarm_val
            trigger_alarm = True

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Estado de la Celda D2")
        if alarm_val:
            st.error(f"🚨 **¡ALARMA ACTIVA!** Valor detectado: `{alarm_val}`")
        else:
            st.success("✅ Sin alarmas pendientes en celda D2")

    with col2:
        render_audio_player(trigger_sound=trigger_alarm)

    st.subheader("Vista previa de NOTAS DEL DIA")
    st.dataframe(df_raw, use_container_width=True)

except Exception as e:
    st.error(f"Error al conectar con Google Sheets: {e}")
