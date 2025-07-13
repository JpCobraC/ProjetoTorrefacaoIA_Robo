import tensorflow as tf
import numpy as np
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
import config

class CNNClassifier:
    def __init__(self, model_filename=None, models_dir=None):
        """
        Inicializa o classificador CNN carregando o modelo TFLite.
        """
        model_filename = model_filename or config.CNN_MODEL_FILENAME
        models_dir = models_dir or config.MODELS_DIR
        model_path = os.path.join(models_dir, model_filename)

        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Modelo CNN não encontrado em {model_path}. Treine ou baixe o modelo primeiro.")

        try:
            self.interpreter = tf.lite.Interpreter(model_path=model_path)
            self.interpreter.allocate_tensors()
            self.input_details = self.interpreter.get_input_details()
            self.output_details = self.interpreter.get_output_details()
            print(f"Classificador CNN carregado de {model_path}")
        except Exception as e:
            print(f"Erro ao carregar o modelo TFLite da CNN: {e}")
            raise e

    def classificar(self, imagem_processada_para_cnn):
        """
        Recebe uma imagem de grão pré-processada e retorna a classe e a confiança.
        """
        if imagem_processada_para_cnn is None:
            return "desconhecido", 0.0

        # Verifica e converte o tipo de dado se necessário
        expected_dtype = self.input_details[0]['dtype']
        if imagem_processada_para_cnn.dtype != expected_dtype:
            imagem_processada_para_cnn = imagem_processada_para_cnn.astype(expected_dtype)

        try:
            self.interpreter.set_tensor(self.input_details[0]['index'], imagem_processada_para_cnn)
            self.interpreter.invoke()
            output_data = self.interpreter.get_tensor(self.output_details[0]['index'])
        except Exception as e:
            print(f"Erro durante a inferência da CNN: {e}")
            return "erro_inferencia", 0.0

        # Processa o resultado da classificação
        classe_predita_idx = np.argmax(output_data[0])
        confianca = float(output_data[0, classe_predita_idx])
        nivel_torra = "incerto"

        # Garante que o índice da classe é válido antes de acessar a lista
        if classe_predita_idx < len(config.CNN_CLASSES):
            # Verifica se a confiança está acima do limiar definido no config
            if confianca >= config.CNN_CONFIDENCE_THRESHOLD:
                nivel_torra = config.CNN_CLASSES[classe_predita_idx]
            else:
                # Se a confiança for baixa, retorna 'incerto' mas indica a classe provável
                nivel_torra = f"incerto ({config.CNN_CLASSES[classe_predita_idx]})"

        return nivel_torra, confianca