import os
import sys
from ultralytics import YOLO 

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
import config

class YOLOObjectDetector:
    def __init__(self, model_filename=None, models_dir=None):
        self.model_filename = model_filename or config.YOLO_MODEL_FILENAME
        self.models_dir = models_dir or config.MODELS_DIR
        self.model_path = os.path.join(self.models_dir, self.model_filename)
        self.confidence_threshold = config.YOLO_CONFIDENCE_THRESHOLD
        
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Modelo YOLO não encontrado em {self.model_path}.")
            
        try:
            self.model = YOLO(self.model_path)
            self.model.to('cpu')
            print(f"Detector de Objetos YOLO carregado de {self.model_path}")
            print(f"Limiar de Confiança: {self.confidence_threshold}")
        except Exception as e:
            print(f"Erro ao carregar o modelo: {e}")
            raise e

    def detectar_e_recortar(self, frame_original):
        """
        Detecta objetos usando o modelo .pt e retorna o frame e os recortes.
        O pós-processamento é feito pela própria biblioteca.
        """

        results = self.model.predict(source=frame_original, conf=self.confidence_threshold, verbose=False)
        
        result = results[0]
        
        frame_com_detecoes = result.plot() 
        imagens_recortadas = []

        for box in result.boxes:
           
            coords = box.xyxy[0].cpu().numpy().astype(int)
            x1, y1, x2, y2 = coords
            
            recorte = frame_original[y1:y2, x1:x2]
            if recorte.size > 0:
                imagens_recortadas.append(recorte)

        if not imagens_recortadas:
            print("YOLO: Nenhuma detecção encontraa com os limiares atuais.")

        return frame_com_detecoes, imagens_recortadas