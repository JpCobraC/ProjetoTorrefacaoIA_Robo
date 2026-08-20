import csv
import os

# ============================================================================
# AVISO IMPORTANTE PARA A DOCUMENTACAO DO PROJETO:
#
# Este script gera valores de Agtron por INTERPOLACAO TEMPORAL LINEAR entre
# os poucos frames marcados manualmente no dataset_real.csv (fases 1=Cru,
# 2=Clara, 3=Media, 4=Escura). Nao temos cartela de referencia nem
# colorimetro fisico, entao esses valores NAO SAO medicoes reais de Agtron.
#
# A premissa assumida e que o escurecimento do grao ao longo do tempo entre
# duas marcacoes consecutivas e aproximadamente linear -- o que e uma
# simplificacao. Na pratica, a torra pode acelerar/desacelerar (ex: reacao
# de Maillard, primeiro/segundo crack), entao os valores intermediarios sao
# ESTIMATIVAS, nao ground truth. Use com essa ressalva ao treinar/avaliar
# modelos e ao reportar resultados.
# ============================================================================

CSV_ENTRADA = 'dataset_real.csv'
CSV_SAIDA = 'dataset_interpolado.csv'

# Valores-alvo de Agtron assumidos para cada fase marcada manualmente
AGTRON_ALVO = {
    'Cru': 95.0,
    'Clara': 75.0,
    'Media': 55.0,
    'Escura': 35.0,
}


def ler_dataset(caminho):
    """Le o dataset_real.csv e retorna a lista de linhas (dicts) na ordem original."""
    with open(caminho, newline='', encoding='utf-8') as arquivo:
        leitor = csv.DictReader(arquivo)
        return list(leitor)


def identificar_ancoras(linhas):
    """Percorre as linhas em ordem cronologica e identifica o timestamp em que
    cada fase foi marcada pela primeira vez (o instante em que o operador
    apertou a tecla), usando esse instante como ponto-ancora para o Agtron
    alvo daquela fase."""
    ancoras = []
    fases_vistas = set()

    for linha in linhas:
        fase = linha['fase'].strip() if linha['fase'] else ''
        if fase and fase not in fases_vistas:
            fases_vistas.add(fase)
            timestamp = float(linha['timestamp'])
            agtron = AGTRON_ALVO.get(fase)
            if agtron is None:
                print(f"Aviso: fase desconhecida '{fase}' ignorada (sem Agtron alvo definido).")
                continue
            ancoras.append((timestamp, agtron, fase))

    # Garante que as ancoras estao ordenadas por tempo (deveriam estar, ja
    # que o CSV e cronologico, mas isso protege contra dados fora de ordem)
    ancoras.sort(key=lambda a: a[0])
    return ancoras


def interpolar_agtron(timestamp, ancoras):
    """Calcula o Agtron estimado para um timestamp qualquer por interpolacao
    linear entre os pontos-ancora vizinhos. Fora do intervalo marcado, usa o
    valor da ancora mais proxima (sem extrapolar)."""
    # Antes da primeira marcacao: usa o Agtron da primeira ancora
    if timestamp <= ancoras[0][0]:
        return ancoras[0][1]

    # Depois da ultima marcacao: usa o Agtron da ultima ancora
    if timestamp >= ancoras[-1][0]:
        return ancoras[-1][1]

    # Encontra o par de ancoras que envolve o timestamp e interpola
    for i in range(len(ancoras) - 1):
        ts_ini, agtron_ini, _ = ancoras[i]
        ts_fim, agtron_fim, _ = ancoras[i + 1]
        if ts_ini <= timestamp <= ts_fim:
            fracao = (timestamp - ts_ini) / (ts_fim - ts_ini)
            return agtron_ini + fracao * (agtron_fim - agtron_ini)

    # Nao deveria chegar aqui, mas por seguranca retorna a ancora mais proxima
    return ancoras[-1][1]


def gerar_dataset_interpolado():
    if not os.path.exists(CSV_ENTRADA):
        print(f"Erro: '{CSV_ENTRADA}' nao encontrado nesta pasta. Rode coletar_dataset_real.py antes.")
        return

    print("=" * 70)
    print("ATENCAO: os valores 'agtron_interpolado' gerados abaixo sao ESTIMATIVAS")
    print("por interpolacao temporal linear entre as poucas marcacoes manuais de")
    print("fase (1=Cru, 2=Clara, 3=Media, 4=Escura). NAO sao medicoes reais de")
    print("Agtron (nao houve cartela de referencia nem colorimetro fisico).")
    print("Assume-se escurecimento aproximadamente linear no tempo entre marcacoes.")
    print("=" * 70)

    linhas = ler_dataset(CSV_ENTRADA)
    ancoras = identificar_ancoras(linhas)

    if not ancoras:
        print("Erro: nenhuma fase marcada foi encontrada no dataset. Nada a interpolar.")
        return

    print("\nPontos-ancora encontrados (timestamp da marcacao -> Agtron alvo):")
    for ts, agtron, fase in ancoras:
        print(f"  {fase:<7} t={ts:.3f}s -> Agtron={agtron:.1f}")

    linhas_saida = []
    for linha in linhas:
        timestamp = float(linha['timestamp'])
        agtron_estimado = interpolar_agtron(timestamp, ancoras)
        linhas_saida.append({
            'frame': linha['frame'],
            'timestamp': linha['timestamp'],
            'L': linha['L'],
            'a': linha['a'],
            'b': linha['b'],
            'agtron_interpolado': round(agtron_estimado, 3),
        })

    with open(CSV_SAIDA, 'w', newline='', encoding='utf-8') as arquivo_csv:
        campos = ['frame', 'timestamp', 'L', 'a', 'b', 'agtron_interpolado']
        escritor = csv.DictWriter(arquivo_csv, fieldnames=campos)
        escritor.writeheader()
        escritor.writerows(linhas_saida)

    print(f"\nDataset interpolado salvo em '{CSV_SAIDA}' com {len(linhas_saida)} frames.")
    print("Lembre-se: use estes valores como estimativas, nao como ground truth real.")


if __name__ == '__main__':
    gerar_dataset_interpolado()
