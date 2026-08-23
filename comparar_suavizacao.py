import argparse
import os
import sys

import cv2
import numpy as np
import matplotlib
matplotlib.use('Agg')  # sem display (roda direto no terminal/headless), so salva o PNG
import matplotlib.pyplot as plt

DIRETORIO_ATUAL = os.path.dirname(os.path.abspath(__file__))
sys.path.append(DIRETORIO_ATUAL)

# Reusa o pipeline de producao de verdade (mesmo modelo, mesma ROI de
# config.py, mesmo buffer/janela de suavizacao) em vez de reimplementar a
# logica aqui -- assim a comparacao reflete exatamente o que api_teste.py
# faz, sem risco de o script de teste desalinhar do pipeline real com o tempo.
import validar_sistema as vs

CAMINHO_VIDEO = os.path.join(DIRETORIO_ATUAL, 'torra_v2.mp4')
CAMINHO_SAIDA_GRAFICO = os.path.join(DIRETORIO_ATUAL, 'comparacao_suavizacao.png')

# A cada quantos frames uma leitura e feita (passo configuravel via --passo).
PASSO_FRAMES_PADRAO = 10

# Timestamps de ancora ja conhecidos (marcacao manual das 4 fases no video de
# teste), mesma referencia usada em comparar_modelos.py.
ANCORAS_FASES = [
    ('Cru', 1.18),
    ('Clara', 85.9),
    ('Media', 111.5),
    ('Escura', 153.5),
]


def coletar_bruto_vs_suavizado(caminho_video, passo_frames):
    """Percorre o video amostrando 1 a cada `passo_frames` frames, chamando
    a MESMA funcao que a API usa (vs.analisar_para_api). O valor bruto de
    cada leitura e o ultimo elemento que acabou de entrar no buffer de
    suavizacao (vs.buffer_agtron) -- analisar_para_api sempre faz o append
    antes de calcular a media, entao buffer_agtron[-1] apos a chamada e
    exatamente o valor bruto usado naquela leitura."""
    captura = cv2.VideoCapture(caminho_video)
    if not captura.isOpened():
        print(f"[ERRO] Nao foi possivel abrir o video: '{caminho_video}'")
        sys.exit(1)

    fps = captura.get(cv2.CAP_PROP_FPS) or 30.0
    total_frames = int(captura.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"[VIDEO] '{caminho_video}': {total_frames} frames a {fps:.1f} FPS "
          f"({total_frames / fps:.1f}s), amostrando 1 a cada {passo_frames} frames.")
    print(f"[SUAVIZACAO] Janela: {vs.TAMANHO_JANELA_SUAVIZACAO} leituras (vs.TAMANHO_JANELA_SUAVIZACAO).\n")

    # Buffer limpo pra esta execucao, independente do que rodou antes neste
    # processo -- mesmo comportamento de "comeca vazio" que o servidor real
    # tem a cada restart (ver item 5 da suavizacao em validar_sistema.py).
    vs.buffer_agtron.clear()

    tempos, brutos, suavizados = [], [], []
    indice_frame = 0

    while True:
        sucesso, frame = captura.read()
        if not sucesso:
            break

        if indice_frame % passo_frames == 0:
            agtron_suavizado, _classe, _desvio = vs.analisar_para_api(frame)

            if agtron_suavizado > 0:
                agtron_bruto = vs.buffer_agtron[-1]
                tempos.append(indice_frame / fps)
                brutos.append(agtron_bruto)
                suavizados.append(agtron_suavizado)

        indice_frame += 1

    captura.release()
    print(f"\n[VIDEO] Concluido: {len(tempos)} amostras coletadas.")
    return tempos, brutos, suavizados


def gerar_grafico(tempos, brutos, suavizados, caminho_saida):
    todos_valores = brutos + suavizados

    # Mesmo ajuste dinamico de eixo Y usado em comparar_modelos.py: prender
    # ylim em (0,100) cortava picos de ruido do bruto rente a borda (ficava
    # com cara de bug visual). O eixo se ajusta aos dados reais, com uma
    # faixa sombreada marcando 0-100 como referencia da escala Agtron valida.
    limite_superior = max(100, max(todos_valores)) + 5
    limite_inferior = min(0, min(todos_valores)) - 5

    plt.figure(figsize=(12, 6))
    plt.axhspan(0, 100, color='#6B8E4E', alpha=0.07, zorder=0, label='Faixa Agtron valida (0-100)')
    plt.plot(tempos, brutos, label='Bruto (frame a frame, sem suavizacao)',
              color='#A8977E', linewidth=1.1, alpha=0.85)
    plt.plot(tempos, suavizados, label=f'Suavizado (media movel, janela={vs.TAMANHO_JANELA_SUAVIZACAO})',
              color='#C1440E', linewidth=2.0)

    for nome_fase, tempo_ancora in ANCORAS_FASES:
        plt.axvline(x=tempo_ancora, color='gray', linestyle='--', linewidth=0.8, alpha=0.6)
        plt.text(tempo_ancora, limite_superior - 1, nome_fase, rotation=90, fontsize=8, color='gray',
                  ha='right', va='top')

    plt.xlabel('Tempo (s)')
    plt.ylabel('Agtron')
    plt.ylim(limite_inferior, limite_superior)
    plt.title('Efeito da suavizacao por media movel no Agtron (bruto vs. suavizado)')
    plt.legend(loc='lower left')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(caminho_saida, dpi=150)
    print(f"[GRAFICO] Salvo em '{caminho_saida}'")


def imprimir_resumo_por_fase(tempos, brutos, suavizados):
    """Mesmo formato de comparar_modelos.py: pra cada timestamp de ancora
    conhecido, acha a amostra coletada mais proxima e imprime bruto vs
    suavizado nesse ponto."""
    tempos_np = np.array(tempos)

    print("\n--- RESUMO POR FASE (ancoras conhecidas) ---")
    print(f"{'Fase':<8} {'t alvo':>8} {'t amostrado':>12} {'Bruto':>10} {'Suavizado':>10} {'Diferenca':>11}")
    for nome_fase, tempo_alvo in ANCORAS_FASES:
        indice_mais_proximo = int(np.argmin(np.abs(tempos_np - tempo_alvo)))
        t_amostrado = tempos[indice_mais_proximo]
        bruto = brutos[indice_mais_proximo]
        suavizado = suavizados[indice_mais_proximo]
        print(f"{nome_fase:<8} {tempo_alvo:>7.2f}s {t_amostrado:>11.2f}s "
              f"{bruto:>10.2f} {suavizado:>10.2f} {suavizado - bruto:>+11.2f}")


def imprimir_estatisticas_de_ruido(brutos, suavizados):
    """Quantifica o quanto a suavizacao realmente reduziu o ruido, alem do
    resumo pontual por fase: desvio padrao da serie inteira e a maior
    variacao entre duas amostras CONSECUTIVAS (proxy direto pro tipo de pico
    isolado que motivou a suavizacao, ex: queda a 52 / salto a 124)."""
    brutos_np = np.array(brutos)
    suavizados_np = np.array(suavizados)

    salto_maximo_bruto = np.max(np.abs(np.diff(brutos_np)))
    salto_maximo_suavizado = np.max(np.abs(np.diff(suavizados_np)))

    print("\n--- RUIDO GERAL (serie completa) ---")
    print(f"Desvio padrao bruto:          {np.std(brutos_np):>6.2f}")
    print(f"Desvio padrao suavizado:      {np.std(suavizados_np):>6.2f}")
    print(f"Maior salto entre 2 amostras consecutivas:")
    print(f"  bruto:      {salto_maximo_bruto:>6.2f}")
    print(f"  suavizado:  {salto_maximo_suavizado:>6.2f}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Compara o Agtron bruto (frame a frame) com o Agtron suavizado '
                    '(media movel de validar_sistema.py) sobre o mesmo video de teste, '
                    'usando o pipeline de producao de verdade (mesmo modelo/ROI/buffer).'
    )
    parser.add_argument(
        '--passo', type=int, default=PASSO_FRAMES_PADRAO,
        help=f'Analisa 1 a cada N frames do video (padrao: {PASSO_FRAMES_PADRAO}).',
    )
    args = parser.parse_args()

    tempos, brutos, suavizados = coletar_bruto_vs_suavizado(CAMINHO_VIDEO, args.passo)

    gerar_grafico(tempos, brutos, suavizados, CAMINHO_SAIDA_GRAFICO)
    imprimir_resumo_por_fase(tempos, brutos, suavizados)
    imprimir_estatisticas_de_ruido(brutos, suavizados)
