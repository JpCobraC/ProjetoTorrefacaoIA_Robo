import cv2
import numpy as np
import csv
import os

# --- MIRA DE PRECISAO (ROI) ---
# Mesmos valores usados em analise_torra.py -- edite os dois arquivos juntos
# ao ajustar a mira para evitar pegar a parede metalica da pipoqueira.
X_INICIAL = 260
Y_INICIAL = 70
X_FINAL = 420
Y_FINAL = 220

VIDEO_PATH = 'torra.mp4'
CSV_SAIDA = 'dataset_real.csv'

# Teclas de marcacao manual da fase da torra
FASES = {
    ord('1'): 'Cru',
    ord('2'): 'Clara',
    ord('3'): 'Media',
    ord('4'): 'Escura',
}


def extrair_lab_da_roi(frame):
    """Recorta a mira verde (ROI) e retorna a media dos canais L, a, b em CIELAB."""
    zona_do_cafe = frame[Y_INICIAL:Y_FINAL, X_INICIAL:X_FINAL]
    lab_frame = cv2.cvtColor(zona_do_cafe, cv2.COLOR_BGR2LAB)
    l_channel, a_channel, b_channel = cv2.split(lab_frame)

    l_mean = float(np.mean(l_channel))
    a_mean = float(np.mean(a_channel))
    b_mean = float(np.mean(b_channel))
    return l_mean, a_mean, b_mean


def desenhar_interface(frame, l_mean, a_mean, b_mean, fase_atual):
    """Desenha a mira, os valores de cor e a fase marcada sobre o frame exibido."""
    cv2.rectangle(frame, (X_INICIAL, Y_INICIAL), (X_FINAL, Y_FINAL), (0, 255, 0), 2)

    texto_sensores = f"L:{l_mean:.1f} a:{a_mean:.1f} b:{b_mean:.1f}"
    cv2.putText(frame, texto_sensores, (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    texto_fase = f"Fase atual: {fase_atual if fase_atual else '(nao marcada)'}"
    cv2.putText(frame, texto_fase, (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

    texto_ajuda = "1=Cru 2=Clara 3=Media 4=Escura | Q=Sair"
    cv2.putText(frame, texto_ajuda, (20, frame.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    return frame


def gerar_resumo(linhas):
    """Imprime no terminal a media de L, a, b agrupada por fase marcada manualmente."""
    acumulado = {}
    for linha in linhas:
        fase = linha['fase']
        if not fase:
            continue
        acumulado.setdefault(fase, {'L': [], 'a': [], 'b': []})
        acumulado[fase]['L'].append(linha['L'])
        acumulado[fase]['a'].append(linha['a'])
        acumulado[fase]['b'].append(linha['b'])

    print("\n--- RESUMO DO DATASET COLETADO ---")
    if not acumulado:
        print("Nenhum frame foi marcado com uma fase.")
        return

    for fase, valores in acumulado.items():
        n = len(valores['L'])
        media_l = sum(valores['L']) / n
        media_a = sum(valores['a']) / n
        media_b = sum(valores['b']) / n
        print(f"Fase '{fase}': {n} frames | L={media_l:.2f}  a={media_a:.2f}  b={media_b:.2f}")


def coletar_dataset():
    if not os.path.exists(VIDEO_PATH):
        print(f"Erro: video '{VIDEO_PATH}' nao encontrado nesta pasta.")
        return

    cap = cv2.VideoCapture(VIDEO_PATH)
    if not cap.isOpened():
        print("Erro: Nao foi possivel abrir o video.")
        return

    linhas_csv = []
    fase_atual = None
    numero_frame = 0

    print("Coleta iniciada.")
    print("Pressione 1=Cru, 2=Clara, 3=Media, 4=Escura para marcar a fase atual da torra.")
    print("A marcacao permanece ativa nos proximos frames ate que outra tecla seja pressionada.")
    print("Pressione 'q' a qualquer momento para encerrar e salvar o CSV.")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Fim do video.")
            break

        frame = cv2.resize(frame, (640, 480))
        numero_frame += 1
        timestamp_seg = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0

        l_mean, a_mean, b_mean = extrair_lab_da_roi(frame)

        tecla = cv2.waitKey(30) & 0xFF
        if tecla == ord('q'):
            print("Coleta interrompida pelo usuario.")
            break
        elif tecla in FASES:
            fase_atual = FASES[tecla]
            print(f"[Frame {numero_frame}] Fase marcada: {fase_atual}")

        linhas_csv.append({
            'frame': numero_frame,
            'timestamp': round(timestamp_seg, 3),
            'L': round(l_mean, 3),
            'a': round(a_mean, 3),
            'b': round(b_mean, 3),
            'fase': fase_atual if fase_atual else '',
        })

        frame_exibicao = desenhar_interface(frame.copy(), l_mean, a_mean, b_mean, fase_atual)
        cv2.imshow("Coleta de Dataset Real - Torrefacao IA", frame_exibicao)

    cap.release()
    cv2.destroyAllWindows()

    with open(CSV_SAIDA, 'w', newline='', encoding='utf-8') as arquivo_csv:
        campos = ['frame', 'timestamp', 'L', 'a', 'b', 'fase']
        escritor = csv.DictWriter(arquivo_csv, fieldnames=campos)
        escritor.writeheader()
        escritor.writerows(linhas_csv)

    print(f"\nDataset salvo em '{CSV_SAIDA}' com {len(linhas_csv)} frames.")
    gerar_resumo(linhas_csv)


if __name__ == '__main__':
    coletar_dataset()
