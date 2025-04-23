import cv2
from camera.capturar_frame import capturar_frame
from processamento_imagem.processar_imagem import bgr_para_hsv, preparar_crop
from yolo.detectar_graos import detectar_graos
from cnn.classificar_torra import classificar_torra

while True:
    frame_bgr = capturar_frame()
    if frame_bgr is None:
        print("Erro ao capturar imagem.")
        break

    frame_hsv = bgr_para_hsv(frame_bgr)
    frame_para_yolo = cv2.cvtColor(frame_hsv, cv2.COLOR_HSV2BGR)

    boxes = detectar_graos(frame_para_yolo)

    for (x1, y1, x2, y2) in boxes:
        crop = frame_bgr[y1:y2, x1:x2]
        if crop.size == 0:
            continue

        try:
            tensor_crop = preparar_crop(crop)
            classe_torra = classificar_torra(tensor_crop)

            cv2.rectangle(frame_bgr, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame_bgr, classe_torra, (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        except:
            continue

    cv2.imshow("YOLO + Classificação de Torra", frame_bgr)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()