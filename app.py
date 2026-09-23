from datetime import datetime
import time
import urllib.parse
import numpy as np
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
# 2. ESTILOS CSS PERSONALIZADOS (MODO OSCURO)
# ==========================================
st.markdown(
    """
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
""",
    unsafe_allow_html=True,
)


# ==========================================
# 3. LECTURA Y PROCESAMIENTO DE GOOGLE SHEETS
# ==========================================
def cargar_datos_gsheets():
    try:
        # Validación defensiva de la existencia de SPREADSHEET_ID
        if "SPREADSHEET_ID" not in st.secrets:
            st.error(
                "⚠️ La clave **SPREADSHEET_ID** no está configurada en `st.secrets`.\n\n"
                "Por favor configúrala en el panel de Streamlit Cloud (**Settings > Secrets**) "
                "o en tu archivo local `.streamlit/secrets.toml` agregando:\n"
                '```toml\nSPREADSHEET_ID = "tu_id_de_google_sheet"\n
