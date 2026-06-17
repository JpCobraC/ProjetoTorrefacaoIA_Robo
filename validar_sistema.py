import os
import sys
import cv2
import numpy as np
from collections import Counter
import re

os.environ['CUDA_VISIBLE_DEVICES'] = ''
DIRETORIO_ATUAL = os.path.dirname(os.path.abspath(__file__))
sys.path.append(DIRETORIO_ATUAL)

from processamento_imagem.preprocess import preprocessar_grao_para_clip
from yolo.detectar_graos import YOLOObjectDetector
from clip_.clip_classifier import CLIPClassifier

yolo_detector = None
cnn_classifier = None

print("[IA] Inicializando pesos do YOLOv8 e CLIP...")
try:
    yolo_detector = YOLOObjectDetector()
    cnn_classifier = CLIPClassifier()
    print("[IA] Modelos carregados com sucesso!")
except Exception as e:
    print(f"[ERRO CRÍTICO] Falha ao carregar modelos: {e}")

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

def analisar_para_api(frame_ao_vivo):
    global yolo_detector, cnn_classifier
    try:
        if frame_ao_vivo is None or yolo_detector is None or cnn_classifier is None:
            return 0.0, "Erro IA", 0.0
        
        frame_desenhado, graos_recortados = yolo_detector.detectar_e_recortar(frame_ao_vivo)
        
        if frame_desenhado is not None:
            caminho_debug = os.path.join(DIRETORIO_ATUAL, "debug_yolo_visao.jpg")
            cv2.imwrite(caminho_debug, frame_desenhado)
        
        pasta_auditoria = os.path.join(DIRETORIO_ATUAL, "auditoria_clip")
        os.makedirs(pasta_auditoria, exist_ok=True)
        
        for arquivo in os.listdir(pasta_auditoria):
            caminho_arquivo = os.path.join(pasta_auditoria, arquivo)
            if os.path.isfile(caminho_arquivo):
                os.remove(caminho_arquivo)

        classificacoes_cnn = []
        if graos_recortados:
            for idx, grao_crop in enumerate(graos_recortados):
                classificacao, _ = cnn_classifier.classificar(grao_crop)
                classificacoes_cnn.append(classificacao)
                
                nome_limpo = str(classificacao).replace("/", "_").replace(" ", "_")
                nome_foto = f"grao_{idx}_Veredito_{nome_limpo}.jpg"
                cv2.imwrite(os.path.join(pasta_auditoria, nome_foto), grao_crop)
                
        estatisticas = analisar_distribuicao_torra(classificacoes_cnn)
        return estatisticas['media_agtron'], estatisticas['classe_dominante'], estatisticas['desvio_padrao']
        
    except Exception as e:
        print(f"[ERRO] Falha na esteira de IA: {e}")
        return 0.0, "Erro Interno", 0.0