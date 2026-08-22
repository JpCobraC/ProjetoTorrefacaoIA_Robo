import os
import sys
import traceback
import cv2
import numpy as np
import pickle

from config import X_INICIAL, Y_INICIAL, X_FINAL, Y_FINAL

# BUG CORRIGIDO (2026-08-21): CAMINHO_VIDEO_TESTE e CAMINHO_MODELO eram
# caminhos RELATIVOS. Isso funcionava rodando o script direto no terminal de
# dentro da pasta do projeto, mas falhava quando o Artisan chama este script
# como "Program device" -- o Artisan executa o processo a partir de outro
# diretorio de trabalho, entao cv2.VideoCapture(...)/open(...) nao achavam o
# arquivo, a excecao caia no fallback silencioso "0,0" e o problema passava
# despercebido. Agora os caminhos sao montados a partir de DIRETORIO_ATUAL
# (a pasta onde o proprio artisan_bridge.py esta), nao do cwd de quem chama.
DIRETORIO_ATUAL = os.path.dirname(os.path.abspath(__file__))

# Se a variavel de ambiente DEBUG_ARTISAN_BRIDGE estiver definida, qualquer
# excecao capturada em main() e impressa no stderr (nunca no stdout, para nao
# interferir no valor "agtron,l_mean" que o Artisan le da saida padrao).
DEBUG_ATIVO = bool(os.environ.get('DEBUG_ARTISAN_BRIDGE'))

# --- CONFIGURACAO DA FONTE DE VIDEO ---
# True  = le um frame do arquivo de video (util para testar em bancada sem a torra ligada)
# False = le um frame ao vivo da camera (uso real durante a torra)
USAR_VIDEO_DE_TESTE = False
# Alinhado com modelo_agtron_linear_v2_producao.pkl (treinado exclusivamente
# com torra_v2.mp4): usar torra.mp4 aqui desalinha o modo de teste do modelo
# em producao e gera predicoes fora da escala Agtron valida.
CAMINHO_VIDEO_TESTE = os.path.join(DIRETORIO_ATUAL, 'torra_v2.mp4')
CAMERA_ID = 0

# O Artisan chama este script como um PROCESSO NOVO a cada leitura (nao e um
# loop continuo: ele abre o processo, le a linha do stdout e o processo
# encerra). Isso nao afeta o uso com camera (ao vivo sempre entrega o frame
# atual), mas no modo de teste com video gravado, abrir o arquivo do zero a
# cada chamada sempre posicionava no frame 0 -- a leitura ficava travada no
# mesmo valor, sem simular a torra progredindo. Para contornar isso, o modo
# de teste guarda em ARQUIVO_POSICAO_TESTE o numero do ultimo frame lido e,
# a cada chamada, avanca FRAMES_POR_CHAMADA frames a partir dali (dando a
# volta para o frame 0 ao chegar no fim do video), simulando a passagem do
# tempo entre chamadas sucessivas do Artisan.
FRAMES_POR_CHAMADA = 20
ARQUIVO_POSICAO_TESTE = os.path.join(DIRETORIO_ATUAL, '.posicao_video_teste.txt')

# Modelo treinado exclusivamente com torra_v2.mp4 (melhor estabilizacao de
# camera), R²=0.9480 -- substituiu o modelo anterior (so torra.mp4, R²=0.8534)
# em 2026-08-21.
# Mesmo modelo usado por validar_sistema.py: treinado com dataset_interpolado_v2_apenas.csv
# (estimativas por interpolacao temporal), nao o modelo_agtron_linear.pkl
# original (treinado so com os 4 pontos reais de calibracao). O modelo anterior
# 'modelo_agtron_linear_interpolado.pkl' foi mantido no disco como backup.
CAMINHO_MODELO = os.path.join(DIRETORIO_ATUAL, 'modelo_agtron_linear_v2_producao.pkl')


def carregar_modelo():
    """Carrega o modelo de Regressao Linear treinado a partir do arquivo .pkl."""
    with open(CAMINHO_MODELO, 'rb') as f:
        return pickle.load(f)


def ler_posicao_salva():
    """Le o numero do ultimo frame lido em ARQUIVO_POSICAO_TESTE. Se o arquivo nao existir ou estiver corrompido, comeca do frame 0."""
    try:
        with open(ARQUIVO_POSICAO_TESTE, 'r') as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError):
        return 0


def salvar_posicao(posicao):
    """Grava o numero do frame atual em ARQUIVO_POSICAO_TESTE para a proxima chamada continuar dali.

    Usa flush + fsync porque o processo encerra logo em seguida (o Artisan
    chama o script do zero a cada leitura): sem forcar a gravacao em disco
    antes do processo morrer, a proxima chamada corre o risco de ler um
    valor desatualizado do arquivo de estado.
    """
    with open(ARQUIVO_POSICAO_TESTE, 'w') as f:
        f.write(str(posicao))
        f.flush()
        os.fsync(f.fileno())


def capturar_frame_video_teste(cap):
    """Avanca FRAMES_POR_CHAMADA frames a partir da posicao salva da chamada anterior, dando a volta para o inicio ao chegar no fim do video (loop), e salva a nova posicao."""
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    posicao_anterior = ler_posicao_salva()
    posicao_nova = posicao_anterior + FRAMES_POR_CHAMADA
    if total_frames > 0 and posicao_nova >= total_frames:
        posicao_nova = 0

    cap.set(cv2.CAP_PROP_POS_FRAMES, posicao_nova)
    ret, frame = cap.read()
    if not ret or frame is None:
        # Fim inesperado do video (ex: contagem de frames imprecisa): volta
        # para o inicio e tenta ler o frame 0 antes de desistir.
        posicao_nova = 0
        cap.set(cv2.CAP_PROP_POS_FRAMES, posicao_nova)
        ret, frame = cap.read()
        if not ret or frame is None:
            raise RuntimeError("Nao foi possivel capturar um frame da fonte de video.")

    salvar_posicao(posicao_nova)
    return frame


def capturar_frame_atual():
    """Abre a fonte configurada (camera ou video), captura um unico frame e libera o recurso."""
    fonte = CAMINHO_VIDEO_TESTE if USAR_VIDEO_DE_TESTE else CAMERA_ID
    cap = cv2.VideoCapture(fonte)

    if not cap.isOpened():
        raise RuntimeError("Nao foi possivel abrir a fonte de video (camera ou arquivo).")

    try:
        if USAR_VIDEO_DE_TESTE:
            return capturar_frame_video_teste(cap)

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
        # Fallback silencioso intencional: nunca deixar uma excecao travar a
        # leitura do Artisan. Com DEBUG_ARTISAN_BRIDGE definida, o detalhe da
        # excecao ainda vai para o stderr (o Artisan so le o stdout).
        if DEBUG_ATIVO:
            print("[DEBUG_ARTISAN_BRIDGE] Excecao capturada em main():", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
        print("0,0")


if __name__ == '__main__':
    main()
