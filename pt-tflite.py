import os
import glob
import tensorflow as tf
import onnx
import numpy as np
from ultralytics import YOLO

INPUT_PT_DIR = 'train/yolo'
OUTPUT_DIR = 'yolo'
IMG_SIZE = 640
APPLY_QUANTIZATION = True

print(f"--- Iniciando a conversão de modelo YOLOv8 (.pt) para TFLite ---")
print(f"Buscando modelo .pt em: {INPUT_PT_DIR}")
print(f"Salvando modelos de saída em: {OUTPUT_DIR}")
print(f"Tamanho da imagem para exportação: {IMG_SIZE}x{IMG_SIZE}")
print(f"Quantização de faixa dinâmica ativada: {APPLY_QUANTIZATION}")

os.makedirs(INPUT_PT_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

pt_files = glob.glob(os.path.join(INPUT_PT_DIR, '*.pt'))

if not pt_files:
    print(f"Erro: Nenhum arquivo .pt encontrado em '{INPUT_PT_DIR}'. Por favor, coloque seu modelo YOLOv8 (.pt) lá.")
    exit()

pt_files.sort(key=os.path.getmtime, reverse=True)
input_model_path = pt_files[0]

model_name_base = os.path.splitext(os.path.basename(input_model_path))[0]
onnx_output_path = os.path.join(OUTPUT_DIR, f'{model_name_base}.onnx')
saved_model_output_path = os.path.join(OUTPUT_DIR, f'{model_name_base}_saved_model')
tflite_output_path = os.path.join(OUTPUT_DIR, f'{model_name_base}.tflite')

print(f"\nModelo .pt encontrado para conversão: {input_model_path}")

print("\n--- Exportando o modelo para ONNX ---")
try:
    model = YOLO(input_model_path)
    model.export(format='onnx', imgsz=IMG_SIZE, dynamic=False, opset=17)
    
    default_onnx_path = os.path.join(os.path.dirname(input_model_path), f'{model_name_base}.onnx')
    if not os.path.exists(default_onnx_path):
        default_onnx_path = f'{model_name_base}.onnx'

    if os.path.exists(default_onnx_path):
        os.rename(default_onnx_path, onnx_output_path)
        print(f"Modelo ONNX salvo em: {onnx_output_path}")
    else:
        print(f"Erro: Não foi possível encontrar o arquivo ONNX gerado em {default_onnx_path}. Verifique o diretório de trabalho.")
        exit()

except Exception as e:
    print(f"Erro ao exportar para ONNX: {e}")
    exit()

print("\n--- Convertendo ONNX para TensorFlow SavedModel ---")
try:
    from onnx_tf.backend import prepare
    onnx_model = onnx.load(onnx_output_path)
    tf_rep = prepare(onnx_model)
    tf_rep.export_graph(saved_model_output_path)
    print(f"Modelo ONNX convertido para TensorFlow SavedModel em: {saved_model_output_path}")
except Exception as e:
    print(f"Erro ao converter ONNX para SavedModel: {e}")
    exit()

print("\n--- Convertendo TensorFlow SavedModel para TFLite ---")
try:
    converter = tf.lite.TFLiteConverter.from_saved_model(saved_model_output_path)

    if APPLY_QUANTIZATION:
        print("Aplicando quantização de faixa dinâmica (dynamic range quantization)...")
        converter.optimizations = [tf.lite.Optimize.DEFAULT]

    tflite_model = converter.convert()

    with open(tflite_output_path, 'wb') as f:
        f.write(tflite_model)

    print(f"Modelo TFLite salvo em: {tflite_output_path}")
    print(f"\n--- Conversão concluída com sucesso! O modelo {os.path.basename(tflite_output_path)} está pronto em '{OUTPUT_DIR}' ---")

except Exception as e:
    print(f"Erro ao converter SavedModel para TFLite: {e}")
    exit()