import cv2
import numpy as np
from camera.capturar_frame import iniciar_webcam, capturar_frame_ativo, liberar_webcam

def preprocessar_frame_para_yolo():
    cap = iniciar_webcam()
    try:
        frame = capturar_frame_ativo(cap)
    finally:
        liberar_webcam(cap)

    INITIALX, INITIALY, WIDTH, HEIGHT = 129, 48, 347, 356
    NEW_WIDTH, NEW_HEIGHT = 256, 256

    y_final_cut = INITIALY + HEIGHT
    x_final_cut = INITIALX + WIDTH
    y_final_cut = min(y_final_cut, frame.shape[0])
    x_final_cut = min(x_final_cut, frame.shape[1])

    image_cropped = frame[INITIALY:y_final_cut, INITIALX:x_final_cut]

    blob = cv2.dnn.blobFromImage(image_cropped,
                                  scalefactor=(1.0/127.5),
                                  size=(NEW_WIDTH, NEW_HEIGHT),
                                  mean=(127.5, 127.5, 127.5),
                                  swapRB=True,
                                  crop=False)



    input_yolo = blob.astype(np.float32)
    return input_yolo, frame.shape
