import cv2
import time
import os
import sys

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

import config
from camera import capturar_frame
from processamento_imagem.preprocess import aplicar_crop_customizado, preprocessar_grao_para_cnn
from yolo.detectar_graos import YOLOObjectDetector
from cnn.classificar_torra import CNNClassifier

def main_pipeline():
    webcam = None
    try:
        # 1. INICIALIZAÇÃO DOS MODELOS E CÂMERA (uma única vez)
        print("--- Inicializando sistemas... ---")
        yolo_detector = YOLOObjectDetector()
        cnn_classifier = CNNClassifier()
        webcam = capturar_frame.iniciar_webcam()
        print("--- Sistemas prontos. Iniciando loop principal. ---")
        print("Pressione 'q' na janela de visualização para sair.")

        # 2. LOOP PRINCIPAL (execução contínua)
        while True:
            # Etapa 1: Capturar frame
            frame_bruto = capturar_frame.capturar_frame_ativo(webcam)
            if frame_bruto is None:
                print("Aviso: Falha ao capturar frame.")
                time.sleep(0.1)
                continue

            # Etapa 2: Aplicar pré-processamento (crop da área de interesse)
            area_de_interesse = aplicar_crop_customizado(frame_bruto)
            if area_de_interesse is None or area_de_interesse.size == 0:
                cv2.imshow("Visao do Torrador IA", frame_bruto)
                if cv2.waitKey(1) & 0xFF == ord('q'): break
                continue

            # Etapa 3: Detecção com YOLO na área de interesse
            frame_com_detecoes, graos_recortados = yolo_detector.detectar_e_recortar(area_de_interesse)

            # Etapa 4: Classificação com CNN em cada grão detectado
            resultados_cnn = []
            if graos_recortados:
                for grao_crop in graos_recortados:
                    input_cnn = preprocessar_grao_para_cnn(grao_crop)
                    if input_cnn is not None:
                        classificacao, _ = cnn_classifier.classificar(input_cnn)
                        resultados_cnn.append(classificacao)
            
            # Etapa 5: Exibição dos resultados
            texto_yolo = f"Graos Detectados: {len(graos_recortados)}"
            cv2.putText(frame_com_detecoes, texto_yolo, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            texto_cnn = "Torra (CNN): " + ", ".join(resultados_cnn[:5])
            if len(resultados_cnn) > 5:
                texto_cnn += "..."
            cv2.putText(frame_com_detecoes, texto_cnn, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)

            cv2.imshow("Visao do Torrador IA", frame_com_detecoes)

            # Condição de saída
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    except Exception as e:
        print(f"Ocorreu um erro crítico na aplicação: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Garante que os recursos sejam liberados
        print("\n--- Finalizando a aplicação... ---")
        if webcam:
            capturar_frame.liberar_webcam(webcam)
        cv2.destroyAllWindows()
        print("Recursos liberados. Sistema finalizado.")


if __name__ == '__main__':
    main_pipeline()