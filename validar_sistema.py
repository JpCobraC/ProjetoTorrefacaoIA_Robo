import os
import sys
import pickle
import cv2
import numpy as np

os.environ['CUDA_VISIBLE_DEVICES'] = ''
DIRETORIO_ATUAL = os.path.dirname(os.path.abspath(__file__))
sys.path.append(DIRETORIO_ATUAL)

from config import X_INICIAL, Y_INICIAL, X_FINAL, Y_FINAL

# ATENCAO: este e o 'modelo_agtron_linear_interpolado.pkl' (gerado por
# treinar_novo.py --interpolado), treinado com TODOS os frames do
# dataset_interpolado.csv -- cujos alvos de Agtron sao ESTIMATIVAS por
# interpolacao temporal linear entre as marcacoes manuais de fase, nao
# medicoes reais de Agtron. Nao confundir com o 'modelo_agtron_linear.pkl'
# original, treinado apenas com os 4 pontos reais de calibracao (ver
# gerar_dataset_interpolado.py e treinar_novo.py para o historico completo).
CAMINHO_MODELO = os.path.join(DIRETORIO_ATUAL, 'modelo_agtron_linear_interpolado.pkl')

modelo_agtron = None

print("[IA] Carregando modelo de regressao linear (Agtron via CIELAB)...")
try:
    with open(CAMINHO_MODELO, 'rb') as f:
        modelo_agtron = pickle.load(f)
    print("[IA] Modelo carregado com sucesso!")
except Exception as e:
    print(f"[ERRO CRÍTICO] Falha ao carregar '{CAMINHO_MODELO}': {e}")

# analisar_distribuicao_torra foi removida: ela dependia de rotulos numericos
# (ex: "25", "35"...) vindos do CLIP antigo, extraidos via regex, para agregar
# a classificacao de varios graos individuais. No pipeline atual nao ha mais
# graos segmentados -- cada chamada a analisar_para_api ja analisa a ROI
# inteira e devolve (agtron, classe, desvio) de um unico frame. A agregacao
# da rajada de 3 frames e feita diretamente em api_teste.py.


def classificar_fase(valor_agtron):
    """Mapeia o Agtron predito para o rotulo de fase da torra, usando as faixas
    aproximadas dos dados reais coletados (Cru~95, Clara~75, Media~55, Escura~35)."""
    if valor_agtron >= 85:
        return "Cru"
    elif valor_agtron >= 65:
        return "Clara"
    elif valor_agtron >= 45:
        return "Media"
    else:
        return "Escura"


def analisar_para_api(frame_ao_vivo):
    global modelo_agtron
    try:
        if modelo_agtron is None:
            return 0.0, "Erro IA", 0.0

        if frame_ao_vivo is None:
            return 0.0, "Sem grãos", 0.0

        # Aplica a mesma mira (ROI) fixa usada em analise_torra.py
        zona_do_cafe = frame_ao_vivo[Y_INICIAL:Y_FINAL, X_INICIAL:X_FINAL]
        if zona_do_cafe is None or zona_do_cafe.size == 0:
            return 0.0, "Sem grãos", 0.0

        # Matematica da cor (espaco CIELAB), igual a analise_torra.py
        lab_frame = cv2.cvtColor(zona_do_cafe, cv2.COLOR_BGR2LAB)
        l_channel, a_channel, b_channel = cv2.split(lab_frame)

        l_mean = float(np.mean(l_channel))
        a_mean = float(np.mean(a_channel))
        b_mean = float(np.mean(b_channel))

        dados_entrada = np.array([[l_mean, a_mean, b_mean]])
        agtron_predito = float(modelo_agtron.predict(dados_entrada)[0])

        classe = classificar_fase(agtron_predito)

        # Sem graos individuais para comparar entre si, o desvio padrao de L
        # dentro da propria ROI serve de proxy para a uniformidade visual do lote
        desvio = float(np.std(l_channel))

        return round(agtron_predito, 2), classe, round(desvio, 2)

    except Exception as e:
        print(f"[ERRO] Falha na analise da ROI/CIELAB: {e}")
        return 0.0, "Erro Interno", 0.0
