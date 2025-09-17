import cv2
import numpy as np
import config

def preprocessar_grao_para_cnn(imagem_grao):
    if imagem_grao is None or imagem_grao.size == 0:
        return None
    
    # Usa o tamanho do config, ou um valor padrão se não encontrar
    CNN_INPUT_SIZE = getattr(config, 'CNN_INPUT_SIZE', (64, 64))

    # Redimensiona para o tamanho de entrada da CNN
    grao_resized = cv2.resize(imagem_grao, CNN_INPUT_SIZE)
    
    # Normaliza os pixels para o intervalo [0, 1]
    grao_normalized = grao_resized.astype(np.float32) / 255.0
    
    # Adiciona a dimensão do 'batch', que o modelo TFLite da CNN espera
    input_cnn = np.expand_dims(grao_normalized, axis=0)
    
    return input_cnn