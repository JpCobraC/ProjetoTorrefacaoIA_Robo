import cv2
import time
import os

import config
from camera import capturar_frame
from processamento_imagem import processar_imagem, desenhar_deteccoes_yolo, desenhar_roi_e_classificacao
from cnn.classificar_torra import CNNClassifier
from yolo.detectar_graos import YOLOObjectDetector
import roaster_control

def main_loop():
    print("Iniciando Sistema de IA para Torrador de Café...")
    roaster_control.configurar_gpio()
    webcam_obj = None
    cnn_classifier = None
    yolo_detector = None

    USAR_YOLO_PARA_ROI = False

    try:
        try:
            cnn_classifier = CNNClassifier(model_filename=config.CNN_MODEL_FILENAME, models_dir=config.MODELS_DIR)
            if USAR_YOLO_PARA_ROI:
                yolo_detector = YOLOObjectDetector(model_filename=config.YOLO_MODEL_FILENAME, models_dir=config.MODELS_DIR)
        except FileNotFoundError as e:
            print(f"Erro ao carregar modelo: {e}")
            print("Certifique-se de que os modelos treinados (.tflite) estão na pasta 'models/'")
            print("e que os nomes em 'config.py' estão corretos.")
            return

        webcam_obj = capturar_frame.iniciar_webcam()
        print("Iniciando processo de torra (simulado ou real).")
        roaster_control.controlar_aquecedor(True)

        ultima_classificacao = "inicializando"
        confianca_classificacao = 0.0

        while True:
            frame_bruto = capturar_frame.capturar_frame_ativo(webcam_obj)
            if frame_bruto is None:
                print("Falha ao capturar frame da webcam. Tentando novamente...")
                time.sleep(0.1)
                continue

            frame_para_display = frame_bruto.copy()
            crop_para_cnn = None

            if USAR_YOLO_PARA_ROI and yolo_detector:
                img_proc_yolo = processar_imagem.preprocessar_para_modelo(frame_bruto.copy(), config.YOLO_INPUT_SIZE)
                if img_proc_yolo is not None:
                    detections = yolo_detector.detectar(img_proc_yolo, frame_bruto.shape)
                    frame_para_display = processar_imagem.desenhar_deteccoes_yolo(frame_para_display, detections)

                    if detections:
                        x1, y1, x2, y2, score, _ = detections[0]
                        if x1 < x2 and y1 < y2:
                             crop_para_cnn = frame_bruto[y1:y2, x1:x2]
                        else:
                            print("YOLO ROI inválido (x1>=x2 ou y1>=y2). Usando ROI fixo de fallback.")
                            USAR_YOLO_PARA_ROI = False
                    else:
                        print("Nenhum objeto detectado pelo YOLO. Usando ROI fixo de fallback.")
                        USAR_YOLO_PARA_ROI = False
                else:
                    print("Falha ao pré-processar imagem para YOLO.")
                    USAR_YOLO_PARA_ROI = False

            if not USAR_YOLO_PARA_ROI or crop_para_cnn is None or crop_para_cnn.size == 0:
                roi_x, roi_y, roi_w, roi_h = 150, 150, 120, 120

                if (roi_y + roi_h > frame_bruto.shape[0] or roi_x + roi_w > frame_bruto.shape[1] or
                    roi_y < 0 or roi_x < 0 or roi_w <=0 or roi_h <=0 ):
                    print(f"ERRO: ROI Fixo ({roi_x},{roi_y},{roi_w},{roi_h}) inválido ou fora dos limites da imagem ({frame_bruto.shape}).")
                    cv2.rectangle(frame_para_display, (roi_x, roi_y), (roi_x + roi_w, roi_y + roi_h), (0,0,255), 2) # Desenha ROI inválido
                else:
                    crop_para_cnn = frame_bruto[roi_y:roi_y+roi_h, roi_x:roi_x+roi_w]
                roi_para_desenho = (roi_x, roi_y, roi_w, roi_h)

            if crop_para_cnn is not None and crop_para_cnn.size > 0:
                img_proc_cnn = processar_imagem.preprocessar_para_modelo(crop_para_cnn.copy(), config.CNN_INPUT_SIZE)
                if img_proc_cnn is not None and cnn_classifier:
                    ultima_classificacao, confianca_classificacao = cnn_classifier.classificar(img_proc_cnn)
                else:
                    ultima_classificacao = "erro_proc_cnn"
                    confianca_classificacao = 0.0
            else:
                ultima_classificacao = "erro_crop_cnn"
                confianca_classificacao = 0.0

            texto_display_cnn = f"{ultima_classificacao} ({confianca_classificacao:.2f})"
            if not USAR_YOLO_PARA_ROI:
                 frame_para_display = processar_imagem.desenhar_roi_e_classificacao(
                     frame_para_display, roi_para_desenho, texto_display_cnn
                 )
            else:
                cv2.putText(frame_para_display, texto_display_cnn, (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)


            cv2.imshow("Visao do Torrador IA", frame_para_display)
            if ultima_classificacao == config.ESTAGIO_FINAL_DESEJADO and \
               confianca_classificacao >= config.CNN_CONFIDENCE_THRESHOLD:
                print(f"ATINGIU ESTÁGIO FINAL: {config.ESTAGIO_FINAL_DESEJADO}. Finalizando.")
                roaster_control.controlar_aquecedor(False)
                roaster_control.controlar_ventoinha(True) 
                break 


            key = cv2.waitKey(500)
            if key & 0xFF == ord('q'):
                print("Tecla 'q' pressionada. Encerrando...")
                break

    except capturar_frame.WebcamError as e:
        print(f"Erro de Webcam: {e}")
    except KeyboardInterrupt:
        print("Programa interrompido pelo usuário.")
    except Exception as e:
        print(f"Ocorreu um erro inesperado no loop principal: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("Finalizando o programa e limpando recursos...")
        if webcam_obj:
            capturar_frame.liberar_webcam(webcam_obj)
        cv2.destroyAllWindows()
        roaster_control.controlar_aquecedor(False)
        roaster_control.controlar_ventoinha(False)
        roaster_control.limpar_gpio()
        print("Sistema finalizado.")

if __name__ == '__main__':
    main_loop()