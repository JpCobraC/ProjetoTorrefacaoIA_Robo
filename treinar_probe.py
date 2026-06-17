import os
import cv2
import torch
import clip
import numpy as np
from PIL import Image
from sklearn.neighbors import KNeighborsClassifier #
import joblib

def treinar():
    print("A iniciar o treino do Cérebro de Cores (KNN)...")
    device = "cpu"
    model, preprocess = clip.load('ViT-B/32', device)
    pasta_base = "dataset/cnn" 
    
    features_lista = []
    labels_lista = []
    MAX_FOTOS = 50
    
    for classe_agtron in os.listdir(pasta_base):
        caminho_classe = os.path.join(pasta_base, classe_agtron)
        
        if not os.path.isdir(caminho_classe):
            continue
            
        print(f"A memorizar as cores da classe Agtron {classe_agtron}...")
        contador = 0
        for nome_foto in os.listdir(caminho_classe):
            if contador >= MAX_FOTOS:
                break
            caminho_foto = os.path.join(caminho_classe, nome_foto)
            imagem_cv2 = cv2.imread(caminho_foto)
            
            if imagem_cv2 is None:
                continue
                
            grao_rgb = cv2.cvtColor(imagem_cv2, cv2.COLOR_BGR2RGB)
            imagem_pil = Image.fromarray(grao_rgb)
            image_input = preprocess(imagem_pil).unsqueeze(0).to(device)
            
            with torch.no_grad():
                image_features = model.encode_image(image_input)
                image_features /= image_features.norm(dim=-1, keepdim=True)
                
            features_lista.append(image_features.cpu().numpy()[0])
            labels_lista.append(classe_agtron)
            contador += 1

    if len(features_lista) == 0:
        print("ERRO: Nenhuma foto encontrada na pasta!")
        return

    print("\nExtração concluída! A treinar o modelo KNN...")
    X = np.array(features_lista)
    y = np.array(labels_lista)
    classifier = KNeighborsClassifier(n_neighbors=5, weights='distance')
    classifier.fit(X, y)
    
    joblib.dump(classifier, "modelo_agtron_knn.pkl")
    print("\nSUCESSO! Modelo 'modelo_agtron_knn.pkl' guardado e pronto.")

if __name__ == "__main__":
    treinar()