import tensorflow as tf
import numpy as np
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import config
import cv2
from yolo.detectar_graos import YOLOObjectDetector

class CNNClassifier:
    def __init__(self, model_filename=config.CNN_MODEL_FILENAME, models_dir=config.MODELS_DIR):
        model_path = os.path.join(models_dir, model_filename)
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Modelo CNN não encontrado em {model_path}. Treine o modelo primeiro.")

        self.interpreter = tf.lite.Interpreter(model_path=model_path)
        self.interpreter.allocate_tensors()
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()

    def classificar(self, imagem_processada_para_cnn):
        if imagem_processada_para_cnn is None:
            return "desconhecido", 0.0

        expected_dtype = self.input_details[0]['dtype']
        if imagem_processada_para_cnn.dtype != expected_dtype:
            imagem_processada_para_cnn = imagem_processada_para_cnn.astype(expected_dtype)

        try:
            self.interpreter.set_tensor(self.input_details[0]['index'], imagem_processada_para_cnn)
            self.interpreter.invoke()
            output_data = self.interpreter.get_tensor(self.output_details[0]['index'])
        except Exception as e:
            print(f"Erro durante a inferência da CNN: {e}")
            print(f"Shape da imagem de entrada: {imagem_processada_para_cnn.shape}, dtype: {imagem_processada_para_cnn.dtype}")
            print(f"Detalhes da entrada do modelo: {self.input_details[0]}")
            return "erro_inferencia", 0.0


        classe_predita_idx = np.argmax(output_data[0])
        confianca = float(output_data[0, classe_predita_idx])

        if confianca >= config.CNN_CONFIDENCE_THRESHOLD and classe_predita_idx < len(config.CNN_CLASSES):
            nivel_torra = config.CNN_CLASSES[classe_predita_idx]
        else:
            nivel_torra = "incerto"
            if classe_predita_idx < len(config.CNN_CLASSES):
                 nivel_torra = f"incerto ({config.CNN_CLASSES[classe_predita_idx]})"


        return nivel_torra, confianca

if __name__ == '__main__':
    try:
        detector = YOLOObjectDetector()
        detections = detector.detectar()

        if not detections:
            print("Nenhum grão detectado para classificar.")
        else:
            classifier = CNNClassifier()
            for i, (x1, y1, x2, y2, score, class_id) in enumerate(detections):
                from processamento_imagem.preprocess import iniciar_webcam, capturar_frame_ativo, liberar_webcam
                cap = iniciar_webcam()
                try:
                    frame = capturar_frame_ativo(cap)
                finally:
                    liberar_webcam(cap)
                grao_crop = frame[y1:y2, x1:x2]
                grao_resized = cv2.resize(grao_crop, config.CNN_INPUT_SIZE)
                grao_resized = grao_resized.astype(np.float32) / 255.0
                grao_resized = np.expand_dims(grao_resized, axis=0)
                nivel, conf = classifier.classificar(grao_resized)
                print(f"Grão {i+1}: Nível={nivel}, Confiança={conf:.2f}, Score YOLO={score:.2f}, Classe YOLO={class_id}")
    except Exception as e:
        print(f"Erro no pipeline YOLO+CNN: {e}")