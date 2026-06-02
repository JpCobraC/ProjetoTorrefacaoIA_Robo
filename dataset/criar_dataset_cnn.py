import os
import cv2
import sys
import shutil

# Garante que o Python encontre os módulos do projeto
# Linha corrigida
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
try:
    from yolo.detectar_graos import YOLOObjectDetector
except ModuleNotFoundError:
    print("ERRO DE IMPORTAÇÃO: Não foi possível encontrar a classe 'YOLOObjectDetector'.")
    print("Verifique se o arquivo 'yolo/detectar_graos.py' existe e está correto.")
    sys.exit(1)

def criar_dataset_cnn_a_partir_do_yolo():
    """
    Usa o detector YOLO para processar um conjunto de imagens-fonte
    (já separadas por classe) para criar um dataset de classificação para a CNN.
    """
    print("--- Iniciando a criação do dataset para a CNN ---")

    # --- CONFIGURAÇÕES ---
    # Diretório onde estão suas imagens originais, já em pastas com os nomes das classes
    # Ex: 'IMAGENS_FONTE/25/imagem1.jpg', 'IMAGENS_FONTE/35/imagem2.jpg'
    diretorio_fonte = "dataset/yolo"
    
    # Diretório de destino, onde o novo dataset para a CNN será criado
    diretorio_destino_cnn = "dataset/cnn"
    # ---------------------

    # Verifica se o diretório fonte existe
    if not os.path.exists(diretorio_fonte):
        print(f"ERRO: O diretório fonte '{diretorio_fonte}' não foi encontrado.")
        print("Por favor, crie esta pasta e organize suas imagens de origem dentro de subpastas com os nomes das classes (ex: '25', '35', etc.).")
        return

    # Limpa e recria o diretório de destino para garantir que não haja arquivos antigos
    if os.path.exists(diretorio_destino_cnn):
        shutil.rmtree(diretorio_destino_cnn)
        print(f"Diretório de destino antigo '{diretorio_destino_cnn}' removido.")
    os.makedirs(diretorio_destino_cnn)
    print(f"Diretório de destino '{diretorio_destino_cnn}' criado.")

    # Inicializa o detector YOLO uma única vez
    try:
        yolo = YOLOObjectDetector()
    except Exception as e:
        print(f"Erro ao carregar o detector YOLO: {e}")
        return

    total_recortes = 0
    # Itera sobre cada pasta de classe no diretório fonte (ex: '25', '35', '45'...)
    for nome_classe in os.listdir(diretorio_fonte):
        caminho_classe_fonte = os.path.join(diretorio_fonte, nome_classe)
        
        if not os.path.isdir(caminho_classe_fonte):
            continue

        print(f"\n---> Processando classe: [{nome_classe}]")
        
        # Cria a pasta de destino correspondente para a classe
        caminho_classe_destino = os.path.join(diretorio_destino_cnn, nome_classe)
        os.makedirs(caminho_classe_destino, exist_ok=True)
        
        recortes_por_classe = 0
        # Itera sobre cada imagem fonte dentro da pasta da classe
        for filename in os.listdir(caminho_classe_fonte):
            if not filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                continue
            
            caminho_imagem = os.path.join(caminho_classe_fonte, filename)
            frame = cv2.imread(caminho_imagem)
            
            if frame is None:
                print(f"   - Aviso: Falha ao ler a imagem {filename}")
                continue

            # Usa o detector para encontrar e recortar os grãos da imagem inteira
            # Não precisamos do frame com as detecções, apenas da lista de recortes
            _, graos_recortados = yolo.detectar_e_recortar(frame)
            
            # Salva cada grão recortado na pasta de destino da classe
            for i, grao in enumerate(graos_recortados):
                recortes_por_classe += 1
                total_recortes += 1
                # Cria um nome de arquivo único para cada recorte
                nome_recorte = f"{nome_classe}__{os.path.splitext(filename)[0]}_grao_{i+1}.png"
                caminho_salvar = os.path.join(caminho_classe_destino, nome_recorte)
                cv2.imwrite(caminho_salvar, grao)
        
        print(f"   -> {recortes_por_classe} grãos recortados e salvos para esta classe.")

    print("\n--- Criação do dataset da CNN concluída! ---")
    print(f"Total de {total_recortes} imagens de grãos individuais salvas.")
    print(f"O dataset está pronto para ser usado em: '{diretorio_destino_cnn}'")


if __name__ == '__main__':
    criar_dataset_cnn_a_partir_do_yolo()