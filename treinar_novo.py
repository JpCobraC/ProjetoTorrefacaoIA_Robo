import argparse
import csv
import pickle
import numpy as np
from sklearn.linear_model import LinearRegression

# ATUALIZADO EM 2026-08-19: X_treino abaixo agora e dado REAL, coletado da nossa
# bancada (pipoqueira + ringlight, ROI ja calibrada e sem contaminacao do metal)
# via coletar_dataset_real.py. Nao e mais dado teorico/mock. Os valores Agtron em
# y_treino continuam sendo a referencia teorica da escala -- essa parte nao muda.

# 1. Dataset real de calibracao [L, a, b] (media por fase marcada manualmente)
X_TREINO_4_PONTOS = np.array([
    [171.71, 134.73, 133.78],  # Cru    (1517 frames)
    [149.27, 130.50, 125.16],  # Clara  (707 frames)
    [145.36, 122.39, 119.78],  # Media  (473 frames)
    [109.42, 118.96, 109.84],  # Escura (80 frames)
])

# Os valores Agtron correspondentes que queremos que a IA aprenda a prever
Y_TREINO_4_PONTOS = np.array([95.0, 75.0, 55.0, 35.0])

CSV_INTERPOLADO = 'dataset_interpolado.csv'

# R2 do modelo atual em producao (modelo_agtron_linear_interpolado.pkl),
# treinado so com o video 1. Usado para comparar explicitamente o resultado
# do retreinamento com os dois videos combinados.
R2_MODELO_ATUAL_EM_PRODUCAO = 0.8534


def carregar_dataset_interpolado(caminho):
    """Le o dataset_interpolado.csv (gerado por gerar_dataset_interpolado.py) e
    monta os arrays X (L, a, b) e y (agtron_interpolado) com TODAS as linhas."""
    X, y = [], []
    with open(caminho, newline='', encoding='utf-8') as arquivo:
        leitor = csv.DictReader(arquivo)
        for linha in leitor:
            X.append([float(linha['L']), float(linha['a']), float(linha['b'])])
            y.append(float(linha['agtron_interpolado']))
    return np.array(X), np.array(y)


def treinar(usar_interpolado, caminho_dataset=CSV_INTERPOLADO, nome_saida_custom=None):
    if usar_interpolado:
        print(f"Carregando dataset interpolado de '{caminho_dataset}'...")
        print("LEMBRETE: os alvos 'agtron_interpolado' sao ESTIMATIVAS por interpolacao")
        print("temporal linear, nao medicoes reais de Agtron. Ver gerar_dataset_interpolado.py.")
        X_treino, y_treino = carregar_dataset_interpolado(caminho_dataset)
        nome_saida = nome_saida_custom or 'modelo_agtron_linear_interpolado.pkl'
        print(f"Treinando o modelo Linear com {len(X_treino)} frames interpolados...")
    else:
        X_treino, y_treino = X_TREINO_4_PONTOS, Y_TREINO_4_PONTOS
        nome_saida = nome_saida_custom or 'modelo_agtron_linear.pkl'
        print("Treinando o modelo Linear com dados reais da bancada (4 pontos de calibracao)...")

    # 2. Treinando o Cerebro
    modelo = LinearRegression()
    modelo.fit(X_treino, y_treino)

    # 3. Avaliacao do ajuste aos dados de treino
    r2 = modelo.score(X_treino, y_treino)

    print("\n--- RESULTADO DO TREINAMENTO ---")
    print(f"Coeficientes (L, a, b): {modelo.coef_}")
    print(f"Intercepto: {modelo.intercept_:.4f}")
    print(f"R² (ajuste aos {len(X_treino)} pontos de treino): {r2:.4f}")

    # 4. Salvando o novo arquivo .pkl
    with open(nome_saida, 'wb') as f:
        pickle.dump(modelo, f)

    print(f"\nNovo '{nome_saida}' treinado e pronto para uso!")

    if usar_interpolado:
        diferenca = r2 - R2_MODELO_ATUAL_EM_PRODUCAO
        print("\n--- COMPARACAO COM O MODELO ATUAL EM PRODUCAO ---")
        print(f"R² modelo atual (so video 1): {R2_MODELO_ATUAL_EM_PRODUCAO:.4f}")
        print(f"R² deste treino:              {r2:.4f}")
        if abs(diferenca) < 0.005:
            print(f"Resultado: ficou praticamente igual (diferenca de {diferenca:+.4f}).")
        elif diferenca > 0:
            print(f"Resultado: MELHOROU em {diferenca:+.4f}.")
        else:
            print(f"Resultado: PIOROU em {diferenca:+.4f}.")

    return r2, nome_saida


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Treina o modelo de regressao linear para prever Agtron a partir de L, a, b.'
    )
    parser.add_argument(
        '--interpolado',
        action='store_true',
        help=(
            'Treina usando todas as linhas do dataset_interpolado.csv '
            '(estimativas por interpolacao temporal) em vez dos 4 pontos reais de calibracao.'
        ),
    )
    parser.add_argument(
        '--dataset',
        default=CSV_INTERPOLADO,
        help=f'Caminho do CSV interpolado de entrada, usado com --interpolado (padrao: {CSV_INTERPOLADO}).',
    )
    parser.add_argument(
        '--saida',
        default=None,
        help=(
            'Nome do arquivo .pkl de saida. Padrao: modelo_agtron_linear_interpolado.pkl '
            '(com --interpolado) ou modelo_agtron_linear.pkl (sem). Use para nao sobrescrever '
            'o modelo em producao, ex: modelo_agtron_linear_interpolado_v2.pkl.'
        ),
    )
    args = parser.parse_args()
    treinar(usar_interpolado=args.interpolado, caminho_dataset=args.dataset, nome_saida_custom=args.saida)
