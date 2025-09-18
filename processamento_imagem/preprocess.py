# No arquivo: processamento_imagem/preprocess.py

import cv2
import numpy as np

# Tenta importar o config e a função oficial de pré-processamento
try:
    import config
    from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
    TENSORFLOW_DISPONIVEL = True
except ImportError:
    config = None
    preprocess_input = None
    TENSORFLOW_DISPONIVEL = False

def aplicar_crop_customizado(frame):
    if frame is None: return None
    INITIALX, INITIALY, WIDTH, HEIGHT = 129, 48, 347, 356
    img_height, img_width = frame.shape[:2]
    y_final_cut = min(INITIALY + HEIGHT, img_height)
    x_final_cut = min(INITIALX + WIDTH, img_width)
    return frame[INITIALY:y_final_cut, INITIALX:x_final_cut]

def preprocessar_grao_para_cnn(imagem_grao):
    if imagem_grao is None or imagem_grao.size == 0:
        return None
    
    CNN_INPUT_SIZE = getattr(config, 'CNN_INPUT_SIZE', (128, 128))
    grao_resized = cv2.resize(imagem_grao, CNN_INPUT_SIZE)
    input_cnn = np.expand_dims(grao_resized, axis=0)

    # --- A LINHA MAIS IMPORTANTE DO PROJETO ---
    # Esta função converte os pixels para a escala exata [-1, 1] que o MobileNetV2 espera.
    if TENSORFLOW_DISPONIVEL:
        input_cnn = preprocess_input(input_cnn)
    else:
        print("AVISO: TensorFlow completo não foi encontrado. A normalização pode estar incorreta.")
        input_cnn = input_cnn.astype(np.float32) / 255.0
        
    return input_cnn