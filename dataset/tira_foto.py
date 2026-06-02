import cv2
import time

camera = cv2.VideoCapture(2)

# Ajusta resolução (exemplo: 1280x720)
camera.set(cv2.CAP_PROP_FRAME_WIDTH, 800)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 600)

# Ajusta exposição
camera.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25) 
camera.set(cv2.CAP_PROP_EXPOSURE, -6)

for i in range(50):
    if i in [10, 20, 30, 40]:
        time.sleep(5)
    ret, frame = camera.read()
    cv2.imwrite(f'./dataset/25/25({i}).jpg', frame)
    print(f"foto {i}")

camera.release()