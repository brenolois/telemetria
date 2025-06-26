import streamlit as st
import pandas as pd
import serial
import time
import re
import os

st.set_page_config(page_title="Telemetria Reptiles", layout="wide")
st.title("Dashboard Reptiles Baja 🦎")

PORTA_SERIAL = 'COM24'
BAUDRATE = 9600

try:
    ser = serial.Serial(PORTA_SERIAL, BAUDRATE, timeout=1)
    st.success(f"Conectado à porta {PORTA_SERIAL}")
except:
    st.error(f"Erro ao conectar à porta {PORTA_SERIAL}")
    st.stop()

# DataFrame para armazenar os dados
df = pd.DataFrame(columns=["Tempo", "RPM Motor", "Velocidade", "RPM Roda"])

MAX_PONTOS = 30 # últimos segundos a aparecerem no gráfico
RESET_GRAFICO = 100  # quando atingir esse tamanho, reinicia os gráficos

col1, col2 = st.columns(2)

col1.subheader("RPM do Motor")
col2.subheader("Velocidade (km/h)")
st.subheader("RPM das Rodas")

# Gráficos fixos
graf_rpm_motor = col1.line_chart()
graf_velocidade = col2.line_chart()
graf_rpm_roda = st.line_chart()

# Métricas fixas
metric_rpm_motor = col1.empty()
metric_velocidade = col2.empty()
metric_rpm_roda = st.empty()
linha_serial = st.empty()

# Função para extrair os dados do texto
def extrair_valores(linha):
    try:
        dados = dict(re.findall(r'([a-z])=?-?(\d+)', linha))
        rpm_motor = int(dados.get('r', 0))
        velocidade = int(dados.get('v', 0))
        rpm_roda = int(dados.get('y', 0))
        return [rpm_motor, velocidade, rpm_roda]
    except:
        return None

#loop principal
while True:
    try:
        linha = ser.readline().decode(errors='ignore').strip()

        valores = extrair_valores(linha)
        if valores:
            tempo_agora = pd.Timestamp.now()
            nova_linha = pd.DataFrame([[tempo_agora] + valores], columns=df.columns)
            # Salva a linha no arquivo CSV
            nova_linha.to_csv("telemetria.csv", mode='a', header=not pd.io.common.file_exists("telemetria.csv"), index=False)

            # Adiciona nova linha ao DataFrame completo
            df = pd.concat([df, nova_linha], ignore_index=True)
            # Limita visualização aos últimos N pontos
            df_viz = df.tail(MAX_PONTOS).set_index("Tempo")

            # Atualiza os gráficos com os dados mais recentes
            graf_rpm_motor.line_chart(df_viz[["RPM Motor"]])
            graf_velocidade.line_chart(df_viz[["Velocidade"]])
            graf_rpm_roda.line_chart(df_viz[["RPM Roda"]])

            # Atualiza as métricas atuais
            metric_rpm_motor.metric("RPM Motor Atual", f"{valores[0]} RPM")
            metric_velocidade.metric("Velocidade Atual", f"{valores[1]} km/h")
            metric_rpm_roda.metric("RPM Roda Atual", f"{valores[2]} RPM")

    except Exception as e:
        st.warning(f"Erro ao processar dados: {e}")

    time.sleep(0.1)
