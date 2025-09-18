import os
import sys
import cv2

# Como este script estará na raiz, ele encontrará as pastas 'yolo', 'cnn', etc. sem problemas.
# Se mesmo assim houver erro, a linha abaixo pode ser descomentada.
# sys.path.append(os.getcwd())

try:
    from processamento_imagem.preprocess import preprocessar_grao_para_cnn
    from yolo.detectar_graos import YOLOObjectDetector
    from cnn.classificar_torra import CNNClassifier
except ModuleNotFoundError as e:
    print(f"ERRO DE IMPORTAÇÃO: {e}")
    print("Verifique se a estrutura de pastas do projeto está correta e se você está executando o script da pasta raiz.")
    sys.exit(1)

def main():
    print("--- INICIANDO TESTE EM LOTE DO PIPELINE COMPLETO ---")
    
    # Define os caminhos a partir da pasta de trabalho atual (a raiz do projeto)
    # Esta é uma forma muito robusta de definir caminhos.
    project_root = os.getcwd()
    imagens_teste_dir = os.path.join(project_root, "test", "yolo", "imagens_input")

    if not os.path.isdir(imagens_teste_dir):
        print(f"ERRO: Pasta de imagens de teste não encontrada em: {imagens_teste_dir}")
        return

    arquivos = [f for f in os.listdir(imagens_teste_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    if not arquivos:
        print(f"ERRO: Nenhuma imagem de teste encontrada em '{imagens_teste_dir}'.")
        return

    print("Inicializando modelos...")
    try:
        yolo_detector = YOLOObjectDetector()
        cnn_classifier = CNNClassifier()
        print("Modelos carregados com sucesso.")
    except Exception as e:
        print(f"ERRO: Falha ao carregar os modelos. {e}")
        return

    imagens_processadas = 0
    total_graos_detectados = 0

    for filename in arquivos:
        caminho_imagem = os.path.join(imagens_teste_dir, filename)
        img = cv2.imread(caminho_imagem)
        if img is None:
            print(f"\nAVISO: Falha ao carregar imagem: {filename}")
            continue

        imagens_processadas += 1
        print(f"\nProcessando imagem {imagens_processadas}/{len(arquivos)}: {filename}")

        # Detecção YOLO
        try:
            _, graos_recortados = yolo_detector.detectar_e_recortar(img)
        except Exception as e:
            print(f"  ERRO na detecção YOLO: {e}")
            continue

        num_graos = len(graos_recortados)
        total_graos_detectados += num_graos
        print(f"  Grãos detectados: {num_graos}")

        # Classificação CNN
        for i, grao_crop in enumerate(graos_recortados):
            input_cnn = preprocessar_grao_para_cnn(grao_crop)
            if input_cnn is None:
                print(f"    - Grão {i+1}: Falha no pré-processamento para CNN.")
                continue
            try:
                classificacao, confianca = cnn_classifier.classificar(input_cnn)
                print(f"    - Grão {i+1}: Classe = {classificacao}, Confiança = {confianca:.2f}")
            except Exception as e:
                print(f"    - Grão {i+1}: ERRO na classificação CNN: {e}")
                continue
    
    print("\n" + "="*40)
    print("--- TESTE EM LOTE CONCLUÍDO ---")
    print(f"Resumo:")
    print(f"  - Imagens Processadas: {imagens_processadas}")
    print(f"  - Total de Grãos Detectados: {total_graos_detectados}")
    print("="*40)


if __name__ == "__main__":
    main()