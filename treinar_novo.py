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


def treinar(usar_interpolado):
    if usar_interpolado:
        print(f"Carregando dataset interpolado de '{CSV_INTERPOLADO}'...")
        print("LEMBRETE: os alvos 'agtron_interpolado' sao ESTIMATIVAS por interpolacao")
        print("temporal linear, nao medicoes reais de Agtron. Ver gerar_dataset_interpolado.py.")
        X_treino, y_treino = carregar_dataset_interpolado(CSV_INTERPOLADO)
        nome_saida = 'modelo_agtron_linear_interpolado.pkl'
        print(f"Treinando o modelo Linear com {len(X_treino)} frames interpolados...")
    else:
        X_treino, y_treino = X_TREINO_4_PONTOS, Y_TREINO_4_PONTOS
        nome_saida = 'modelo_agtron_linear.pkl'
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
    args = parser.parse_args()
    treinar(usar_interpolado=args.interpolado)
