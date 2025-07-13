import os
import cv2
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Importa as suas classes e funções customizadas
try:
    from yolo.detectar_graos import YOLOObjectDetector
    from processamento_imagem.preprocess import aplicar_crop_customizado
except ModuleNotFoundError:
    print("ERRO DE IMPORTAÇÃO: Não foi possível encontrar os módulos necessários.")
    print("Verifique se os arquivos 'yolo/detectar_graos.py' e 'processamento_imagem/preprocess.py' existem.")
    print("Execute o script a partir da raiz do projeto, como: python -m test.yolo.testar_yolo")
    sys.exit(1)


def testar_pipeline_yolo():
    print("--- Iniciando Teste do Pipeline YOLO com Arquivos Locais ---")

    # 1. Inicializa o detector de objetos uma única vez.
    try:
        detector = YOLOObjectDetector()
    except Exception as e:
        print(f"Erro ao inicializar o detector: {e}")
        return

    # 2. Define os diretórios de entrada e saída.
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_dir = os.path.join(script_dir, 'imagens_input')
    output_dir_geral = os.path.join(script_dir, 'imagens_output')

    # Cria o diretório de saída principal se não existir.
    os.makedirs(output_dir_geral, exist_ok=True)

    if not os.path.isdir(input_dir) or not os.listdir(input_dir):
        print(f"\nERRO: Pasta de imagens de teste '{input_dir}' não encontrada ou está vazia.")
        print("Por favor, crie a pasta e coloque algumas imagens .jpg ou .png para testar.")
        return

    print(f"\nProcurando imagens em: {input_dir}")
    print(f"Salvando resultados em: {output_dir_geral}")

    # 3. Itera sobre todos os arquivos na pasta de entrada.
    for filename in os.listdir(input_dir):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            image_path = os.path.join(input_dir, filename)
            print(f"\n-> Processando: {filename}")

            # ETAPA 1: Carrega a imagem do arquivo
            frame = cv2.imread(image_path)
            if frame is None:
                print(f"   Erro ao carregar a imagem.")
                continue

            # ETAPA 2: Passa a imagem pelo seu pré-processamento (crop)
            frame_recortado_area = aplicar_crop_customizado(frame)

            if frame_recortado_area is None or frame_recortado_area.size == 0:
                print("   Erro ou recorte resultou em imagem vazia.")
                continue
            
            # ETAPA 3: Passa a imagem JÁ RECORTADA para o detector YOLO
            frame_resultado, graos_recortados = detector.detectar_e_recortar(frame_recortado_area)

            # ETAPA 4: Salva os resultados
            output_image_path = os.path.join(output_dir_geral, filename)
            cv2.imwrite(output_image_path, frame_resultado)

            print(f"   Foram detectados {len(graos_recortados)} grãos.")
            print(f"   Imagem com detecções salva em: {output_image_path}")
            
            if graos_recortados:
                nome_base, _ = os.path.splitext(filename)
                output_dir_recortes = os.path.join(output_dir_geral, nome_base + "_recortes")
                os.makedirs(output_dir_recortes, exist_ok=True)
                for i, recorte in enumerate(graos_recortados):
                    recorte_path = os.path.join(output_dir_recortes, f"grao_{i+1}.png")
                    cv2.imwrite(recorte_path, recorte)
                print(f"   Recortes individuais salvos em: {output_dir_recortes}")

    print("\n--- Teste Concluído ---")


if __name__ == '__main__':
    testar_pipeline_yolo()