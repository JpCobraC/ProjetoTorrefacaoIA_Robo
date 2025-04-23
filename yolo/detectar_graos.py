from ultralytics import YOLO
import cv2
import os

modelo_yolo = YOLO("yolo/pesos/graos_best.pt")

def detectar_graos(imagem_bgr):
    resultados = modelo_yolo(imagem_bgr)
    boxes = []
    for r in resultados:
        for box in r.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            boxes.append((x1, y1, x2, y2))
    return boxes