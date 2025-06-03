import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config

def guia_treinamento_yolo():
    print("--- Guia para Treinamento YOLO (ex: com YOLOv5/YOLOv8) ---")
    print("\nEste script NÃO executa o treinamento YOLO diretamente.")
    print("Ele serve como um guia dos passos que você normalmente seguiria.")
    print("O treinamento YOLO é intensivo e melhor realizado no Google Colab com GPU.")

    print("\n1. Coleta e Anotação de Dados:")
    print(f"  - Colete imagens dos seus grãos. Armazene-as em: '{config.YOLO_TRAIN_IMAGES_PATH}'")
    print(f"  - Anote essas imagens (desenhe bounding boxes ao redor dos grãos).")
    print(f"  - Use ferramentas como 'LabelImg', 'Roboflow', ou 'CVAT'.")
    print(f"  - Exporte as anotações no formato YOLO (arquivos .txt, um para cada imagem, com o mesmo nome).")
    print(f"  - Armazene os arquivos de anotação em: '{config.YOLO_TRAIN_LABELS_PATH}'")
    print(f"  - Certifique-se de que as classes no arquivo de anotação (geralmente 0 para a primeira classe) correspondem ao que o modelo espera.")

    print("\n2. Escolha um Framework YOLO e Ambiente:")
    print(f"  - Frameworks Populares: YOLOv5, YOLOv8 (da Ultralytics). São baseados em PyTorch.")
    print(f"  - Ambiente: Google Colab é altamente recomendado devido ao acesso gratuito a GPUs.")

    print("\n3. Preparação no Ambiente de Treinamento (ex: Colab com YOLOv5):")
    print(f"  a. Clone o repositório do YOLO escolhido (ex: `git clone https://github.com/ultralytics/yolov5`)")
    print(f"  b. Instale as dependências (`pip install -r yolov5/requirements.txt`)")
    print(f"  c. Faça upload do seu dataset (imagens e labels) para o ambiente Colab, ou monte o Google Drive.")
    print(f"  d. Crie um arquivo de configuração do dataset (ex: `data.yaml`) que aponte para seus dados de treino e validação, e defina o número de classes e nomes das classes.")
    print(f"     Exemplo de `custom_dataset.yaml` para YOLOv5 (assumindo 1 classe: 'grao'):")
    print(f"       train: ../dataset/train/yolo_data/images  # ou caminho completo no Colab")
    print(f"       val: ../dataset/validation/yolo_data/images # Crie uma pasta de validação!")
    print(f"       nc: 1")
    print(f"       names: ['grao']")

    print("\n4. Treinamento:")
    print(f"  - Navegue para a pasta do YOLO (ex: `cd yolov5`)")
    print(f"  - Execute o script de treinamento. Exemplo para YOLOv5:")
    print(f"    `python train.py --img {config.YOLO_INPUT_SIZE[0]} --batch {config.TRAIN_BATCH_SIZE} --epochs {config.TRAIN_EPOCHS_YOLO} --data custom_dataset.yaml --weights yolov5s.pt`")
    print(f"    (yolov5s.pt são pesos pré-treinados; o modelo fará fine-tuning)")
    print(f"  - Monitore o treinamento (perda, mAP). Os resultados geralmente são salvos em uma pasta como `runs/train/expX`.")

    print("\n5. Exportação para TFLite:")
    print(f"  - Após o treinamento, use o script de exportação do framework YOLO para converter o modelo treinado (ex: `best.pt`) para TFLite.")
    print(f"  - Exemplo para YOLOv5:")
    print(f"    `python export.py --weights runs/train/expX/weights/best.pt --include tflite --img {config.YOLO_INPUT_SIZE[0]}`")
    print(f"  - Isso deve gerar um arquivo como `best.tflite` ou `best-fp16.tflite`.")

    print("\n6. Uso no Raspberry Pi:")
    print(f"  - Copie o arquivo `.tflite` gerado para a pasta '{config.MODELS_DIR}' no seu Raspberry Pi.")
    print(f"  - Atualize `config.YOLO_MODEL_FILENAME` com o nome do seu arquivo .tflite.")
    print(f"  - Implemente a lógica de pós-processamento em `yolo/detectar_graos.py` para interpretar a saída do seu modelo TFLite específico.")

    print("\nBoa sorte com o treinamento!")

if __name__ == '__main__':
    guia_treinamento_yolo()