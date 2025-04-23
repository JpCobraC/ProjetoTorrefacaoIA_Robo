import torch
import torch.nn as nn

classes_torra = ['clara', 'media', 'escura']

class TorraCNN(nn.Module):
    def __init__(self):
        super().__init__()
        self.model = nn.Sequential(
            nn.Conv2d(3, 16, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(16, 32, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
            nn.Flatten(),
            nn.Linear(32 * 16 * 16, 64), nn.ReLU(),
            nn.Linear(64, 3)
        )
    def forward(self, x):
        return self.model(x)

modelo_cnn = TorraCNN()
modelo_cnn.load_state_dict(torch.load("cnn/modelo_torra.pt", map_location="cpu"))
modelo_cnn.eval()

def classificar_torra(tensor_crop):
    with torch.no_grad():
        output = modelo_cnn(tensor_crop)
        idx = torch.argmax(output, 1).item()
        return classes_torra[idx]
