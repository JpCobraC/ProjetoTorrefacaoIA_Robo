from ultralytics import YOLO

modelo = YOLO("yolov8n.pt")

modelo.train(
    data="graos_dataset/data.yaml",
    epochs=50,
    imgsz=640,
    batch=8,
    device="cpu",
    name="treinamento_graos"
)
