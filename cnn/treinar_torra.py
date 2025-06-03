import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D, Dropout
from tensorflow.keras.models import Model
from tensorflow.keras.optimizers import Adam
import matplotlib.pyplot as plt
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config

def criar_modelo_cnn(num_classes, input_shape=(224, 224, 3)):
    base_model = MobileNetV2(weights='imagenet', include_top=False, input_shape=input_shape)
    base_model.trainable = False

    x = base_model.output
    x = GlobalAveragePooling2D()(x)
    x = Dense(128, activation='relu')(x)
    x = Dropout(0.5)(x)
    predictions = Dense(num_classes, activation='softmax')(x)

    model = Model(inputs=base_model.input, outputs=predictions)
    return model

def treinar():
    print(f"Usando TensorFlow versão: {tf.__version__}")
    print(f"Diretório de dados de treino CNN: {config.CNN_TRAIN_DATA_PATH}")
    print(f"Número de classes CNN: {len(config.CNN_CLASSES)}")

    if not os.path.exists(config.CNN_TRAIN_DATA_PATH):
        print(f"ERRO: Diretório de dados de treino CNN não encontrado: {config.CNN_TRAIN_DATA_PATH}")
        print("Certifique-se de criar subpastas para cada classe de torra dentro deste diretório.")
        return

    train_datagen = ImageDataGenerator(
        rescale=1./255,
        rotation_range=30,
        width_shift_range=0.2,
        height_shift_range=0.2,
        shear_range=0.2,
        zoom_range=0.2,
        horizontal_flip=True,
        fill_mode='nearest',
        validation_split=0.2
    )

    img_height, img_width = config.CNN_INPUT_SIZE

    train_generator = train_datagen.flow_from_directory(
        config.CNN_TRAIN_DATA_PATH,
        target_size=(img_height, img_width),
        batch_size=config.TRAIN_BATCH_SIZE,
        class_mode='categorical',
        subset='training',
        classes=config.CNN_CLASSES
    )

    validation_generator = train_datagen.flow_from_directory(
        config.CNN_TRAIN_DATA_PATH,
        target_size=(img_height, img_width),
        batch_size=config.TRAIN_BATCH_SIZE,
        class_mode='categorical',
        subset='validation',
        classes=config.CNN_CLASSES
    )

    if train_generator.num_classes == 0:
        print("ERRO: Nenhuma classe encontrada nos geradores de dados. Verifique a estrutura do seu dataset.")
        return

    model = criar_modelo_cnn(num_classes=len(config.CNN_CLASSES), input_shape=(img_height, img_width, 3))

    model.compile(optimizer=Adam(learning_rate=config.TRAIN_LEARNING_RATE),
                  loss='categorical_crossentropy',
                  metrics=['accuracy'])

    print("Iniciando treinamento da CNN...")
    history = model.fit(
        train_generator,
        epochs=config.TRAIN_EPOCHS_CNN,
        validation_data=validation_generator,
        steps_per_epoch=train_generator.samples // config.TRAIN_BATCH_SIZE,
        validation_steps=validation_generator.samples // config.TRAIN_BATCH_SIZE
    )

    if not os.path.exists(config.MODELS_DIR):
        os.makedirs(config.MODELS_DIR)
    keras_model_path = os.path.join(config.MODELS_DIR, config.CNN_MODEL_FILENAME.replace('.tflite', '.h5'))
    model.save(keras_model_path)
    print(f"Modelo Keras salvo em: {keras_model_path}")

    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    tflite_model = converter.convert()

    tflite_model_path = os.path.join(config.MODELS_DIR, config.CNN_MODEL_FILENAME)
    with open(tflite_model_path, 'wb') as f:
        f.write(tflite_model)
    print(f"Modelo TFLite salvo em: {tflite_model_path}")

    acc = history.history['accuracy']
    val_acc = history.history['val_accuracy']
    loss = history.history['loss']
    val_loss = history.history['val_loss']
    epochs_range = range(len(acc))

    plt.figure(figsize=(12, 4))
    plt.subplot(1, 2, 1)
    plt.plot(epochs_range, acc, label='Training Accuracy')
    plt.plot(epochs_range, val_acc, label='Validation Accuracy')
    plt.legend(loc='lower right')
    plt.title('Training and Validation Accuracy')

    plt.subplot(1, 2, 2)
    plt.plot(epochs_range, loss, label='Training Loss')
    plt.plot(epochs_range, val_loss, label='Validation Loss')
    plt.legend(loc='upper right')
    plt.title('Training and Validation Loss')

    plot_filename = os.path.join(config.MODELS_DIR, 'cnn_training_history.png')
    plt.savefig(plot_filename)
    print(f"Gráfico do histórico de treinamento salvo em: {plot_filename}")

if __name__ == '__main__':
    treinar()