# No arquivo: processamento_imagem/preprocess.py
import cv2

def aplicar_crop_customizado(frame):
    if frame is None:
        print("Erro de pré-processamento: frame de entrada é None.")
        return None

    # Coordenadas do seu recorte customizado
    INITIALX, INITIALY, WIDTH, HEIGHT = 129, 48, 347, 356

    # Garante que as coordenadas do recorte não ultrapassem os limites da imagem
    img_height, img_width = frame.shape[:2]
    y_final_cut = min(INITIALY + HEIGHT, img_height)
    x_final_cut = min(INITIALX + WIDTH, img_width)

    # Aplica o recorte
    imagem_recortada = frame[INITIALY:y_final_cut, INITIALX:x_final_cut]
    
    # Retorna APENAS a imagem
    return imagem_recortada