import cv2
import numpy as np
import pickle

from config import X_INICIAL, Y_INICIAL, X_FINAL, Y_FINAL

# --- CONFIGURACAO DA FONTE DE VIDEO ---
# True  = le um frame do arquivo de video (util para testar em bancada sem a torra ligada)
# False = le um frame ao vivo da camera (uso real durante a torra)
USAR_VIDEO_DE_TESTE = True
CAMINHO_VIDEO_TESTE = 'torra.mp4'
CAMERA_ID = 0

# Mesmo modelo usado por validar_sistema.py: treinado com o dataset_interpolado.csv
# (estimativas por interpolacao temporal, R²=0.85), nao o modelo_agtron_linear.pkl
# original (treinado so com os 4 pontos reais de calibracao).
CAMINHO_MODELO = 'modelo_agtron_linear_interpolado.pkl'


def carregar_modelo():
    """Carrega o modelo de Regressao Linear treinado a partir do arquivo .pkl."""
    with open(CAMINHO_MODELO, 'rb') as f:
        return pickle.load(f)


def capturar_frame_atual():
    """Abre a fonte configurada (camera ou video), captura um unico frame e libera o recurso."""
    fonte = CAMINHO_VIDEO_TESTE if USAR_VIDEO_DE_TESTE else CAMERA_ID
    cap = cv2.VideoCapture(fonte)

    if not cap.isOpened():
        raise RuntimeError("Nao foi possivel abrir a fonte de video (camera ou arquivo).")

    try:
        ret, frame = cap.read()
        if not ret or frame is None:
            raise RuntimeError("Nao foi possivel capturar um frame da fonte de video.")
        return frame
    finally:
        cap.release()


def extrair_lab_da_roi(frame):
    """Recorta a mira verde (ROI) e retorna a media dos canais L, a, b em CIELAB."""
    frame = cv2.resize(frame, (640, 480))
    zona_do_cafe = frame[Y_INICIAL:Y_FINAL, X_INICIAL:X_FINAL]

    lab_frame = cv2.cvtColor(zona_do_cafe, cv2.COLOR_BGR2LAB)
    l_channel, a_channel, b_channel = cv2.split(lab_frame)

    l_mean = float(np.mean(l_channel))
    a_mean = float(np.mean(a_channel))
    b_mean = float(np.mean(b_channel))
    return l_mean, a_mean, b_mean


def main():
    """Ponto de entrada chamado pelo Artisan (dispositivo 'Program') a cada intervalo configurado.

    Imprime SOMENTE "agtron_valor,l_mean" no stdout. Qualquer falha (camera
    ausente, modelo nao carregado, video ausente, etc.) resulta em "0,0"
    para nao travar a leitura do Artisan.
    """
    try:
        modelo_agtron = carregar_modelo()
        frame = capturar_frame_atual()
        l_mean, a_mean, b_mean = extrair_lab_da_roi(frame)

        dados_entrada = np.array([[l_mean, a_mean, b_mean]])
        valor_agtron_predito = modelo_agtron.predict(dados_entrada)[0]

        print(f"{valor_agtron_predito:.2f},{l_mean:.2f}")
    except Exception:
        print("0,0")


if __name__ == '__main__':
    main()
