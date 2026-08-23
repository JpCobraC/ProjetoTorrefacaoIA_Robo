import os
import sys
import pickle
import cv2
import numpy as np
from collections import deque

os.environ['CUDA_VISIBLE_DEVICES'] = ''
DIRETORIO_ATUAL = os.path.dirname(os.path.abspath(__file__))
sys.path.append(DIRETORIO_ATUAL)

from config import X_INICIAL, Y_INICIAL, X_FINAL, Y_FINAL

# Modelo treinado exclusivamente com torra_v2.mp4 (melhor estabilizacao de
# camera), R²=0.9480 -- substituiu o modelo anterior (so torra.mp4, R²=0.8534)
# em 2026-08-21.
# ATENCAO: alvos de Agtron sao ESTIMATIVAS por interpolacao temporal linear
# entre as marcacoes manuais de fase (dataset_interpolado_v2_apenas.csv), nao
# medicoes reais de Agtron. O modelo anterior 'modelo_agtron_linear_interpolado.pkl'
# foi mantido no disco como backup para rollback rapido se necessario (ver
# gerar_dataset_interpolado.py e treinar_novo.py para o historico completo).
CAMINHO_MODELO = os.path.join(DIRETORIO_ATUAL, 'modelo_agtron_linear_v2_producao.pkl')

modelo_agtron = None

print("[IA] Carregando modelo de regressao linear (Agtron via CIELAB)...")
try:
    with open(CAMINHO_MODELO, 'rb') as f:
        modelo_agtron = pickle.load(f)
    print("[IA] Modelo carregado com sucesso!")
except Exception as e:
    print(f"[ERRO CRÍTICO] Falha ao carregar '{CAMINHO_MODELO}': {e}")

# Tamanho da janela da media movel de suavizacao do Agtron (ver buffer_agtron
# e o comentario dentro de analisar_para_api).
TAMANHO_JANELA_SUAVIZACAO = 5

# Buffer persistente ENTRE CHAMADAS (nao e reiniciado a cada frame/request),
# no mesmo espirito do modelo carregado uma unica vez acima no escopo do
# modulo. Guarda os ultimos TAMANHO_JANELA_SUAVIZACAO valores BRUTOS de
# Agtron preditos pelo modelo, usados para calcular a media movel devolvida
# por analisar_para_api.
buffer_agtron = deque(maxlen=TAMANHO_JANELA_SUAVIZACAO)

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
    global modelo_agtron, buffer_agtron
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
        agtron_bruto = float(modelo_agtron.predict(dados_entrada)[0])

        # Suavizacao por media movel: com o video de teste (torra_v2.mp4), o
        # Agtron bruto oscila bastante frame a frame no inicio da leitura
        # (chega a subir de volta perto de 95 depois de ja ter caido pra 80).
        # E ruido real de captura -- desfoque de movimento do grao girando no
        # tambor, ou reflexo momentaneo em frames especificos -- nao erro do
        # modelo. O jeito certo de resolver na origem seria travar a exposicao
        # da camera via firmware (frente ainda pendente); ate la, suaviza-se
        # aqui: cada novo valor bruto entra no buffer persistente do modulo
        # (buffer_agtron) e o Agtron devolvido e a media das ultimas
        # TAMANHO_JANELA_SUAVIZACAO leituras, nao o valor isolado deste frame.
        buffer_agtron.append(agtron_bruto)
        agtron_predito = sum(buffer_agtron) / len(buffer_agtron)

        # Debug: descomente para comparar bruto vs suavizado lado a lado no
        # terminal (ver instrucoes de teste com torra_v2.mp4 no historico do PR).
        # print(f"[DEBUG SUAVIZACAO] bruto={agtron_bruto:.2f} | suavizado={agtron_predito:.2f} | janela={[round(v, 2) for v in buffer_agtron]}")

        classe = classificar_fase(agtron_predito)

        # Sem graos individuais para comparar entre si, o desvio padrao de L
        # dentro da propria ROI serve de proxy para a uniformidade visual do lote
        desvio = float(np.std(l_channel))

        return round(agtron_predito, 2), classe, round(desvio, 2)

    except Exception as e:
        print(f"[ERRO] Falha na analise da ROI/CIELAB: {e}")
        return 0.0, "Erro Interno", 0.0
