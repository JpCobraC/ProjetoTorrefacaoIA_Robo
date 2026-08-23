
# Automação de torra de café — estimativa de Agtron via visão computacional

Sistema que estima o nível de torra (escala Agtron: Cru/Clara/Media/Escura) a partir
de uma mira (ROI) fixa apontada para o grão, convertendo a imagem para o espaço de cor
CIELAB e usando um modelo de Regressão Linear (scikit-learn) treinado com dados reais
de bancada para prever o valor Agtron a partir de L, a, b.

## Componentes

- **`api_teste.py`** — servidor FastAPI (porta 8000) que expõe a rota `/analisar`,
  consumida pelo frontend React em `frontend-torrador/`.
- **`validar_sistema.py`** — pipeline de análise (ROI + CIELAB + `modelo_agtron_linear_interpolado.pkl`)
  usado pela API.
- **`coletar_dataset_real.py`** / **`gerar_dataset_interpolado.py`** / **`treinar_novo.py`** —
  fluxo de coleta de dados de bancada, geração do dataset interpolado e treino dos modelos.
- **`analise_torra.py`** — ferramenta de monitoramento visual standalone (exibe a ROI e o
  Agtron predito em tempo real sobre o vídeo).

## Rodando

```bash
pip install -r requirements.txt
python3 -m uvicorn api_teste:app --host 0.0.0.0 --port 8000 --reload
```

O frontend em `frontend-torrador/` consome a API em `http://localhost:8000`.
