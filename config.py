# No arquivo: config.py
import os
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), '.env.local')
load_dotenv(dotenv_path=dotenv_path)

ROBOFLOW_API_KEY = os.getenv("ROBOFLOW_API_KEY")
ROBOFLOW_MODEL_ID = os.getenv("ROBOFLOW_MODEL_ID")

YOLO_MODEL_FILENAME = 'best.pt'
CNN_MODEL_FILENAME = 'modelo_cnn.tflite'
MODELS_DIR = 'models'
CNN_CLASSES = ['25', '35', '45', '55', '65', '75', '85', '95', 'raw']
YOLO_CONFIDENCE_THRESHOLD = 0.85
CNN_CONFIDENCE_THRESHOLD = 0.85

CAMERA_ID = 0