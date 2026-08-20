# No arquivo: config.py

CAMERA_ID = 0

# --- MIRA DE PRECISAO (ROI) usada pelo pipeline atual (CIELAB + regressao linear) ---
# Centralizada aqui para nao depender de importar analise_torra.py (que roda um
# loop de video e cv2.imshow direto no import). analise_torra.py e
# coletar_dataset_real.py ainda tem essas constantes duplicadas localmente;
# ao ajustar a mira, mantenha os 3 lugares em sincronia (ou migre-os para ca
# na limpeza geral que ja esta em andamento).
X_INICIAL = 260
Y_INICIAL = 70
X_FINAL = 420
Y_FINAL = 220
