import torch
import clip
import cv2
import numpy as np
from PIL import Image
import joblib # <-- Importante para ler o ficheiro .pkl

class CLIPClassifier:
    def __init__(self):
        print("A inicializar o modelo CLIP e o Cérebro Lógico (Linear Probe)...")
        self.device = "cpu"
        
        # 1. Carrega o motor de extração (CLIP)
        self.model, self.preprocess = clip.load("ViT-B/32", device=self.device)
        
        # 2. Carrega a lógica matemática que você acabou de treinar!
        # (Substitui completamente o dicionário de textos em inglês)
        try:
            self.classifier = joblib.load("modelo_agtron_knn.pkl")
            print("Modelo Lógico carregado com sucesso e pronto para classificar!")
        except FileNotFoundError:
            print("ERRO: Não encontrei o ficheiro 'modelo_agtron_linear.pkl'.")

    def classificar(self, imagem_yolo):
        """Recebe o recorte do YOLO e devolve a classe Agtron e a confiança."""
        if imagem_yolo is None or imagem_yolo.size == 0:
            return "erro", 0.0

        # --- PONTE OpenCV -> CLIP ---
        grao_rgb = cv2.cvtColor(imagem_yolo, cv2.COLOR_BGR2RGB)
        imagem_pil = Image.fromarray(grao_rgb)
        image_input = self.preprocess(imagem_pil).unsqueeze(0).to(self.device)

        # --- EXTRAÇÃO DOS VETORES ---
        with torch.no_grad():
            image_features = self.model.encode_image(image_input)
            image_features /= image_features.norm(dim=-1, keepdim=True)
            
        # Converte os vetores da IA para o formato do Scikit-Learn
        features_numpy = image_features.cpu().numpy()
        
        # --- A MAGIA ACONTECE AQUI ---
        # Pergunta ao modelo que você treinou qual é a classe com base nestes números
        classes_disponiveis = self.classifier.classes_
        probabilidades = self.classifier.predict_proba(features_numpy)[0]
        
        # Encontra a classe com a maior probabilidade (Top 1)
        indice_vencedor = np.argmax(probabilidades)
        classe_vencedora = classes_disponiveis[indice_vencedor]
        confianca_float = probabilidades[indice_vencedor]
        
        return str(classe_vencedora), float(confianca_float)