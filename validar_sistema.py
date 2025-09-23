import os
import cv2
import numpy as np
from yolo.detectar_graos import YOLOObjectDetector
from cnn.classificar_torra import CNNClassifier
from processamento_imagem.preprocess import preprocessar_grao_para_cnn

# Configurações
PASTA_IMAGENS_INPUT = os.path.join(os.getcwd(), "test", "yolo", "imagens_input")
PASTA_OUTPUT = os.path.join(os.getcwd(), "teste_completo_output")
CNN_CLASSES = ['25', '35', '45', '55', '65', '75', '85', '95', 'raw']
CNN_CONFIDENCE_THRESHOLD = 0.60

def analisar_distribuicao_torra(lista_classificacoes):
    from collections import Counter
    import re
    if not lista_classificacoes:
        return {"classe_dominante": "N/A", "media_agtron": 0.0, "desvio_padrao": 0.0, "contagem_classes": {}}
    valores_numericos, classes_validas_para_moda = [], []
    for classificacao in lista_classificacoes:
        numeros = re.findall(r'\d+', classificacao)
        if numeros:
            valores_numericos.append(int(numeros[0]))
            if "incerto" not in classificacao:
                classes_validas_para_moda.append(classificacao)
    if not valores_numericos:
        return {"classe_dominante": "N/A", "media_agtron": 0.0, "desvio_padrao": 0.0, "contagem_classes": dict(Counter(lista_classificacoes))}
    contagem = Counter(classes_validas_para_moda)
    classe_dominante = contagem.most_common(1)[0][0] if contagem else "N/A"
    media_agtron = np.mean(valores_numericos)
    desvio_padrao = np.std(valores_numericos)
    contagem_total = dict(Counter(lista_classificacoes))
    return {
        "classe_dominante": classe_dominante,
        "media_agtron": round(media_agtron, 2),
        "desvio_padrao": round(desvio_padrao, 2),
        "contagem_classes": contagem_total
    }

def main():
    # Limpa/cria a pasta de saída
    import shutil
    if os.path.exists(PASTA_OUTPUT):
        shutil.rmtree(PASTA_OUTPUT)
    os.makedirs(PASTA_OUTPUT)
    print(f"Diretório de saída '{PASTA_OUTPUT}' limpo e pronto.")

    arquivos = [f for f in os.listdir(PASTA_IMAGENS_INPUT) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    if not arquivos:
        print("Nenhuma imagem de teste encontrada.")
        return

    print("Inicializando modelos...")
    yolo_detector = YOLOObjectDetector()
    cnn_classifier = CNNClassifier()

    for idx, filename in enumerate(arquivos, 1):
        caminho = os.path.join(PASTA_IMAGENS_INPUT, filename)
        img = cv2.imread(caminho)
        if img is None:
            print(f"Falha ao carregar imagem: {filename}")
            continue

        print(f"\n---> Processando imagem {idx}/{len(arquivos)}: {filename}")

        # Detecção YOLO e recorte dos grãos
        try:
            frame_com_detecoes, graos_recortados = yolo_detector.detectar_e_recortar(img)
        except Exception as e:
            print(f"Erro na detecção YOLO: {e}")
            continue

        print(f"  - Grãos detectados: {len(graos_recortados)}")

        classificacoes_cnn = []
        for i, grao_crop in enumerate(graos_recortados):
            input_cnn = preprocessar_grao_para_cnn(grao_crop)
            if input_cnn is not None:
                try:
                    classificacao, confianca = cnn_classifier.classificar(input_cnn)
                except Exception as e:
                    print(f"    Erro na classificação CNN para grão {i+1}: {e}")
                    classificacao, confianca = "erro", 0.0
                if confianca < CNN_CONFIDENCE_THRESHOLD:
                    classificacao = f"incerto ({classificacao})"
                classificacoes_cnn.append(classificacao)
            else:
                classificacoes_cnn.append("erro_preprocessamento")

        # Análise estatística
        estatisticas = analisar_distribuicao_torra(classificacoes_cnn)
        print("  - Análise Estatística:")
        print(f"    - Classe Dominante: {estatisticas['classe_dominante']}")
        print(f"    - Média Agtron: {estatisticas['media_agtron']}")
        print(f"    - Uniformidade (Desvio Padrão): {estatisticas['desvio_padrao']}")

        # Salva a imagem com detecções
        nome_base = os.path.splitext(filename)[0]
        output_image_path = os.path.join(PASTA_OUTPUT, nome_base + "_resultado.jpg")
        cv2.imwrite(output_image_path, frame_com_detecoes)

        # Salva os recortes individuais
        output_dir_recortes = os.path.join(PASTA_OUTPUT, nome_base + "_recortes")
        os.makedirs(output_dir_recortes, exist_ok=True)
        for i, recorte in enumerate(graos_recortados):
            cv2.imwrite(os.path.join(output_dir_recortes, f"grao_{i+1}_{classificacoes_cnn[i].replace(' ','')}.png"), recorte)
        print(f"  - Imagem de resultado e {len(graos_recortados)} recortes salvos.")

if __name__ == "__main__":
    main()