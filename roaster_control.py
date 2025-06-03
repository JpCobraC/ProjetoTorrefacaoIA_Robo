import time
import config

# Mude para True quando for rodar no Raspberry Pi
EXECUTAR_EM_RASPBERRY_PI = False # MUDE PARA True NO PI

if EXECUTAR_EM_RASPBERRY_PI:
    try:
        import RPi.GPIO as GPIO
    except ImportError:
        print("AVISO: RPi.GPIO não pôde ser importado. Funções de controle do torrador serão simuladas.")
        EXECUTAR_EM_RASPBERRY_PI = False # Força simulação se a importação falhar
else:
    print("AVISO: EXECUTAR_EM_RASPBERRY_PI é False. Funções de controle do torrador serão simuladas.")


def configurar_gpio():
    if EXECUTAR_EM_RASPBERRY_PI:
        GPIO.setmode(GPIO.BCM) # Ou GPIO.BOARD, dependendo da sua preferência
        GPIO.setwarnings(False) # Desativa avisos de canal já em uso, etc.
        GPIO.setup(config.PIN_AQUECEDOR, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(config.PIN_VENTOINHA, GPIO.OUT, initial=GPIO.LOW)
        # GPIO.setup(config.PIN_MOTOR_TAMBOR, GPIO.OUT, initial=GPIO.LOW) # Descomente se for usar
        print("GPIOs configurados no modo BCM.")
    else:
        print("Simulando configuração de GPIOs.")

def _controlar_elemento(nome_elemento, pino, ligar: bool):
    """Função interna para controlar um elemento."""
    estado_str = "LIGADO" if ligar else "DESLIGADO"
    if EXECUTAR_EM_RASPBERRY_PI:
        GPIO.output(pino, GPIO.HIGH if ligar else GPIO.LOW)
        print(f"Hardware: Elemento '{nome_elemento}' (pino {pino}) {estado_str}.")
    else:
        print(f"Simulação: Elemento '{nome_elemento}' (pino {pino}) {estado_str}.")

def controlar_aquecedor(ligar: bool):
    _controlar_elemento("Aquecedor", config.PIN_AQUECEDOR, ligar)

def controlar_ventoinha(ligar: bool):
    _controlar_elemento("Ventoinha", config.PIN_VENTOINHA, ligar)

def controlar_motor_tambor(ligar: bool): # Exemplo
    _controlar_elemento("Motor Tambor", config.PIN_MOTOR_TAMBOR, ligar)

def limpar_gpio():
    if EXECUTAR_EM_RASPBERRY_PI:
        print("Limpando configurações dos GPIOs...")
        GPIO.cleanup() # Limpa todos os canais configurados por este script
    else:
        print("Simulando limpeza de GPIOs.")

# Exemplo de uso para teste individual do módulo
if __name__ == '__main__':
    print("Testando controle do torrador (simulado ou real)...")
    configurar_gpio()
    try:
        controlar_aquecedor(True)
        time.sleep(2)
        controlar_aquecedor(False)
        time.sleep(1)
        controlar_ventoinha(True)
        time.sleep(2)
        controlar_ventoinha(False)
    except KeyboardInterrupt:
        print("Teste interrompido.")
    finally:
        limpar_gpio()
    print("Teste do controle do torrador finalizado.")