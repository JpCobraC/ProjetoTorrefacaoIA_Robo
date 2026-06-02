import cv2
import numpy as np

    # Importa o config apenas para pegar o tamanho da imagem, sem puxar bibliotecas pesadas
try:
    import sys
    import os
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    import config
except ImportError:
    config = None

def preprocessar_grao_para_clip(imagem_grao):
    """
    Prepara o recorte do grão (OpenCV) para o formato esperado pelos modelos de IA.
    Substitui completamente o uso do TensorFlow Keras para evitar conflitos de memória e Segmentation Faults no Linux.
    """
    if imagem_grao is None or imagem_grao.size == 0:
        return None
        
    # 1. Busca o tamanho esperado no config ou usa o padrão (128x128)
    CLIP_INPUT_SIZE = getattr(config, 'CLIP_INPUT_SIZE', (128, 128))
        
    # 2. Redimensiona a imagem usando o OpenCV (rápido e seguro em CPU)
    grao_resized = cv2.resize(imagem_grao, CLIP_INPUT_SIZE)
        
    # 3. Adiciona a dimensão do "batch" (necessário para a maioria das inferências locais)
    # Transforma de (128, 128, 3) para (1, 128, 128, 3)
    input_clip = np.expand_dims(grao_resized, axis=0)

    # 4. Normalização Matemática Estilo MobileNetV2 (SEM usar TensorFlow)
    # O MobileNetV2 espera valores entre -1 e 1.
    # Fórmula padrão: (imagem / 127.5) - 1.0
    input_clip = input_clip.astype(np.float32)
    input_clip = (input_clip / 127.5) - 1.0
            
    return input_clip
