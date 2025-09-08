import streamlit as st
import pandas as pd
import serial
import re
import altair as alt
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Telemetria Reptiles", layout="wide")
st.title("Reptiles Baja 🦎")

st_autorefresh(interval=150, key="atualizacao_telemetria") #antes tava 100 (apenas teste) agora em 200 atualiza 5x por segundo

PORTA_SERIAL = 'COM31'
BAUDRATE = 115200  # ver 

if "ser" not in st.session_state:
    try:
        st.session_state.ser = serial.Serial(PORTA_SERIAL, BAUDRATE, timeout=0.05)
        st.success(f"Conectado à porta {PORTA_SERIAL}")
    except Exception as e:
        st.error(f"Erro ao conectar na serial: {e}")
        st.stop()

if "dados" not in st.session_state:
    st.session_state.dados = pd.DataFrame(columns=["Tempo", "RPM Motor", "Velocidade", "RPM Roda"])


def extrair_valores(linha):
    try:
        # captura letras + numero inteiro ou decimal (positivo ou negativo)
        dados = dict(re.findall(r'([a-z])=?(-?\d+(?:\.\d+)?)', linha))

        rpm_motor = int(float(dados.get('r', 0)))
        velocidade = int(float(dados.get('v', 0)))
        rpm_roda = int(float(dados.get('y', 0)))

        return [rpm_motor, velocidade, rpm_roda]
    except Exception as e:
        st.warning(f"Erro ao extrair valores da linha: {linha} ({e})")
        return None


if st.session_state.ser.in_waiting:
    buffer = st.session_state.ser.read(st.session_state.ser.in_waiting).decode(errors='ignore')
    linhas = buffer.splitlines()

    for linha in linhas:
        valores = extrair_valores(linha)
        if valores:
            tempo = pd.Timestamp.now()
            nova_linha = pd.DataFrame([[tempo] + valores], columns=st.session_state.dados.columns)
            st.session_state.dados = pd.concat([st.session_state.dados, nova_linha], ignore_index=True)
            st.session_state.dados = st.session_state.dados.tail(50)  # Mantém últimos 50 pontos

# mostra os gráficos (se houver dados)
df = st.session_state.dados.copy()
df = df.dropna()  # remove valores nulos
if not df.empty:
    df["Tempo"] = pd.to_datetime(df["Tempo"])

    def plot(col, title, color):
        return alt.Chart(df).mark_line(color=color).encode(
            x=alt.X("Tempo:T", title="Tempo"),
            y=alt.Y(f"{col}:Q", title=title)
        ).properties(height=200)

    col1, col2 = st.columns(2)
    col1.altair_chart(plot("RPM Motor", "RPM Motor", "red"), use_container_width=True)
    col2.altair_chart(plot("Velocidade", "Velocidade (km/h)", "blue"), use_container_width=True)
    st.altair_chart(plot("RPM Roda", "RPM Roda", "green"), use_container_width=True)

    ult = df.iloc[-1]
    col1.metric("RPM Motor", f"{ult['RPM Motor']} RPM")
    col2.metric("Velocidade", f"{ult['Velocidade']} km/h")
    st.metric("RPM Roda", f"{ult['RPM Roda']} RPM")

import time
import random

# --- MODO DE TESTE / SIMULAÇÃO --- A PARTIR DAQUI SÓ TESTE, APAGAR DEPOIS (O RESTO FUNCIONA)
# Ative colocando True
MODO_TESTE = False

if MODO_TESTE:
    st.subheader("🧪 Modo de Teste Ativado")

    if "dados_teste" not in st.session_state:
        st.session_state.dados_teste = pd.DataFrame(columns=["Tempo", "RPM Motor", "Velocidade", "RPM Roda"])

    # inicializa contador no session_state
    if "contador" not in st.session_state:
        st.session_state.contador = 0

    # simula chegada de dados (números crescentes)
    for _ in range(5):  # gera 5 amostras por atualização
        tempo = pd.Timestamp.now()
        rpm_motor = st.session_state.contador * 100
        velocidade = st.session_state.contador
        rpm_roda = st.session_state.contador * 50

        nova_linha = pd.DataFrame([[tempo, rpm_motor, velocidade, rpm_roda]],
                                  columns=st.session_state.dados_teste.columns)
        st.session_state.dados_teste = pd.concat([st.session_state.dados_teste, nova_linha], ignore_index=True)
        st.session_state.dados_teste = st.session_state.dados_teste.tail(50)

        st.session_state.contador += 1

    # mede tempo de atualização
    inicio = time.time()
    df_teste = st.session_state.dados_teste.copy()
    fim = time.time()
    tempo_exec = (fim - inicio) * 1000  # em ms

    st.write(f"⏱️ Tempo de processamento (ms): {tempo_exec:.2f}")

    if not df_teste.empty:
        df_teste["Tempo"] = pd.to_datetime(df_teste["Tempo"])

        def plot_teste(col, title, color):
            return alt.Chart(df_teste).mark_line(color=color).encode(
                x=alt.X("Tempo:T", title="Tempo"),
                y=alt.Y(f"{col}:Q", title=title)
            ).properties(height=200)

        col1, col2 = st.columns(2)
        col1.altair_chart(plot_teste("RPM Motor", "RPM Motor (teste)", "orange"), use_container_width=True)
        col2.altair_chart(plot_teste("Velocidade", "Velocidade (teste)", "green"), use_container_width=True)
        st.altair_chart(plot_teste("RPM Roda", "RPM Roda (teste)", "blue"), use_container_width=True)

        ult = df_teste.iloc[-1]
        col1.metric("RPM Motor (teste)", f"{ult['RPM Motor']} RPM")
        col2.metric("Velocidade (teste)", f"{ult['Velocidade']} km/h")
        st.metric("RPM Roda (teste)", f"{ult['RPM Roda']} RPM")
