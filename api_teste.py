import cv2
import os
import re
import threading
import time
from collections import Counter
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from validar_sistema import analisar_para_api, resetar_suavizacao
from fastapi.responses import StreamingResponse
import config

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ultimo_frame = None
lock_frame = threading.Lock()
sistema_rodando = True
comando_calibrar = False
camera = None

def descobrir_e_ligar_camera():
    """Tenta ligar a câmera externa (geralmente índice 0, 2 ou 4).

    Se config.USAR_VIDEO_DE_TESTE estiver ativo, abre o vídeo de bancada
    (torra.mp4) no lugar da câmera física, simulando uma torra ao vivo --
    útil para testar o pipeline completo (frontend, gráfico, medidor de
    torra) sem ter a câmera conectada.
    """
    if config.USAR_VIDEO_DE_TESTE:
        print(f"[MODO TESTE] Usando {config.CAMINHO_VIDEO_TESTE} como câmera simulada")
        cam = cv2.VideoCapture(config.CAMINHO_VIDEO_TESTE)
        if cam.isOpened():
            return cam
        print(f"[MODO TESTE] Falha ao abrir '{config.CAMINHO_VIDEO_TESTE}'.")
        return None

    indices_para_testar = [config.CAMERA_ID] + [i for i in [0, 2, 4, 1, 3] if i != config.CAMERA_ID]
    for indice in indices_para_testar:
        print(f"[HARDWARE] Tentando abrir /dev/video{indice}...")
        cam = cv2.VideoCapture(indice, cv2.CAP_V4L2)
        if cam.isOpened():
            sucesso, _ = cam.read()
            if sucesso:
                print(f"[SUCESSO] Câmera ativada no índice {indice}!")
                return cam
            cam.release()
    return None

def thread_captura_camera():
    """Mantém a câmera (ou o vídeo de teste) lendo frames e escuta comandos de reset"""
    global ultimo_frame, sistema_rodando, camera, comando_calibrar
    print("[HARDWARE] Thread de captura iniciada.")

    # No modo de teste, o intervalo entre leituras respeita o FPS real do
    # video (calculado assim que a captura abre), em vez do intervalo fixo
    # usado para a camera fisica -- assim a torra simulada roda na velocidade
    # real, nao mais rapido que o video de verdade.
    intervalo_leitura = 0.03

    while sistema_rodando:

        if comando_calibrar:
            print("[HARDWARE] Reiniciando e limpando o sensor da câmera...")
            if camera is not None:
                camera.release()
            camera = descobrir_e_ligar_camera()
            if camera is not None and config.USAR_VIDEO_DE_TESTE:
                intervalo_leitura = 1.0 / (camera.get(cv2.CAP_PROP_FPS) or 30)
            with lock_frame:
                ultimo_frame = None
            comando_calibrar = False
            continue

        if camera is None:
            camera = descobrir_e_ligar_camera()
            if camera is None:
                time.sleep(2.0)
                continue
            if config.USAR_VIDEO_DE_TESTE:
                intervalo_leitura = 1.0 / (camera.get(cv2.CAP_PROP_FPS) or 30)

        try:
            sucesso, frame = camera.read()

            # O video de teste tem fim (a camera fisica nao) -- ao chegar no
            # ultimo frame, volta para o inicio e continua em loop, para dar
            # para testar continuamente sem reiniciar o servidor.
            if not sucesso and config.USAR_VIDEO_DE_TESTE:
                camera.set(cv2.CAP_PROP_POS_FRAMES, 0)
                sucesso, frame = camera.read()

            if sucesso and frame is not None:
                with lock_frame:
                    ultimo_frame = frame.copy()
            else:
                if camera:
                    camera.release()
                camera = None
                time.sleep(1.0)
        except Exception as e:
            print(f"[ERRO CRÍTICO] Falha na leitura: {e}")
            camera = None
            time.sleep(1.0)

        time.sleep(intervalo_leitura)

threading.Thread(target=thread_captura_camera, daemon=True).start()

def gerar_frames_video():
    """Gerador contínuo de frames para o React (MJPEG Stream)"""
    global ultimo_frame, lock_frame
    while True:
        with lock_frame:
            if ultimo_frame is None:
                time.sleep(0.1)
                continue
            sucesso, buffer = cv2.imencode('.jpg', ultimo_frame)
            if not sucesso:
                continue
            frame_bytes = buffer.tobytes()
        
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        
        time.sleep(0.03) 

@app.get("/video_feed")
def video_feed():
    """Rota consumida pelo <CameraFeed /> do React"""
    return StreamingResponse(gerar_frames_video(), media_type="multipart/x-mixed-replace; boundary=frame")
@app.get("/status")
def checar_status():
    return {"status": "online"}

@app.get("/calibrar")
def acionar_calibracao():
    """Rota disparada pelo botão 'Calibrar Sensor'"""
    global comando_calibrar
    comando_calibrar = True
    return {"status": "sucesso", "mensagem": "Hardware resetado"}


class ROIAtualizacao(BaseModel):
    x_inicial: int
    y_inicial: int
    x_final: int
    y_final: int


def persistir_roi_no_disco(roi: ROIAtualizacao):
    """Reescreve as 4 linhas X_INICIAL/Y_INICIAL/X_FINAL/Y_FINAL em config.py
    com os novos valores, para que o ajuste feito no frontend sobreviva a um
    restart do servidor (o resto do arquivo, incluindo comentarios, fica
    intacto)."""
    caminho_config = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.py')
    with open(caminho_config, 'r') as f:
        conteudo = f.read()

    substituicoes = {
        'X_INICIAL': roi.x_inicial,
        'Y_INICIAL': roi.y_inicial,
        'X_FINAL': roi.x_final,
        'Y_FINAL': roi.y_final,
    }
    for nome, valor in substituicoes.items():
        conteudo = re.sub(rf'^{nome} = \d+$', f'{nome} = {valor}', conteudo, count=1, flags=re.MULTILINE)

    with open(caminho_config, 'w') as f:
        f.write(conteudo)


@app.get("/roi")
def obter_roi():
    """Estado atual da mira, consumido pelo overlay do CameraFeed no frontend."""
    return {
        "x_inicial": config.X_INICIAL,
        "y_inicial": config.Y_INICIAL,
        "x_final": config.X_FINAL,
        "y_final": config.Y_FINAL,
        "frame_width": config.FRAME_WIDTH,
        "frame_height": config.FRAME_HEIGHT,
    }


@app.post("/roi")
def atualizar_roi(roi: ROIAtualizacao):
    """Rota disparada ao salvar o ROI ajustado no frontend (arrastar/redimensionar
    a mira sobre o video ao vivo). Atualiza config em memoria (o pipeline em
    validar_sistema.py le config.X_INICIAL etc a cada frame, entao o efeito e
    imediato), persiste em disco e limpa o buffer de suavizacao para nao
    misturar leituras da mira antiga com a nova."""
    if not (0 <= roi.x_inicial < roi.x_final <= config.FRAME_WIDTH):
        return {"status": "erro", "mensagem": "Coordenadas X invalidas"}
    if not (0 <= roi.y_inicial < roi.y_final <= config.FRAME_HEIGHT):
        return {"status": "erro", "mensagem": "Coordenadas Y invalidas"}

    config.X_INICIAL = roi.x_inicial
    config.Y_INICIAL = roi.y_inicial
    config.X_FINAL = roi.x_final
    config.Y_FINAL = roi.y_final
    resetar_suavizacao()
    persistir_roi_no_disco(roi)

    return {"status": "sucesso", **roi.model_dump()}

@app.get("/analisar")
def rodar_analise():
    """Rota de análise estabilizada com rajada de 3 frames"""
    global ultimo_frame, lock_frame
    
    resultados_agtron = []
    classes_detectadas = []
    desvios_detectados = []
    
    print("\n[IA] Iniciando captura de rajada (3 frames)...")
    
    for i in range(3):
        with lock_frame:
            if ultimo_frame is None:
                time.sleep(0.15)
                continue
            frame_para_analise = ultimo_frame.copy()
        
        agtron, classe, desvio = analisar_para_api(frame_para_analise)
        
        if agtron > 0:
            resultados_agtron.append(agtron)
            classes_detectadas.append(classe)
            desvios_detectados.append(desvio)
            print(f"   -> Frame {i+1}: Agtron {agtron} | Classe: {classe}")
            
        time.sleep(0.15)
        
    if not resultados_agtron:
        print("[IA] FALHA: Nenhum grão validado.")
        return {"score": 0.0, "stage": "Sem grãos", "uniformidade": 0}
        
    media_agtron = round(sum(resultados_agtron) / len(resultados_agtron), 2)
    classe_final = Counter(classes_detectadas).most_common(1)[0][0]
    media_desvio = sum(desvios_detectados) / len(desvios_detectados)
    uniformidade_visual = max(0, 100 - int(media_desvio * 3))
    
    print(f"[IA] FINAL ESTABILIZADO: Score {media_agtron} | Stage: {classe_final}\n")
    
    return {
        "score": float(media_agtron), 
        "stage": str(classe_final), 
        "uniformidade": uniformidade_visual
    }