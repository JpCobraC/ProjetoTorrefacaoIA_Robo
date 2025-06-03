import tensorflow as tf
import numpy as np
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config

class CNNClassifier:
    def __init__(self, model_filename=config.CNN_MODEL_FILENAME, models_dir=config.MODELS_DIR):
        model_path = os.path.join(models_dir, model_filename)
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Modelo CNN não encontrado em {model_path}. Treine o modelo primeiro.")

        self.interpreter = tf.lite.Interpreter(model_path=model_path)
        self.interpreter.allocate_tensors()
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()
        print(f"Classificador CNN carregado de {model_path}")
        print(f"Detalhes da entrada CNN: {self.input_details}")
        print(f"Detalhes da saída CNN: {self.output_details}")


    def classificar(self, imagem_processada_para_cnn):
        if imagem_processada_para_cnn is None:
            return "desconhecido", 0.0

        expected_dtype = self.input_details[0]['dtype']
        if imagem_processada_para_cnn.dtype != expected_dtype:
            imagem_processada_para_cnn = imagem_processada_para_cnn.astype(expected_dtype)

        try:
            self.interpreter.set_tensor(self.input_details[0]['index'], imagem_processada_para_cnn)
            self.interpreter.invoke()
            output_data = self.interpreter.get_tensor(self.output_details[0]['index'])
        except Exception as e:
            print(f"Erro durante a inferência da CNN: {e}")
            print(f"Shape da imagem de entrada: {imagem_processada_para_cnn.shape}, dtype: {imagem_processada_para_cnn.dtype}")
            print(f"Detalhes da entrada do modelo: {self.input_details[0]}")
            return "erro_inferencia", 0.0


        classe_predita_idx = np.argmax(output_data[0])
        confianca = float(output_data[0, classe_predita_idx])

        if confianca >= config.CNN_CONFIDENCE_THRESHOLD and classe_predita_idx < len(config.CNN_CLASSES):
            nivel_torra = config.CNN_CLASSES[classe_predita_idx]
        else:
            nivel_torra = "incerto"
            if classe_predita_idx < len(config.CNN_CLASSES):
                 nivel_torra = f"incerto ({config.CNN_CLASSES[classe_predita_idx]})"


        return nivel_torra, confianca

if __name__ == '__main__':
    print("Testando o classificador CNN...")
    try:
        dummy_image_data = np.random.rand(1, config.CNN_INPUT_SIZE[0], config.CNN_INPUT_SIZE[1], 3).astype(np.float32)

        model_file = os.path.join(config.MODELS_DIR, config.CNN_MODEL_FILENAME)
        if not os.path.exists(model_file):
            print(f"Modelo de teste {model_file} não encontrado. Crie um placeholder ou treine um modelo.")
            if not os.path.exists(config.MODELS_DIR): os.makedirs(config.MODELS_DIR)
            print("Pulando teste de inferência pois o modelo real não foi encontrado.")

        else:
            classifier = CNNClassifier()
            nivel, conf = classifier.classificar(dummy_image_data)
            print(f"Classificação da imagem dummy: Nível={nivel}, Confiança={conf:.2f}")

    except Exception as e:
        print(f"Erro no teste do classificador CNN: {e}")