import cv2
import numpy as np

def preprocessar_para_modelo(frame, input_size_tuple, normalize_type="0_1"):
    if frame is None or frame.size == 0:
        print("Erro: Frame de entrada para pré-processamento está vazio.")
        return None

    try:
        img_resized = cv2.resize(frame, input_size_tuple)
    except Exception as e:
        print(f"Erro ao redimensionar imagem: {e}. Shape do frame: {frame.shape}, input_size: {input_size_tuple}")
        return None


    if normalize_type == "0_1":
        img_normalized = img_resized / 255.0
    elif normalize_type == "-1_1":
        img_normalized = (img_resized.astype(np.float32) - 127.5) / 127.5
    else:
        img_normalized = img_resized.astype(np.float32)

    input_data = np.expand_dims(img_normalized, axis=0).astype(np.float32)
    return input_data

def desenhar_deteccoes_yolo(frame, boxes_scores_classes, frame_scale_factor_x=1.0, frame_scale_factor_y=1.0):
    for (x1, y1, x2, y2, score, classe_id) in boxes_scores_classes:
        x1_adj = int(x1 * frame_scale_factor_x)
        y1_adj = int(y1 * frame_scale_factor_y)
        x2_adj = int(x2 * frame_scale_factor_x)
        y2_adj = int(y2 * frame_scale_factor_y)

        cv2.rectangle(frame, (x1_adj, y1_adj), (x2_adj, y2_adj), (0, 255, 0), 2)
        label = f"Grao: {score:.2f}"
        cv2.putText(frame, label, (x1_adj, y1_adj - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    return frame

def desenhar_roi_e_classificacao(frame, roi_rect, texto_classificacao, cor=(0, 255, 0)):
    (x, y, w, h) = roi_rect
    cv2.rectangle(frame, (x, y), (x + w, y + h), cor, 2)
    if texto_classificacao:
        cv2.putText(frame, texto_classificacao, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, cor, 2)
    return frame