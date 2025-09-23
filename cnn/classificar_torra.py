# No arquivo: cnn/classificar_torra_api.py
import os
import sys
from inference import get_model

# Adiciona a raiz do projeto ao path para encontrar o config.py
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
import config

class CNNClassifierAPI:
    def __init__(self):
        # Puxa as informações do Roboflow do arquivo config.py
        self.api_key = config.ROBOFLOW_API_KEY
        self.model_id = config.ROBOFLOW_MODEL_ID
        self.confidence_threshold = config.CNN_CONFIDENCE_THRESHOLD
        self.classes = config.CNN_CLASSES
        
        if not self.api_key or not self.model_id:
             raise ValueError("ERRO: ROBOFLOW_API_KEY e ROBOFLOW_MODEL_ID devem ser definidos no seu .env.local e carregados pelo config.py")

        # O resto do código da classe está perfeito...
        try:
            self.model = get_model(model_id=self.model_id, api_key=self.api_key)
            print(f"Classificador CNN (API) carregado para o modelo: {self.model_id}")
        except Exception as e:
            print(f"Erro ao carregar o modelo da API do Roboflow: {e}")
            raise e

    def classificar(self, imagem_grao):
        # ... (seu código de classificação está perfeito) ...
        if imagem_grao is None:
            return "desconhecido", 0.0

        try:
            results = self.model.infer(imagem_grao)[0]
            classe_prevista = results.top
            confianca = float(results.confidence)
            nivel_torra = "incerto"

            if classe_prevista in self.classes:
                if confianca >= self.confidence_threshold:
                    nivel_torra = classe_prevista
                else:
                    nivel_torra = f"incerto ({classe_prevista})"
            
            return nivel_torra, confianca

        except Exception as e:
            print(f"Erro durante a inferência com a API da CNN: {e}")
            return "erro_api", 0.0