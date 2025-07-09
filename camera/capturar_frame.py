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
    return cap

def capturar_frame_ativo(cap):
    if not cap or not cap.isOpened():
        raise WebcamError("Erro: Objeto da webcam não está iniciado ou é inválido.")
    ret, frame = cap.read()
    if not ret:
        raise WebcamError("Erro: Não foi possível capturar o frame.")
    return frame

def liberar_webcam(cap):
    if cap and cap.isOpened():
        cap.release()