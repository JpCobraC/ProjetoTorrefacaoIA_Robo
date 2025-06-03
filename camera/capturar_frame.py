import cv2
import config

class WebcamError(Exception):
    pass

def iniciar_webcam():
    cap = cv2.VideoCapture(config.CAMERA_ID)
    if not cap.isOpened():
        raise WebcamError(f"Erro: Não foi possível abrir a webcam ID {config.CAMERA_ID}.")
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)
    print(f"Webcam {config.CAMERA_ID} iniciada com {config.FRAME_WIDTH}x{config.FRAME_HEIGHT}")
    return cap

def capturar_frame_ativo(cap):
    """Captura um frame de um objeto 'cap' já iniciado."""
    if not cap or not cap.isOpened():
        print("Erro: Objeto da webcam não está iniciado ou é inválido.")
        return None
    ret, frame = cap.read()
    if not ret:
        print("Erro: Não foi possível capturar o frame.")
        return None
    return frame

def liberar_webcam(cap):
    if cap and cap.isOpened():
        cap.release()
        print("Webcam liberada.")