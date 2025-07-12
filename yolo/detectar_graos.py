import os
import sys
import cv2
import numpy as np
import tensorflow as tf
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config
from processamento_imagem.preprocess import preprocessar_frame_para_yolo

class YOLOObjectDetector:
    def __init__(self, model_filename=None, models_dir=None, input_size=None, confidence_threshold=None):
        self.model_filename = model_filename or config.YOLO_MODEL_FILENAME
        self.models_dir = models_dir or config.MODELS_DIR
        self.input_size = input_size or config.YOLO_INPUT_SIZE
        self.confidence_threshold = confidence_threshold or config.YOLO_CONFIDENCE_THRESHOLD

        self.model_path = os.path.join(self.models_dir, self.model_filename)
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Modelo YOLO não encontrado em {self.model_path}. Treine o modelo primeiro.")

        self.interpreter = tf.lite.Interpreter(model_path=self.model_path)
        self.interpreter.allocate_tensors()
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()
        print(f"Detector de Objetos YOLO carregado de {self.model_path}")


    def detectar(self, imagem_processada_para_yolo=None, original_frame_shape=None):
        """
        Detecta objetos em um frame capturado da webcam e pré-processado.
        Retorna: lista de class_id (nível de torra) das detecções com alta confiabilidade.
        """
        if imagem_processada_para_yolo is None or original_frame_shape is None:
            imagem_processada_para_yolo, original_frame_shape = preprocessar_frame_para_yolo(input_size=self.input_size)

        if imagem_processada_para_yolo is None:
            print("YOLO: Imagem de entrada é None.")
            return []

        expected_dtype = self.input_details[0]['dtype']
        if imagem_processada_para_yolo.dtype != expected_dtype:
            imagem_processada_para_yolo = imagem_processada_para_yolo.astype(expected_dtype)

        try:
            self.interpreter.set_tensor(self.input_details[0]['index'], imagem_processada_para_yolo)
            self.interpreter.invoke()
        except Exception as e:
            print(f"Erro durante a inferência do YOLO: {e}")
            return []

        raw_detections = self.interpreter.get_tensor(self.output_details[0]['index'])
        boxes = []
        scores = []
        class_ids = []

        frame_h, frame_w = original_frame_shape[:2]
        input_h, input_w = self.input_size

        for i in range(raw_detections.shape[1]):
            detection = raw_detections[0, i, :]
            obj_confidence = detection[4]
            if obj_confidence > self.confidence_threshold:
                class_scores = detection[5:]
                class_id = np.argmax(class_scores)
                max_class_score = class_scores[class_id]
                confidence_score = obj_confidence * max_class_score
                if confidence_score > self.confidence_threshold:
                    cx, cy, w, h = detection[0], detection[1], detection[2], detection[3]
                    x1_input = (cx - w / 2) * input_w
                    y1_input = (cy - h / 2) * input_h
                    x2_input = (cx + w / 2) * input_w
                    y2_input = (cy + h / 2) * input_h
                    boxes.append([x1_input, y1_input, x2_input, y2_input])
                    scores.append(float(confidence_score))
                    class_ids.append(int(class_id))

        # NMS
        if len(boxes) > 0:
            nms_boxes = []
            for box in boxes:
                x1, y1, x2, y2 = box
                nms_boxes.append([int(x1), int(y1), int(x2-x1), int(y2-y1)])
            indices = cv2.dnn.NMSBoxes(nms_boxes, scores, self.confidence_threshold, nms_threshold=0.45)
        else:
            indices = []

        high_confidence_classes = []
        # Defina o limiar "alto" de confiança
        high_conf_threshold = getattr(config, 'YOLO_HIGH_CONFIDENCE_THRESHOLD', 0.8)

        if len(indices) > 0:
            if isinstance(indices, tuple):
                indices = indices[0]
            else:
                indices = indices.flatten() if hasattr(indices, 'flatten') else indices

            for i in indices:
                score = scores[i]
                class_id = class_ids[i]
                if score >= high_conf_threshold:
                    high_confidence_classes.append(class_id)

        if not high_confidence_classes:
            print("YOLO: Nenhuma detecção de alta confiabilidade encontrada.")

        return high_confidence_classes

