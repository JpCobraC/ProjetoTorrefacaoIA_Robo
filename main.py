import cv2
import time
import os
import sys

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

import config
from camera import capturar_frame
from processamento_imagem.preprocess import aplicar_crop_customizado
from yolo.detectar_graos import YOLOObjectDetector
from cnn.classificar_torra import CNNClassifier

def main_pipeline():
    """
    Função principal que executa o pipeline completo:
    Câmera -> Crop -> Detecção YOLO -> Classificação CNN
    """
    webcam = None
    try:
        # 1. INICIALIZAÇÃO (uma única vez)
        print("--- Inicializando sistemas... ---")
        yolo_detector = YOLOObjectDetector()
        cnn_classifier = CNNClassifier()
        webcam = capturar_frame.iniciar_webcam(config.CAMERA_ID)
        print("--- Sistemas prontos. Iniciando loop principal. ---")
        print("Pressione 'q' na janela de visualização para sair.")

        # 2. LOOP PRINCIPAL
        while True:
            # Etapa 1: Capturar frame da webcam
            frame_bruto = capturar_frame.capturar_frame_ativo(webcam)
            if frame_bruto is None:
                print("Aviso: Falha ao capturar frame.")
                time.sleep(0.1)
                continue

            # Etapa 2: Aplicar pré-processamento
            area_de_interesse = aplicar_crop_customizado(frame_bruto)
            if area_de_interesse is None or area_de_interesse.size == 0:
                print("Aviso: O recorte da área de interesse resultou em uma imagem vazia.")
                cv2.imshow("Visao do Torrador IA", frame_bruto) # Mostra o frame original em caso de erro
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                continue

            # Etapa 3: Detecção com YOLO na área de interesse
            # Este método já retorna o frame com as detecções e a lista de grãos recortados
            frame_com_detecoes, graos_recortados = yolo_detector.detectar_e_recortar(area_de_interesse)

            # Etapa 4: Classificação com CNN em cada grão detectado
            resultados_cnn = []
            if graos_recortados:
                for grao in graos_recortados:
                    # Pré-processamento específico para a CNN (se houver)
                    # Assumindo que a classe CNNClassifier tem um método para isso
                    classificacao, confianca = cnn_classifier.classificar(grao)
                    resultados_cnn.append(f"{classificacao} ({confianca:.0%})")
            
            # Etapa 5: Exibição dos resultados
            # Adiciona informações de texto no frame que já tem as caixas do YOLO
            texto_yolo = f"Graos Detectados: {len(graos_recortados)}"
            cv2.putText(frame_com_detecoes, texto_yolo, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # Mostra os resultados da CNN
            texto_cnn = "CNN: " + ", ".join(resultados_cnn[:4]) # Mostra os 4 primeiros resultados
            if len(resultados_cnn) > 4:
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