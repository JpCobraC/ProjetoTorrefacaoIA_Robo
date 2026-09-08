import argparse
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
#
# SUPORTE A MULTIPLOS VIDEOS: quando --inputs recebe mais de um CSV, cada
# video e interpolado SEPARADAMENTE com seus proprios pontos-ancora de tempo
# (o timestamp de cada video comeca do zero e nao tem relacao com o outro).
# Os frames resultantes de cada video sao entao concatenados no CSV final,
# marcados com a coluna 'origem_video' (v1 para o 1o arquivo em --inputs, v2
# para o 2o, etc.) para permitir filtrar por video depois.
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
    """Le um dataset_real*.csv e retorna a lista de linhas (dicts) na ordem original."""
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


def interpolar_video(caminho, origem_video):
    """Le um dataset_real*.csv de UM video, identifica suas proprias ancoras
    e retorna as linhas interpoladas ja marcadas com a coluna origem_video.
    Retorna lista vazia (com aviso) se o video nao tiver nenhuma fase marcada."""
    linhas = ler_dataset(caminho)
    ancoras = identificar_ancoras(linhas)

    if not ancoras:
        print(f"Aviso: '{caminho}' nao tem nenhuma fase marcada. Ignorando este video.")
        return []

    print(f"\nPontos-ancora de '{caminho}' ({origem_video}):")
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
            'origem_video': origem_video,
        })

    return linhas_saida


def gerar_dataset_interpolado(caminhos_entrada, caminho_saida):
    print("=" * 70)
    print("ATENCAO: os valores 'agtron_interpolado' gerados abaixo sao ESTIMATIVAS")
    print("por interpolacao temporal linear entre as poucas marcacoes manuais de")
    print("fase (1=Cru, 2=Clara, 3=Media, 4=Escura). NAO sao medicoes reais de")
    print("Agtron (nao houve cartela de referencia nem colorimetro fisico).")
    print("Assume-se escurecimento aproximadamente linear no tempo entre marcacoes.")
    print("Cada video em --inputs e interpolado SEPARADAMENTE com suas proprias")
    print("ancoras de tempo (timestamps nao sao comparaveis entre videos).")
    print("=" * 70)

    linhas_finais = []
    for indice, caminho in enumerate(caminhos_entrada, start=1):
        if not os.path.exists(caminho):
            print(f"Erro: '{caminho}' nao encontrado nesta pasta. Pulando.")
            continue
        origem_video = f'v{indice}'
        linhas_finais.extend(interpolar_video(caminho, origem_video))

    if not linhas_finais:
        print("Erro: nenhum video produziu linhas interpoladas. Nada a salvar.")
        return

    with open(caminho_saida, 'w', newline='', encoding='utf-8') as arquivo_csv:
        campos = ['frame', 'timestamp', 'L', 'a', 'b', 'agtron_interpolado', 'origem_video']
        escritor = csv.DictWriter(arquivo_csv, fieldnames=campos)
        escritor.writeheader()
        escritor.writerows(linhas_finais)

    print(f"\nDataset interpolado salvo em '{caminho_saida}' com {len(linhas_finais)} frames no total.")
    for origem in sorted(set(linha['origem_video'] for linha in linhas_finais)):
        n = sum(1 for linha in linhas_finais if linha['origem_video'] == origem)
        print(f"  {origem}: {n} frames")
    print("Lembre-se: use estes valores como estimativas, nao como ground truth real.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=(
            'Gera dataset_interpolado.csv por interpolacao temporal linear entre '
            'marcacoes manuais de fase. Aceita um ou mais CSVs de entrada (um por '
            'video), cada um interpolado com suas proprias ancoras de tempo.'
        )
    )
    parser.add_argument(
        '--inputs',
        nargs='+',
        default=[CSV_ENTRADA],
        help=(
            "Um ou mais CSVs de entrada, na ordem desejada (ex: dataset_real.csv "
            "dataset_real_v2.csv). Cada arquivo vira 'v1', 'v2', ... na coluna "
            "origem_video, conforme a ordem informada. Padrao: dataset_real.csv."
        ),
    )
    parser.add_argument(
        '--saida',
        default=CSV_SAIDA,
        help=f'Caminho do CSV combinado de saida (padrao: {CSV_SAIDA}).',
    )
    args = parser.parse_args()
    gerar_dataset_interpolado(args.inputs, args.saida)
