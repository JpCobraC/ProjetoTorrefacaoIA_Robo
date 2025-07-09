import config
import RPi.GPIO as GPIO

def configurar_gpio():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(config.PIN_VENTOINHA, GPIO.OUT, initial=GPIO.LOW)

def controlar_ventoinha(ligar: bool):
    GPIO.output(config.PIN_VENTOINHA, GPIO.HIGH if ligar else GPIO.LOW)

def set_dimmer_resistencia(valor_pwm: float):
    if not hasattr(set_dimmer_resistencia, 'pwm'):
        set_dimmer_resistencia.pwm = GPIO.PWM(config.PIN_AQUECEDOR, 100)
        set_dimmer_resistencia.pwm.start(0)
    duty_cycle = max(0, min(100, valor_pwm * 100))
    set_dimmer_resistencia.pwm.ChangeDutyCycle(duty_cycle)

def limpar_gpio():
    GPIO.cleanup()