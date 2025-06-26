import serial
import threading
import time

PORTA_SERIAL = 'COM24'
BAUD_RATE = 9600

ser = serial.Serial(PORTA_SERIAL, BAUD_RATE, timeout=1) # Abre a conexão serial com o ESP32.
time.sleep(2)            # espera o ESP32 resetar e completar o boot
ser.reset_input_buffer() # joga fora tudo que ficou no buffer (os logs do bootloader)

def ler_serial():
    while True:
        if ser.in_waiting:
            dados = ser.readline().decode('utf-8', errors='ignore').strip() #Lê a linha completa e decodifica em UTF-8
            if dados.strip():  # garante que está realmente vazio de conteúdo visível
                print(f"[ESP32] {dados}")
            else:
                print(f"[IGNORADO] '{repr(dados)}'")


threading.Thread(target=ler_serial, daemon=True).start()

print("Digite algo para enviar ao ESP32:")
try:
    while True:
        texto = input("> ")
        ser.write((texto + "\n").encode('utf-8'))
except KeyboardInterrupt:
    print("\nEncerrando...") 
    ser.close() # pressionar Ctrl+C para encerrar o programa de forma limpa
