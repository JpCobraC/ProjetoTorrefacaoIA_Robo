import cv2
import torchvision.transforms as transforms
from PIL import Image
import torch

transform_crop = transforms.Compose([
    transforms.Resize((64, 64)),
    transforms.ToTensor()
])

def bgr_para_hsv(frame_bgr):
    return cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)

def preparar_crop(crop_frame):
    img_pil = Image.fromarray(crop_frame)
    return transform_crop(img_pil).unsqueeze(0) 