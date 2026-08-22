import cv2
import numpy as np
import pickle  # Biblioteca nativa para carregar arquivos .pkl

# --- MIRA DE PRECISAO (ROI) ---
# Edite esses 4 numeros e rode o script de novo para ajustar a mira aos graos,
# evitando pegar a parede metalica da pipoqueira.
X_INICIAL = 260
Y_INICIAL = 70
X_FINAL = 420
Y_FINAL = 220

# 1. CARREGANDO O MODELO DE IA (CÉREBRO TREINADO)
try:
    with open('modelo_agtron_linear.pkl', 'rb') as f:
        modelo_agtron = pickle.load(f)
    print("Modelo IA carregado com sucesso!")
except Exception as e:
    print(f"Erro ao carregar o modelo: {e}")
    print("Verifique se o arquivo 'modelo_agtron_linear.pkl' está na mesma pasta.")
    exit()

# 2. Conectando a fonte de vídeo
video_path = 'torra_v2.mp4'
cap = cv2.VideoCapture(video_path)

if not cap.isOpened():
    print("Erro: Não foi possível abrir o vídeo.")
    exit()

while True:
    ret, frame = cap.read()
    if not ret:
        print("Fim do vídeo.")
        break
        
    frame = cv2.resize(frame, (640, 480))

    zona_do_cafe = frame[Y_INICIAL:Y_FINAL, X_INICIAL:X_FINAL]

    # Matemática da Cor (Espaço CIELAB)
    lab_frame = cv2.cvtColor(zona_do_cafe, cv2.COLOR_BGR2LAB)
    l_channel, a_channel, b_channel = cv2.split(lab_frame)
    
    l_mean = np.mean(l_channel)
    a_mean = np.mean(a_channel)
    b_mean = np.mean(b_channel)
    
    # 3. PREDIÇÃO EM TEMPO REAL
    # Organiza os dados no formato que a IA espera: [[L, a, b]]
    dados_entrada = np.array([[l_mean, a_mean, b_mean]])
    
    # A IA calcula o valor Agtron com base no que aprendeu no treino
    valor_agtron_predito = modelo_agtron.predict(dados_entrada)[0]
    
    # Classificação visual baseada no valor Agtron predito
    if valor_agtron_predito > 85:
        tipo_torra = "Crua / Muito Clara"
    elif 70 < valor_agtron_predito <= 85:
        tipo_torra = "Clara (Light)"
    elif 50 < valor_agtron_predito <= 70:
        tipo_torra = "Media (Medium)"
    else:
        tipo_torra = "Escura (Dark)"

    # 4. EXIBIÇÃO DOS DADOS DE IA NA TELA
    cv2.rectangle(frame, (X_INICIAL, Y_INICIAL), (X_FINAL, Y_FINAL), (0, 255, 0), 2)
    
    # Texto 1: Valores brutos dos sensores
    texto_sensores = f"L: {l_mean:.1f} | a: {a_mean:.1f} | b: {b_mean:.1f}"
    cv2.putText(frame, texto_sensores, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    
    # Texto 2: Resultado da Inteligência Artificial
    texto_ia = f"AGTRON: {valor_agtron_predito:.1f} ({tipo_torra})"
    cv2.putText(frame, texto_ia, (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
    
    # Exibindo as imagens
    cv2.imshow("Sistema de Monitoramento - IA Torrefacao", frame)
    
    if cv2.waitKey(30) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()