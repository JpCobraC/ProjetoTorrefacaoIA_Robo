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
        Se não receber imagem_processada_para_yolo, faz a captura e o preprocessamento automaticamente.
        Retorna: lista de tuplas (x1, y1, x2, y2, score, classe_id)
                 EM COORDENADAS DA IMAGEM ORIGINAL.
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


        # --- INÍCIO DA SEÇÃO QUE PRECISA DE MUITA ADAPTAÇÃO ---
        # O formato da saída do YOLO TFLite varia MUITO dependendo de como
        # o modelo foi exportado (ex: de YOLOv5, YOLOv8, SSD MobileNet, etc.)
        # Você precisará inspecionar 'self.output_details' e a documentação
        # do seu modelo específico para implementar o pós-processamento corretamente.

        # Exemplo genérico para um modelo que retorna uma lista de detecções:
        # Pode haver múltiplos tensores de saída.
        # Output[0]: caixas, Output[1]: classes, Output[2]: scores, Output[3]: num_detections
        # Ou uma única saída combinada.
        
        # Supondo que o modelo YOLOv5/v8 exportado para TFLite tenha uma saída como:
        # (batch_size, num_boxes, num_classes + 5) onde os 5 são (cx, cy, w, h, object_confidence)
        # ou (batch_size, num_boxes, 6) onde 6 é (x1,y1,x2,y2, class_id, confidence) - mais raro para TFLite direto

        raw_detections = self.interpreter.get_tensor(self.output_details[0]['index'])
        # print(f"YOLO raw output shape: {raw_detections.shape}") # (ex: 1, 25200, 6)
        # print(f"YOLO output details: {self.output_details}")

        boxes = []
        scores = []
        class_ids = []

        # Obter dimensões originais e do input para reescalar as caixas
        frame_h, frame_w = original_frame_shape[:2]
        input_h, input_w = self.input_size # O tamanho para o qual a imagem foi redimensionada

        # Iterar sobre as detecções (assumindo raw_detections[0] para batch_size=1)
        # Este loop é um EXEMPLO e provavelmente precisará ser ajustado:
        for i in range(raw_detections.shape[1]): # raw_detections.shape[1] é num_boxes
            detection = raw_detections[0, i, :]

            # Exemplo para formato (cx, cy, w, h, obj_conf, class_scores...)
            obj_confidence = detection[4]
            if obj_confidence > self.confidence_threshold:
                class_scores = detection[5:] # Probabilidades das classes
                class_id = np.argmax(class_scores)
                max_class_score = class_scores[class_id]
                confidence_score = obj_confidence * max_class_score # Ou apenas obj_confidence

                if confidence_score > self.confidence_threshold:
                    # Coordenadas do centro, largura, altura (normalizadas pelo input_size)
                    cx, cy, w, h = detection[0], detection[1], detection[2], detection[3]

                    # Converter de [cx, cy, w, h] normalizado para [x1, y1, x2, y2] na escala do input_size
                    x1_input = (cx - w / 2) * input_w
                    y1_input = (cy - h / 2) * input_h
                    x2_input = (cx + w / 2) * input_w
                    y2_input = (cy + h / 2) * input_h

                    boxes.append([x1_input, y1_input, x2_input, y2_input])
                    scores.append(float(confidence_score))
                    class_ids.append(int(class_id))

        # Aplicar Non-Maximum Suppression (NMS)
        # O OpenCV NMS espera caixas no formato (x, y, w, h) ou (x1,y1,x2,y2)
        # e scores. A função retorna os índices das caixas a serem mantidas.
        # Converta boxes para o formato (x,y,w,h) se necessário para NMSBoxes, ou use NMSBoxesRotated
        # Esta conversão para NMSBoxes é para (x_min, y_min, width, height)
        # NMSBoxes do OpenCV espera (x,y,w,h) onde x,y é o canto superior esquerdo.
        # Ou, se as boxes já são (x1,y1,x2,y2), você pode usá-las com um nms_threshold.
        
        # Para NMS, as caixas (x1,y1,x2,y2) são geralmente melhores
        # Aqui, boxes já estão como [x1_input, y1_input, x2_input, y2_input]
        if len(boxes) > 0:
            # O NMS do TF Lite Task Library é mais fácil de usar se você puder incluí-lo
            # Ou usar cv2.dnn.NMSBoxes
            # NMSBoxes espera uma lista de BBoxes e uma lista de scores.
            # BBoxes devem ser (x_min, y_min, width, height)
            # No nosso caso, x1,y1,x2,y2. Vamos converter.
            nms_boxes = []
            for box in boxes:
                x1,y1,x2,y2 = box
                nms_boxes.append([int(x1), int(y1), int(x2-x1), int(y2-y1)])


            indices = cv2.dnn.NMSBoxes(nms_boxes, scores, self.confidence_threshold, nms_threshold=0.45)
        else:
            indices = []

        final_detections = []
        if len(indices) > 0:
            # Se NMSBoxes retorna uma tupla de arrays, pegue o primeiro. Se for flat, use diretamente.
            # indices = indices[0] if isinstance(indices, tuple) else indices.flatten()
            # Ou apenas:
            if isinstance(indices, tuple): # YOLOv8 NMS output
                indices = indices[0]
            else: # YOLOv5 NMS output
                indices = indices.flatten() if hasattr(indices, 'flatten') else indices


            for i in indices:
                x1_input, y1_input, x2_input, y2_input = boxes[i]
                score = scores[i]
                class_id = class_ids[i]

                # Reescalar para as dimensões do frame original
                scale_x = frame_w / input_w
                scale_y = frame_h / input_h

                x1_orig = int(x1_input * scale_x)
                y1_orig = int(y1_input * scale_y)
                x2_orig = int(x2_input * scale_x)
                y2_orig = int(y2_input * scale_y)
                
                # Garantir que as coordenadas não saiam dos limites da imagem
                x1_orig = max(0, x1_orig)
                y1_orig = max(0, y1_orig)
                x2_orig = min(frame_w -1, x2_orig)
                y2_orig = min(frame_h -1, y2_orig)

                final_detections.append((x1_orig, y1_orig, x2_orig, y2_orig, score, class_id))
        
        if not final_detections:
             print("YOLO: Nenhuma detecção final após NMS ou o NMS falhou em retornar índices válidos.")


        # --- FIM DA SEÇÃO QUE PRECISA DE MUITA ADAPTAÇÃO ---
        if not final_detections:
            print("AVISO: Nenhuma detecção YOLO processada. Verifique a lógica de pós-processamento em 'detectar_graos.py'.")

        return final_detections

# Exemplo de uso (para teste)
if __name__ == '__main__':
    print("Testando o detector YOLO...")
    try:
        # Crie uma imagem de exemplo e dimensões originais para testar
        dummy_image_data = np.random.rand(1, config.YOLO_INPUT_SIZE[0], config.YOLO_INPUT_SIZE[1], 3).astype(np.float32)
        original_shape = (480, 640, 3) # Exemplo de forma original

        model_file = os.path.join(config.MODELS_DIR, config.YOLO_MODEL_FILENAME)
        if not os.path.exists(model_file):
            print(f"Modelo de teste {model_file} não encontrado. Crie um placeholder ou treine um modelo.")
            if not os.path.exists(config.MODELS_DIR): os.makedirs(config.MODELS_DIR)
            # with open(model_file, 'w') as f: f.write("Este é um placeholder") # Não é um tflite válido
            print("Pulando teste de inferência YOLO pois o modelo real não foi encontrado.")
        else:
            detector = YOLOObjectDetector()
            detections = detector.detectar(dummy_image_data, original_shape)
            print(f"Detecções da imagem dummy: {len(detections)} objetos.")
            if detections:
                print(f"Primeira detecção: {detections[0]}")
    except Exception as e:
        print(f"Erro no teste do detector YOLO: {e}")