import cv2
import time
import os
import sys

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

import config
from camera import capturar_frame
from processamento_imagem.preprocess import preprocessar_grao_para_clip
from yolo.detectar_graos import YOLOObjectDetector
from clip_.clip_classifier import CLIPClassifier

def main_pipeline():
    webcam = None
    try:
        print("--- Inicializando sistemas... ---")
        yolo_detector = YOLOObjectDetector()
        cnn_classifier = CLIPClassifier()
        webcam = capturar_frame.iniciar_webcam()
        print("--- Sistemas prontos. Iniciando loop principal. ---")
        print("Pressione 'q' na janela de visualização para sair.")

        while True:
            frame_bruto = capturar_frame.capturar_frame_ativo(webcam)
            if frame_bruto is None:
                print("Aviso: Falha ao capturar frame.")
                time.sleep(0.1)
                continue

            frame_com_detecoes, graos_recortados = yolo_detector.detectar_e_recortar(frame_bruto)

            resultados_clip = []
            if graos_recortados:
                for grao_crop in graos_recortados:
                    input_clip = preprocessar_grao_para_clip(grao_crop)
                    if input_clip is not None:
                        classificacao, _ = cnn_classifier.classificar(input_clip)
                        resultados_clip.append(classificacao)
            
            texto_yolo = f"Graos Detectados: {len(graos_recortados)}"
            cv2.putText(frame_com_detecoes, texto_yolo, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            texto_cnn = "Torra (CLIP): " + ", ".join(resultados_clip[:5])
            if len(resultados_clip) > 5:
                texto_cnn += "..."
            cv2.putText(frame_com_detecoes, texto_cnn, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)

            cv2.imshow("Visao do Torrador IA", frame_com_detecoes)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    except Exception as e:
        print(f"Ocorreu um erro crítico na aplicação: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n--- Finalizando a aplicação... ---")
        if webcam:
            capturar_frame.liberar_webcam(webcam)
        cv2.destroyAllWindows()
        print("Recursos liberados. Sistema finalizado.")


if __name__ == '__main__':
    main_pipeline()
