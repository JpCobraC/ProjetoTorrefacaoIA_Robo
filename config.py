# No arquivo: config.py

CAMERA_ID = 2

# --- MODO TESTE (sem camera fisica) ---
# Quando True, api_teste.py abre CAMINHO_VIDEO_TESTE (em loop, na velocidade
# real do video) no lugar da camera fisica, simulando uma torra ao vivo para
# testar o pipeline completo (frontend, grafico, medidor de torra) sem ter a
# camera conectada.
# IMPORTANTE: deixe False antes da apresentacao real, com a camera conectada.
USAR_VIDEO_DE_TESTE = False
# Alinhado com modelo_agtron_linear_v2_producao.pkl (treinado exclusivamente
# com torra_v2.mp4): usar torra.mp4 aqui desalinha o modo de teste do modelo
# em producao e gera predicoes fora da escala Agtron valida.
CAMINHO_VIDEO_TESTE = 'torra_v2.mp4'

# --- MIRA DE PRECISAO (ROI) usada pelo pipeline atual (CIELAB + regressao linear) ---
# Centralizada aqui para nao depender de importar analise_torra.py (que roda um
# loop de video e cv2.imshow direto no import). coletar_dataset_real.py ja
# importa esses 4 valores daqui; analise_torra.py ainda tem essa constante
# duplicada localmente -- sincronize-a manualmente se for usa-lo com a mesma mira.
X_INICIAL = 245
Y_INICIAL = 265
X_FINAL = 355
Y_FINAL = 355

# Resolucao do frame que a ROI acima referencia (usada para validar limites
# ao ajustar a mira pelo frontend em /roi e para o overlay do ROI se
# posicionar corretamente sobre o video). Casa com o formato nativo da
# camera (ver v4l2-ctl --list-formats-ext).
FRAME_WIDTH = 640
FRAME_HEIGHT = 480