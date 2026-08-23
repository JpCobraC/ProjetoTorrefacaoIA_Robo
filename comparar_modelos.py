import argparse
import os
import pickle
import sys

import cv2
import numpy as np
import matplotlib
matplotlib.use('Agg')  # sem display (roda direto no terminal/headless), so salva o PNG
import matplotlib.pyplot as plt

DIRETORIO_ATUAL = os.path.dirname(os.path.abspath(__file__))
sys.path.append(DIRETORIO_ATUAL)

# ROI CORRIGIDA atual, usada para os DOIS modelos igualmente -- fisicamente a
# camera/ROI de captura sao as mesmas, o que muda entre "antigo" e "novo" e
# so o modelo (pesos treinados), nao a regiao de imagem analisada.
from config import X_INICIAL, Y_INICIAL, X_FINAL, Y_FINAL

# ATENCAO (historico): modelo_agtron_linear_interpolado.pkl foi sobrescrito em
# 2026-08-23 por um retreino com a ROI corrigida (R2=0.9623), sem usar --saida
# em treinar_novo.py -- isso apagou do disco a versao anterior (R2=0.8534,
# ROI antiga que tocava o metal). A versao antiga foi recuperada do commit
# 0a9bd40f (git show 0a9bd40f:modelo_agtron_linear_interpolado.pkl) e salva
# aqui com nome proprio, para os dois modelos ficarem lado a lado sem ambiguidade.
CAMINHO_MODELO_ANTIGO = os.path.join(DIRETORIO_ATUAL, 'modelo_agtron_linear_antigo_roi.pkl')
CAMINHO_MODELO_NOVO = os.path.join(DIRETORIO_ATUAL, 'modelo_agtron_linear_novo_roi.pkl')

CAMINHO_VIDEO = os.path.join(DIRETORIO_ATUAL, 'torra_v2.mp4')
CAMINHO_SAIDA_GRAFICO = os.path.join(DIRETORIO_ATUAL, 'comparacao_modelos.png')

# A cada quantos frames uma leitura e feita (nao vale a pena rodar os dois
# modelos em TODO frame do video so pra comparar tendencia geral -- passo
# configuravel via --passo).
PASSO_FRAMES_PADRAO = 10

# Timestamps de ancora ja conhecidos (marcacao manual das 4 fases no video de
# teste), usados so para o resumo final -- mesma referencia de
# gerar_dataset_interpolado.py / dataset_interpolado_v2_apenas.csv.
ANCORAS_FASES = [
    ('Cru', 1.18),
    ('Clara', 85.9),
    ('Media', 111.5),
    ('Escura', 153.5),
]


def carregar_modelo(caminho):
    """Carrega um .pkl de modelo, com uma mensagem de erro clara se faltar --
    os dois modelos comparados aqui sao arquivos externos ao git normal (ver
    o comentario historico acima), entao um caminho errado e um erro real de
    uso, nao um caso que "nao pode acontecer"."""
    if not os.path.exists(caminho):
        print(f"[ERRO] Modelo nao encontrado: '{caminho}'")
        sys.exit(1)
    with open(caminho, 'rb') as f:
        return pickle.load(f)


def extrair_lab_medio(frame, x_inicial, y_inicial, x_final, y_final):
    """Mesma matematica de cor (ROI fixa + medias do espaco CIELAB) usada em
    validar_sistema.py/analise_torra.py, aplicada aqui uma unica vez por
    frame amostrado -- os dois modelos preveem em cima do MESMO L, a, b,
    entao a diferenca no grafico vem so dos pesos do modelo, nunca da ROI."""
    zona_do_cafe = frame[y_inicial:y_final, x_inicial:x_final]
    lab_frame = cv2.cvtColor(zona_do_cafe, cv2.COLOR_BGR2LAB)
    l_channel, a_channel, b_channel = cv2.split(lab_frame)
    return float(np.mean(l_channel)), float(np.mean(a_channel)), float(np.mean(b_channel))


def coletar_predicoes(modelo_antigo, modelo_novo, caminho_video, passo_frames):
    """Percorre o video amostrando 1 a cada `passo_frames` frames, aplicando a
    ROI corrigida (config.py) e prevendo o Agtron com os dois modelos sobre
    exatamente os mesmos L, a, b. Retorna 3 listas paralelas: tempos (s),
    predicoes do modelo antigo e predicoes do modelo novo."""
    captura = cv2.VideoCapture(caminho_video)
    if not captura.isOpened():
        print(f"[ERRO] Nao foi possivel abrir o video: '{caminho_video}'")
        sys.exit(1)

    fps = captura.get(cv2.CAP_PROP_FPS) or 30.0
    total_frames = int(captura.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"[VIDEO] '{caminho_video}': {total_frames} frames a {fps:.1f} FPS "
          f"({total_frames / fps:.1f}s), amostrando 1 a cada {passo_frames} frames.")

    tempos, predicoes_antigo, predicoes_novo = [], [], []
    indice_frame = 0

    while True:
        sucesso, frame = captura.read()
        if not sucesso:
            break

        if indice_frame % passo_frames == 0:
            l_mean, a_mean, b_mean = extrair_lab_medio(frame, X_INICIAL, Y_INICIAL, X_FINAL, Y_FINAL)
            dados_entrada = np.array([[l_mean, a_mean, b_mean]])

            pred_antigo = float(modelo_antigo.predict(dados_entrada)[0])
            pred_novo = float(modelo_novo.predict(dados_entrada)[0])

            tempos.append(indice_frame / fps)
            predicoes_antigo.append(pred_antigo)
            predicoes_novo.append(pred_novo)

        indice_frame += 1

    captura.release()
    print(f"[VIDEO] Concluido: {len(tempos)} amostras coletadas.")
    return tempos, predicoes_antigo, predicoes_novo


def gerar_grafico(tempos, predicoes_antigo, predicoes_novo, caminho_saida):
    todas_predicoes = predicoes_antigo + predicoes_novo

    # A escala valida do Agtron e 0-100 -- mas o proprio ponto deste grafico e
    # evidenciar que o modelo antigo (ROI antiga) extrapola bem acima disso
    # (ver resumo por fase: chega a 109 na fase Media). Prender ylim em (0,100)
    # cortava a curva rente ao teto, criando aquele efeito "serrilhado colado
    # na borda" que parece bug de renderizacao. Em vez de cortar, o eixo Y se
    # ajusta aos dados reais, com uma faixa sombreada marcando 0-100 como
    # referencia visual da escala Agtron valida -- assim da pra ver tanto a
    # forma real da curva quanto o quanto o modelo antigo sai da faixa.
    limite_superior = max(100, max(todas_predicoes)) + 5
    limite_inferior = min(0, min(todas_predicoes)) - 5

    plt.figure(figsize=(12, 6))
    plt.axhspan(0, 100, color='#6B8E4E', alpha=0.07, zorder=0, label='Faixa Agtron valida (0-100)')
    plt.plot(tempos, predicoes_antigo, label='Modelo antigo - ROI antiga', color='#8B5A2B', linewidth=1.8)
    plt.plot(tempos, predicoes_novo, label='Modelo novo - ROI corrigida', color='#C1440E', linewidth=1.8)

    # Marca as 4 fases de ancora tambem no grafico, para correlacionar
    # visualmente com o resumo impresso no terminal.
    for nome_fase, tempo_ancora in ANCORAS_FASES:
        plt.axvline(x=tempo_ancora, color='gray', linestyle='--', linewidth=0.8, alpha=0.6)
        plt.text(tempo_ancora, limite_superior - 1, nome_fase, rotation=90, fontsize=8, color='gray',
                  ha='right', va='top')

    plt.xlabel('Tempo (s)')
    plt.ylabel('Agtron')
    plt.ylim(limite_inferior, limite_superior)
    plt.title('Comparacao: modelo antigo (ROI antiga) vs. modelo novo (ROI corrigida)')
    plt.legend(loc='lower left')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(caminho_saida, dpi=150)
    print(f"[GRAFICO] Salvo em '{caminho_saida}'")


def imprimir_resumo_por_fase(tempos, predicoes_antigo, predicoes_novo):
    """Para cada timestamp de ancora conhecido, acha a amostra coletada mais
    proxima (o passo de amostragem raramente cai exatamente no segundo da
    ancora) e imprime a predicao de cada modelo nesse ponto, lado a lado."""
    tempos_np = np.array(tempos)

    print("\n--- RESUMO POR FASE (ancoras conhecidas) ---")
    print(f"{'Fase':<8} {'t alvo':>8} {'t amostrado':>12} {'Antigo':>10} {'Novo':>10} {'Diferenca':>11}")
    for nome_fase, tempo_alvo in ANCORAS_FASES:
        indice_mais_proximo = int(np.argmin(np.abs(tempos_np - tempo_alvo)))
        t_amostrado = tempos[indice_mais_proximo]
        pred_antigo = predicoes_antigo[indice_mais_proximo]
        pred_novo = predicoes_novo[indice_mais_proximo]
        diferenca = pred_novo - pred_antigo
        print(f"{nome_fase:<8} {tempo_alvo:>7.2f}s {t_amostrado:>11.2f}s "
              f"{pred_antigo:>10.2f} {pred_novo:>10.2f} {diferenca:>+11.2f}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Compara as predicoes do modelo antigo (ROI antiga) e do modelo novo '
                    '(ROI corrigida) sobre o mesmo video de teste, usando sempre a ROI '
                    'corrigida atual (config.py) para os dois.'
    )
    parser.add_argument(
        '--passo', type=int, default=PASSO_FRAMES_PADRAO,
        help=f'Analisa 1 a cada N frames do video (padrao: {PASSO_FRAMES_PADRAO}).',
    )
    args = parser.parse_args()

    print("[MODELOS] Carregando modelo antigo e modelo novo...")
    modelo_antigo = carregar_modelo(CAMINHO_MODELO_ANTIGO)
    modelo_novo = carregar_modelo(CAMINHO_MODELO_NOVO)

    tempos, predicoes_antigo, predicoes_novo = coletar_predicoes(
        modelo_antigo, modelo_novo, CAMINHO_VIDEO, args.passo
    )

    gerar_grafico(tempos, predicoes_antigo, predicoes_novo, CAMINHO_SAIDA_GRAFICO)
    imprimir_resumo_por_fase(tempos, predicoes_antigo, predicoes_novo)
