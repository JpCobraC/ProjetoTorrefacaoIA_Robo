
# Automação de torra de café — Visão Computacional e Telemetria

Sistema integrado para monitoramento e análise de torra de café. O projeto é composto por dois módulos principais operando em conjunto:
1. Estimativa do nível de torra (escala Agtron) via visão computacional.
2. Telemetria térmica em tempo real (ESP32) integrada ao software Artisan via WebSocket.

## Módulo 1: Visão Computacional (Estimativa de Agtron)

Sistema que estima o nível de torra a partir de uma mira (ROI) fixa apontada para o grão, convertendo a imagem para o espaço de cor CIELAB e usando um modelo de Regressão Linear (scikit-learn) treinado com dados reais de bancada para prever o valor Agtron a partir de L, a, b.

- **`api_teste.py`** — servidor FastAPI (porta 8000) que expõe a rota `/analisar`,
  consumida pelo frontend React em `frontend-torrador/`.
- **`validar_sistema.py`** — pipeline de análise (ROI + CIELAB + `modelo_agtron_linear_interpolado.pkl`)
  usado pela API.
- **`coletar_dataset_real.py`** / **`gerar_dataset_interpolado.py`** / **`treinar_novo.py`** —
  fluxo de coleta de dados de bancada, geração do dataset interpolado e treino dos modelos.
- **`analise_torra.py`** — ferramenta de monitoramento visual standalone (exibe a ROI e o
  Agtron predito em tempo real sobre o vídeo).

## Módulo 2: Telemetria Térmica (ESP32 + Artisan)

Firmware em C++ para a placa LilyGO TTGO T-Beam (ESP32) que atua como um servidor WebSocket. Ele lê a temperatura do grão (BT) utilizando o módulo termopar MAX31855 e responde às requisições JSON do software Artisan.

### Hardware e Pinagem
- **Microcontrolador:** LilyGO TTGO T-Beam (ESP32)
- **Módulo Amplificador:** MAX31855
- **Sensor Térmico:** Termopar Tipo K (haste inserida no torrador)

**Conexões SPI (Padrão atual no código):**
> *Nota: A pinagem abaixo reflete a configuração atual no `main.cpp`, mas pode ser remapeada via software para outros pinos livres dependendo da revisão da sua placa T-Beam.*
- **MISO (DO):** Pino 13
- **CS:** Pino 15
- **SCK (CLK):** Pino 14

## Rodando:

```bash
pip install -r requirements.txt
python3 -m uvicorn api_teste:app --host 0.0.0.0 --port 8000 --reload
```

O frontend em `frontend-torrador/` consome a API em `http://localhost:8000`.

## Configurando o ESP32:

* **Entrar na pasta do firmware**

```bash
cd esp32_artisan
```


* **Fazer o upload para o ESP32**

```bash
~/.platformio/penv/bin/pio run -t upload
```

* **Abrir o monitor serial para acompanhar os logs e descobrir o IP**

```bash
~/.platformio/penv/bin/pio device monitor
```