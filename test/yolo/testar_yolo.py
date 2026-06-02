import os
import cv2
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Importa as classes e funções customizadas

from yolo.detectar_graos import YOLOObjectDetector

def testar_pipeline_yolo():

    # 1. Define o detector YOLO
    detector = YOLOObjectDetector()

    # 2. Define os diretórios de entrada e saída.
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_dir = os.path.join(script_dir, 'imagens_input')
    output_dir_geral = os.path.join(script_dir, 'imagens_output')

    # Cria o diretório de saída principal se não existir.
    os.makedirs(output_dir_geral, exist_ok=True)

    print(f"\nProcurando imagens em: {input_dir}")
    print(f"Salvando resultados em: {output_dir_geral}")

    # 3. Itera sobre todos os arquivos na pasta de entrada.
    for filename in os.listdir(input_dir):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            image_path = os.path.join(input_dir, filename)
            print(f"\n-> Processando: {filename}")

            # ETAPA 1: Carrega a imagem do arquivo
            frame = cv2.imread(image_path)

            # ETAPA 2: Passa a imagem pelo seu pré-processamento (crop)
            # Removido: frame_recortado_area = aplicar_crop_customizado(frame)
            
            # ETAPA 3: Passa a imagem para o detector YOLO
            # Alterado para usar 'frame' diretamente
            frame_resultado, graos_recortados = detector.detectar_e_recortar(frame)

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