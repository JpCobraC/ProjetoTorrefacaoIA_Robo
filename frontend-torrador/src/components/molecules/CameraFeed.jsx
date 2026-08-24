import React, { useEffect, useRef, useState } from 'react';
import { API_BASE_URL } from '../../utils/config';

// Tamanho minimo (em pixels do frame, nao da tela) que a mira pode ter ao
// redimensionar -- evita que o usuario arraste o cantinho ate a ROI virar um
// ponto e a analise de cor perder qualquer grao dentro dela.
const TAMANHO_MINIMO_ROI = 20;

// Feed de video ao vivo da camera apontada para o cafe, com a mira (ROI) que
// o backend usa para medir a cor (CIELAB -> Agtron) desenhada por cima. Sem
// isso o operador nao tinha como saber onde, dentro do frame, o sistema
// estava de fato medindo -- so descobria via tentativa e erro editando
// config.py e reiniciando o servidor. Agora a mira e visivel sempre e, em
// modo de ajuste, arrastavel/redimensionavel direto sobre o video, com o
// resultado salvo no backend (rota /roi) e refletido na proxima leitura.
export const CameraFeed = () => {
  const [roi, setRoi] = useState(null);
  const [roiSalvo, setRoiSalvo] = useState(null);
  const [frame, setFrame] = useState({ largura: 640, altura: 480 });
  const [editando, setEditando] = useState(false);
  const [salvando, setSalvando] = useState(false);
  const [erro, setErro] = useState(null);

  const caixaVideoRef = useRef(null);
  const arrastoRef = useRef(null);

  useEffect(() => {
    const carregarRoi = async () => {
      try {
        const resposta = await fetch(`${API_BASE_URL}/roi`);
        const dados = await resposta.json();
        const roiCarregado = {
          xInicial: dados.x_inicial,
          yInicial: dados.y_inicial,
          xFinal: dados.x_final,
          yFinal: dados.y_final,
        };
        setRoi(roiCarregado);
        setRoiSalvo(roiCarregado);
        setFrame({ largura: dados.frame_width, altura: dados.frame_height });
      } catch (e) {
        console.error('Erro ao carregar ROI:', e);
      }
    };
    carregarRoi();
  }, []);

  // Converte um clientX/clientY do mouse para coordenadas de pixel dentro do
  // frame (0..frame.largura / 0..frame.altura), usando o retangulo real do
  // elemento de video na tela -- assim a conversao continua correta em
  // qualquer tamanho de card/janela, ja que a caixa de video mantem sempre a
  // proporcao 4:3 nativa da camera (ver o wrapper com aspectRatio abaixo).
  const paraCoordenadasDoFrame = (clientX, clientY) => {
    const retangulo = caixaVideoRef.current.getBoundingClientRect();
    const fracaoX = (clientX - retangulo.left) / retangulo.width;
    const fracaoY = (clientY - retangulo.top) / retangulo.height;
    return {
      x: Math.round(Math.min(Math.max(fracaoX, 0), 1) * frame.largura),
      y: Math.round(Math.min(Math.max(fracaoY, 0), 1) * frame.altura),
    };
  };

  const iniciarArrasto = (evento, modo) => {
    if (!editando) return;
    evento.preventDefault();
    evento.stopPropagation();
    arrastoRef.current = {
      modo, // 'mover' ou 'redimensionar'
      inicio: paraCoordenadasDoFrame(evento.clientX, evento.clientY),
      roiInicial: roi,
    };
    window.addEventListener('mousemove', moverArrasto);
    window.addEventListener('mouseup', finalizarArrasto);
  };

  const moverArrasto = (evento) => {
    if (!arrastoRef.current) return;
    const { modo, inicio, roiInicial } = arrastoRef.current;
    const atual = paraCoordenadasDoFrame(evento.clientX, evento.clientY);
    const deltaX = atual.x - inicio.x;
    const deltaY = atual.y - inicio.y;

    if (modo === 'mover') {
      const largura = roiInicial.xFinal - roiInicial.xInicial;
      const altura = roiInicial.yFinal - roiInicial.yInicial;
      const xInicial = Math.min(Math.max(roiInicial.xInicial + deltaX, 0), frame.largura - largura);
      const yInicial = Math.min(Math.max(roiInicial.yInicial + deltaY, 0), frame.altura - altura);
      setRoi({ xInicial, yInicial, xFinal: xInicial + largura, yFinal: yInicial + altura });
    } else {
      const xFinal = Math.min(Math.max(roiInicial.xFinal + deltaX, roiInicial.xInicial + TAMANHO_MINIMO_ROI), frame.largura);
      const yFinal = Math.min(Math.max(roiInicial.yFinal + deltaY, roiInicial.yInicial + TAMANHO_MINIMO_ROI), frame.altura);
      setRoi({ ...roiInicial, xFinal, yFinal });
    }
  };

  const finalizarArrasto = () => {
    arrastoRef.current = null;
    window.removeEventListener('mousemove', moverArrasto);
    window.removeEventListener('mouseup', finalizarArrasto);
  };

  const handleSalvar = async () => {
    setSalvando(true);
    setErro(null);
    try {
      const resposta = await fetch(`${API_BASE_URL}/roi`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          x_inicial: roi.xInicial,
          y_inicial: roi.yInicial,
          x_final: roi.xFinal,
          y_final: roi.yFinal,
        }),
      });
      const dados = await resposta.json();
      if (dados.status !== 'sucesso') {
        setErro(dados.mensagem || 'Falha ao salvar a mira');
        return;
      }
      setRoiSalvo(roi);
      setEditando(false);
    } catch (e) {
      setErro('Servidor indisponível');
    } finally {
      setSalvando(false);
    }
  };

  const handleCancelar = () => {
    setRoi(roiSalvo);
    setErro(null);
    setEditando(false);
  };

  // Percentuais (nao pixels) para o retangulo da mira acompanhar o video em
  // qualquer resolucao de tela, ja que a caixa de video tem sempre a mesma
  // proporcao do frame (ver aspectRatio no wrapper).
  const estiloRoi = roi
    ? {
        left: `${(roi.xInicial / frame.largura) * 100}%`,
        top: `${(roi.yInicial / frame.altura) * 100}%`,
        width: `${((roi.xFinal - roi.xInicial) / frame.largura) * 100}%`,
        height: `${((roi.yFinal - roi.yInicial) / frame.altura) * 100}%`,
      }
    : null;

  return (
    <div className="entrada-card card-torra flex flex-col flex-1 bg-[var(--cor-superficie)] rounded-3xl border border-black/20 overflow-hidden w-full">

      <div className="flex items-center justify-between px-5 py-3 border-b border-black/20">
        <span className="text-xs font-semibold uppercase tracking-wider text-[var(--cor-texto-secundario)]">
          Mira de leitura (ROI)
        </span>

        {!editando ? (
          <button
            onClick={() => setEditando(true)}
            disabled={!roi}
            className="text-xs font-semibold px-3 py-1.5 rounded-full border border-[var(--cor-superficie-clara)] text-[var(--cor-texto-secundario)] hover:bg-[var(--cor-superficie-clara)] hover:text-[var(--cor-texto)] transition-all disabled:opacity-40"
          >
            Ajustar mira
          </button>
        ) : (
          <div className="flex items-center gap-2">
            {erro && <span className="text-xs text-[var(--cor-alerta)]">{erro}</span>}
            <button
              onClick={handleCancelar}
              className="text-xs font-semibold px-3 py-1.5 rounded-full border border-[var(--cor-superficie-clara)] text-[var(--cor-texto-secundario)] hover:bg-[var(--cor-superficie-clara)] transition-all"
            >
              Cancelar
            </button>
            <button
              onClick={handleSalvar}
              disabled={salvando}
              className="text-xs font-semibold px-3 py-1.5 rounded-full text-[var(--cor-fundo)] bg-[var(--cor-sucesso)] hover:opacity-90 transition-all disabled:opacity-50"
            >
              {salvando ? 'A salvar...' : 'Salvar mira'}
            </button>
          </div>
        )}
      </div>

      <div className="flex-1 min-h-[320px] bg-[#120D09] relative overflow-hidden flex items-center justify-center">

        {/* Caixa com a proporcao nativa do frame (4:3 = 640x480): garante que
            o retangulo da mira, calculado em percentual sobre essa caixa,
            fique pixel-a-pixel alinhado com a imagem real, mesmo que o card
            ao redor tenha outra proporcao (letterbox nas laterais/topo). */}
        <div
          ref={caixaVideoRef}
          className="relative max-w-full max-h-full"
          style={{ aspectRatio: `${frame.largura} / ${frame.altura}`, width: '100%' }}
        >
          <img
            src={`${API_BASE_URL}/video_feed`}
            alt="Feed do Torrador"
            className="w-full h-full object-cover select-none"
            draggable={false}
          />

          {estiloRoi && (
            <div
              className="absolute box-border"
              style={{
                ...estiloRoi,
                border: `2px solid var(--cor-sucesso)`,
                backgroundColor: editando ? 'rgba(107, 142, 78, 0.15)' : 'transparent',
                cursor: editando ? 'move' : 'default',
              }}
              onMouseDown={(e) => iniciarArrasto(e, 'mover')}
            >
              {editando && (
                <div
                  onMouseDown={(e) => iniciarArrasto(e, 'redimensionar')}
                  className="absolute -right-1.5 -bottom-1.5 w-4 h-4 rounded-full border-2 border-[var(--cor-fundo)]"
                  style={{ backgroundColor: 'var(--cor-sucesso)', cursor: 'nwse-resize' }}
                />
              )}
            </div>
          )}

          <span className="absolute bottom-4 left-4 bg-black/40 backdrop-blur-md px-3 py-1.5 rounded-full border border-white/10 text-[var(--cor-texto)] text-xs font-medium tracking-wide">
            Câmera ao vivo
          </span>

          <span className="absolute bottom-4 right-4 bg-black/40 backdrop-blur-md px-3 py-1.5 rounded-full border border-white/10 text-[var(--cor-texto-secundario)] text-xs font-mono">
            ML: CIELAB→Agtron
          </span>
        </div>
      </div>
    </div>
  );
};
