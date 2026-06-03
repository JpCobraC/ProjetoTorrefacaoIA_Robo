import cv2
import threading
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import validar_sistema

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. Liga a câmara (0 é a webcam padrão. Se falhar, tente 1 ou 2)
camera = cv2.VideoCapture(0)

# Variável global para guardar a "fotocópia" e um "Cadeado" (Lock) de segurança
ultimo_frame = None
lock_frame = threading.Lock()

def gerar_frames():
    """Loop infinito que lê a câmara e gera o vídeo"""
    global ultimo_frame
    
    while True:
        sucesso, frame = camera.read()
        if not sucesso:
            break
            
        # Guarda uma cópia segura do frame para quando o botão for clicado
        with lock_frame:
            ultimo_frame = frame.copy()

        # Codifica o frame para formato de imagem JPEG
        _, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()

        # Envia a imagem empacotada no formato de vídeo contínuo (MJPEG)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.get("/video_feed")
def video_feed():
    """Rota que o React usa na tag <img> para ver o vídeo ao vivo"""
    return StreamingResponse(gerar_frames(), media_type="multipart/x-mixed-replace; boundary=frame")

@app.get("/analisar")
def rodar_analise():
    """Rota que o React chama quando clica no botão"""
    global ultimo_frame
    
    print("Capturando frame exato para análise...")
    
    # Pega o frame atual protegido pelo cadeado
    with lock_frame:
        if ultimo_frame is None:
            return {"score": 0.0, "stage": "Câmara desligada", "uniformidade": 0}
        frame_para_analise = ultimo_frame.copy()
    
    # Envia a fotocópia para a Inteligência Artificial
    agtron, classe, desvio = validar_sistema.analisar_para_api(frame_para_analise)
    
    uniformidade_visual = max(0, 100 - int(desvio * 3))

    return {
        "score": float(agtron),
        "stage": str(classe),
        "uniformidade": uniformidade_visual
    }

@app.get("/status")
def checar_status():
    return {"status": "online"}