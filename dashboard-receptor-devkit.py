import streamlit as st
import pandas as pd
import serial
import altair as alt
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Telemetria Reptiles", layout="wide")
st.title("Dashboard Reptiles Baja 🦎")

# Atualiza a cada 200 ms (ajustado)
st_autorefresh(interval=200, key="atualizacao_telemetria")

PORTA_SERIAL = 'COM31'
BAUDRATE = 115200

# Inicializa conexão serial
if "ser" not in st.session_state:
    try:
        st.session_state.ser = serial.Serial(PORTA_SERIAL, BAUDRATE, timeout=0.05)
        st.success(f"Conectado à porta {PORTA_SERIAL}")
    except Exception as e:
        st.error(f"Erro ao conectar na serial: {e}")
        st.stop()

# DataFrame para armazenar dados
if "dados" not in st.session_state:
    st.session_state.dados = pd.DataFrame(columns=[
        "Tempo_ms", "Data", "Hora", "Latitude", "Longitude",
        "RPM Motor", "Vel D", "RPM D", "Alerta BOX", "Alerta GPS"
    ])

def extrair_valores(linha):
    try:
        partes = linha.split(",")
        if len(partes) != 10:
            return None  # linha inválida

        tempo_ms = int(partes[0])
        data = partes[1]
        hora = partes[2]
        lat = float(partes[3])
        lon = float(partes[4])
        rpm_motor = int(partes[5])
        vel_d = int(partes[6])
        rpm_d = int(partes[7])
        alerta_box = int(partes[8])
        alerta_gps = int(partes[9])

        return [tempo_ms, data, hora, lat, lon, rpm_motor, vel_d, rpm_d, alerta_box, alerta_gps]
    except Exception:
        return None

# Lê dados da serial
if st.session_state.ser.in_waiting:
    buffer = st.session_state.ser.read(st.session_state.ser.in_waiting).decode(errors='ignore')
    linhas = buffer.splitlines()

    for linha in linhas:
        valores = extrair_valores(linha)
        if valores:
            nova_linha = pd.DataFrame([valores], columns=st.session_state.dados.columns)
            st.session_state.dados = pd.concat([st.session_state.dados, nova_linha], ignore_index=True)
            st.session_state.dados = st.session_state.dados.tail(100)  # mantém últimos 100 pontos

# Mostra gráficos se houver dados
df = st.session_state.dados.copy()
df = df.dropna()

if not df.empty:
    def plot(col, title, color):
        return alt.Chart(df).mark_line(color=color).encode(
            x=alt.X("Tempo_ms:Q", title="Tempo (ms)"),
            y=alt.Y(f"{col}:Q", title=title)
        ).properties(height=200)

    col1, col2 = st.columns(2)
    col1.altair_chart(plot("RPM Motor", "RPM Motor", "orange"), use_container_width=True)
    col2.altair_chart(plot("Vel D", "Velocidade (km/h)", "green"), use_container_width=True)
    st.altair_chart(plot("RPM D", "RPM Roda", "blue"), use_container_width=True)

    ult = df.iloc[-1]
    col1.metric("RPM Motor", f"{ult['RPM Motor']} RPM")
    col2.metric("Velocidade", f"{ult['Vel D']} km/h")
    st.metric("RPM Roda", f"{ult['RPM D']} RPM")

    # Mostra posição GPS
    st.map(pd.DataFrame({"lat": [ult["Latitude"]], "lon": [ult["Longitude"]]}))

    # Indicadores de alerta
    st.write(f"🚨 Alerta BOX: {ult['Alerta BOX']}")
    st.write(f"📡 Alerta GPS: {ult['Alerta GPS']}")
