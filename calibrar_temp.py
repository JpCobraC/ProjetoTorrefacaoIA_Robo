# calibrar_temp.py
#
# Script TEMPORARIO e DESCARTAVEL para calibrar a ROI (mira) definida em
# config.py sobre o video torra_v2.mp4, sem precisar rodar o pipeline
# completo (analise_torra.py) so para ver se o retangulo caiu em cima dos
# graos. Pode ser apagado assim que a mira estiver validada.
#
# Uso: ajuste X_INICIAL/Y_INICIAL/X_FINAL/Y_FINAL em config.py, rode este
# script, veja se o retangulo verde esta em cima dos graos, feche a janela
# (qualquer tecla) e repita ate acertar.

import cv2

from config import X_INICIAL, Y_INICIAL, X_FINAL, Y_FINAL

VIDEO_PATH = 'torra_v2.mp4'
FRAME_ALVO = 100

# Mesmo resize (640x480) que analise_torra.py e coletar_dataset_real.py
# aplicam em cada frame ANTES de recortar a ROI. Sem repetir esse resize
# aqui, o retangulo apareceria na escala errada em relacao ao que o
# pipeline de verdade usa para calcular L/a/b.
LARGURA_PIPELINE = 640
ALTURA_PIPELINE = 480


def calibrar():
    cap = cv2.VideoCapture(VIDEO_PATH)
    if not cap.isOpened():
        print(f"Erro: nao foi possivel abrir '{VIDEO_PATH}'.")
        return

    largura_real = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    altura_real = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"Resolucao real do video: {largura_real}x{altura_real}")

    cap.set(cv2.CAP_PROP_POS_FRAMES, FRAME_ALVO)
    ret, frame = cap.read()
    cap.release()

    if not ret:
        print(f"Erro: nao foi possivel capturar o frame {FRAME_ALVO} (o video tem frames suficientes?).")
        return

    frame = cv2.resize(frame, (LARGURA_PIPELINE, ALTURA_PIPELINE))

    print(
        f"ROI atual (config.py), ja no espaco {LARGURA_PIPELINE}x{ALTURA_PIPELINE} "
        f"usado pelo pipeline:"
    )
    print(f"  X_INICIAL={X_INICIAL}  Y_INICIAL={Y_INICIAL}  X_FINAL={X_FINAL}  Y_FINAL={Y_FINAL}")

    if X_FINAL > LARGURA_PIPELINE or Y_FINAL > ALTURA_PIPELINE:
        print(
            f"AVISO: a ROI ultrapassa os limites do frame redimensionado "
            f"({LARGURA_PIPELINE}x{ALTURA_PIPELINE}) -- o retangulo vai aparecer cortado "
            f"na janela. Ajuste os valores em config.py."
        )

    cv2.rectangle(frame, (X_INICIAL, Y_INICIAL), (X_FINAL, Y_FINAL), (0, 255, 0), 2)
    cv2.putText(
        frame,
        f"frame {FRAME_ALVO} | ROI: ({X_INICIAL},{Y_INICIAL}) -> ({X_FINAL},{Y_FINAL})",
        (10, 20),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (0, 255, 0),
        1,
    )

    cv2.imshow("Calibracao da ROI - pressione qualquer tecla para fechar", frame)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


if __name__ == '__main__':
    calibrar()
