import os
import sys
#Garante que a GPU não sera chamada
os.environ['CUDA_VISIBLE_DEVICES'] = ''


#Garante os caminhos corretos do repositório
sys.path.append(os.getcwd())

import cv2
import time
import numpy as np
from collections import Counter
import re
from cnn.clip_classifier import CLIPClassifier

try:
    from processamento_imagem.preprocess import preprocessar_grao_para_clip
    from yolo.detectar_graos import YOLOObjectDetector
    from cnn.clip_classifier import CLIPClassifier
except ModuleNotFoundError as e:
    print(f"ERRO DE IMPORTAÇÃO: {e}")
    sys.exit(1)

def analisar_distribuicao_torra(lista_classificacoes):
    if not lista_classificacoes:
        return {"classe_dominante": "N/A", "media_agtron": 0.0, "desvio_padrao": 0.0}
    
    valores_numericos = [int(n) for c in lista_classificacoes for n in re.findall(r'\d+', c)]
    classes_validas = [c for c in lista_classificacoes if "incerto" not in c and "erro" not in c]

    if not valores_numericos:
        return {"classe_dominante": "N/A", "media_agtron": 0.0, "desvio_padrao": 0.0}
    
    contagem = Counter(classes_validas)
    classe_dominante = contagem.most_common(1)[0][0] if contagem else "N/A"
    
    return {
        "classe_dominante": classe_dominante,
        "media_agtron": round(np.mean(valores_numericos), 2),
        "desvio_padrao": round(np.std(valores_numericos), 2)
    }

def main():
    print("--- INICIANDO ANÁLISE EM LOTE DE IMAGENS ---")

    PASTA_IMAGENS_INPUT = "golden_test_set"

    if not os.path.isdir(PASTA_IMAGENS_INPUT):
        print(f"ERRO: Pasta de entrada '{PASTA_IMAGENS_INPUT}' não encontrada.")
        print("Por favor, crie esta pasta e coloque suas imagens de teste dentro dela.")
        return

    print("\nInicializando modelos...")
    try:
        yolo_detector = YOLOObjectDetector()
        cnn_classifier = CLIPClassifier()
    except Exception as e:
        print(f"ERRO: Falha ao carregar os modelos. Verifique seu config.py e .env.local. Detalhe: {e}")
        return
        
    arquivos_a_processar = [f for f in os.listdir(PASTA_IMAGENS_INPUT) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    
    if not arquivos_a_processar:
        print(f"ERRO: Nenhuma imagem encontrada em '{PASTA_IMAGENS_INPUT}'.")
        return

    start_time = time.time()

    for idx, filename in enumerate(sorted(arquivos_a_processar), 1):
        caminho_imagem = os.path.join(PASTA_IMAGENS_INPUT, filename)
        print(f"\n---> Processando {idx}/{len(arquivos_a_processar)}: {filename}")

        frame = cv2.imread(caminho_imagem)
        if frame is None:
            print("   ERRO: Falha ao ler a imagem.")
            continue
            
        frame_com_detecoes, graos_recortados = yolo_detector.detectar_e_recortar(frame)
        
        classificacoes_cnn = []
        print(f"   - {len(graos_recortados)} grãos detectados. Classificando via API...")
        if graos_recortados:
            for i, grao_crop in enumerate(graos_recortados, 1):
                classificacao, confianca = cnn_classifier.classificar(grao_crop)
                classificacoes_cnn.append(classificacao)
                print(f"     - Grão {i}: Classe = {classificacao}, Confiança = {confianca:.2f}")

        estatisticas = analisar_distribuicao_torra(classificacoes_cnn)
        
        print("\n   --- Análise da Amostra ---")
        print(f"   -> Classe Dominante: {estatisticas['classe_dominante']}")
        print(f"   -> Média Agtron da Amostra: {estatisticas['media_agtron']:.2f}")
        print(f"   -> Uniformidade (Desvio Padrão): {estatisticas['desvio_padrao']:.2f}")

    end_time = time.time()
    
    print(f"\n--- ANÁLISE EM LOTE CONCLUÍDA em {end_time - start_time:.2f} segundos ---")


if __name__ == '__main__':
    main()