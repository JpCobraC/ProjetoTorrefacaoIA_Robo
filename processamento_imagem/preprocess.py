import cv2
import numpy as np
import config

def aplicar_crop_customizado(frame):
    if frame is None:
        print("Erro de pré-processamento: frame de entrada para crop é None.")
        return None

    INITIALX, INITIALY, WIDTH, HEIGHT = 129, 48, 347, 356

    img_height, img_width = frame.shape[:2]
    y_final_cut = min(INITIALY + HEIGHT, img_height)
    x_final_cut = min(INITIALX + WIDTH, img_width)

    imagem_recortada = frame[INITIALY:y_final_cut, INITIALX:x_final_cut]
    
    return imagem_recortada

def preprocessar_grao_para_cnn(imagem_grao):
    if imagem_grao is None or imagem_grao.size == 0:
        return None
    
    # Usa o tamanho do config, ou um valor padrão se não encontrar
    CNN_INPUT_SIZE = getattr(config, 'CNN_INPUT_SIZE', (128, 128))

    # Redimensiona para o tamanho de entrada da CNN
    grao_resized = cv2.resize(imagem_grao, CNN_INPUT_SIZE)
    
    # Normaliza os pixels para o intervalo [0, 1]
    grao_normalized = grao_resized.astype(np.float32) / 255.0
    
    # Adiciona a dimensão do 'batch', que o modelo TFLite da CNN espera
    input_cnn = np.expand_dims(grao_normalized, axis=0)
    
    return input_cnn