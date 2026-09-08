import React from 'react';
import { AgtronBadge } from '../atoms/AgtronBadge';

// Extremos da escala Agtron que o gauge representa: 95 = grao cru (dourado),
// 35 = torra escura (marrom quase preto). Mesmos limiares usados pelo
// backend (validar_sistema.py) para classificar a fase.
const AGTRON_CRU = 95;
const AGTRON_ESCURA = 35;

// Converte o score Agtron atual numa posicao de 0 a 100% ao longo do arco,
// do lado do cru (esquerda) para o lado da torra escura (direita).
const calcularPosicaoPercentual = (score) => {
  if (!score) return 0;
  const bruto = ((AGTRON_CRU - score) / (AGTRON_CRU - AGTRON_ESCURA)) * 100;
  return Math.min(100, Math.max(0, bruto));
};

// Geometria do gauge: um arco semicircular (180 graus), varrendo da esquerda
// (angulo 180, "Cru") ate a direita (angulo 0, "Escura"), passando pelo topo
// (angulo 90). cx/cy/r ficam em unidades do viewBox do SVG abaixo.
const CX = 120;
const CY = 128;
const R = 90;
const ESPESSURA_ARCO = 18;

// As 4 faixas reais de torra que compoe o arco, em ordem esquerda->direita.
// Cada uma cobre 45 graus (180 / 4), usando os tokens de cor do tema --
// --cor-gauge-clara e --cor-gauge-escura-profunda foram adicionados em
// App.css especificamente para dar ao gauge 4 tons distintos de verdade,
// em vez do degrade continuo que a barra linear anterior usava.
const FAIXAS_GAUGE = [
  { id: 'cru', anguloInicial: 180, anguloFinal: 135, cor: 'var(--cor-cru)' },
  { id: 'clara', anguloInicial: 135, anguloFinal: 90, cor: 'var(--cor-gauge-clara)' },
  { id: 'media', anguloInicial: 90, anguloFinal: 45, cor: 'var(--cor-torrada)' },
  { id: 'escura', anguloInicial: 45, anguloFinal: 0, cor: 'var(--cor-gauge-escura-profunda)' },
];

const paraRadianos = (graus) => (graus * Math.PI) / 180;

// Ponto sobre a circunferencia de raio r, centrado em (cx, cy), no angulo
// dado (convencao matematica: 0 = direita, 90 = topo, 180 = esquerda).
const pontoNoArco = (cx, cy, r, anguloGraus) => ({
  x: cx + r * Math.cos(paraRadianos(anguloGraus)),
  y: cy - r * Math.sin(paraRadianos(anguloGraus)),
});

// Monta o "d" de um <path> de arco SVG entre dois angulos. sweep-flag fixo
// em 1 porque, na varredura 180 -> 0 (esquerda -> topo -> direita) que este
// gauge usa, o arco sempre percorre o caminho "horario" na tela.
const trajetoArco = (cx, cy, r, anguloInicial, anguloFinal) => {
  const inicio = pontoNoArco(cx, cy, r, anguloInicial);
  const fim = pontoNoArco(cx, cy, r, anguloFinal);
  const arcoGrande = Math.abs(anguloInicial - anguloFinal) > 180 ? 1 : 0;
  return `M ${inicio.x} ${inicio.y} A ${r} ${r} 0 ${arcoGrande} 1 ${fim.x} ${fim.y}`;
};

// Comprimento do ponteiro a partir do pivo (menor que R para nao cobrir o
// arco colorido) e largura da base (o "grosso" do estilo termometro).
const COMPRIMENTO_PONTEIRO = R - 30;
const LARGURA_BASE_PONTEIRO = 7;
const PONTEIRO_D = `M ${CX - LARGURA_BASE_PONTEIRO} ${CY} L ${CX} ${CY - COMPRIMENTO_PONTEIRO} L ${CX + LARGURA_BASE_PONTEIRO} ${CY} Z`;

// Elemento de assinatura do painel. O gauge semicircular substitui a barra
// linear anterior porque a progressao de cor de uma torra real nao e uma
// regua reta -- e um arco com 4 faixas distintas, com um ponteiro fisico
// indicando o ponto atual, no mesmo espirito de um termometro de torrador
// analogico (Hottop/Rancilio), nao de um dashboard de SaaS generico.
export const MedidorTorra = ({ score, stage }) => {
  const posicao = calcularPosicaoPercentual(score);

  // Deriva a rotacao do ponteiro direto da posicao percentual (0-100%): o
  // SVG desenha o ponteiro apontando "para cima" (norte) por padrao, que
  // corresponde a posicao=50% (fronteira Clara/Media). Girar +-90 graus a
  // partir dai cobre toda a varredura de 180 graus do arco.
  const rotacaoPonteiro = posicao * 1.8 - 90;

  return (
    <div
      className="entrada-card card-torra bg-[var(--cor-superficie)] rounded-3xl p-7 border border-black/20 flex flex-col items-center gap-1"
      style={{ animationDelay: '90ms' }}
    >
      <span className="self-start text-[var(--cor-texto-secundario)] text-sm font-semibold uppercase tracking-wider mb-2">
        Ponto da Torra
      </span>

      <svg viewBox={`0 0 ${CX * 2} 150`} className="w-full max-w-[280px]" role="img" aria-label={`Medidor de torra: ${stage}, Agtron ${score.toFixed(1)}`}>
        {/* Trilho de fundo: um arco fino e apagado atras das 4 faixas, dando
            sensacao de bezel de instrumento em vez de formas soltas no ar. */}
        <path
          d={trajetoArco(CX, CY, R, 180, 0)}
          fill="none"
          stroke="var(--cor-superficie-clara)"
          strokeWidth={ESPESSURA_ARCO + 6}
          strokeLinecap="round"
        />

        {FAIXAS_GAUGE.map((faixa) => (
          <path
            key={faixa.id}
            d={trajetoArco(CX, CY, R, faixa.anguloInicial, faixa.anguloFinal)}
            fill="none"
            stroke={faixa.cor}
            strokeWidth={ESPESSURA_ARCO}
          />
        ))}

        {/* Ponteiro: cunha solida (nao uma linha fina) para ler como um
            instrumento fisico. Gira em torno do pivo (CX, CY) via CSS
            transform -- barato para o Pi 3, com transicao suave definida na
            classe .ponteiro-medidor (App.css), respeitando reduced-motion. */}
        <path
          className="ponteiro-medidor"
          d={PONTEIRO_D}
          fill="var(--cor-texto)"
          style={{ transform: `rotate(${rotacaoPonteiro}deg)`, transformOrigin: `${CX}px ${CY}px` }}
        />
        <circle cx={CX} cy={CY} r={11} fill="var(--cor-texto)" stroke="var(--cor-superficie)" strokeWidth={4} />
      </svg>

      {/* Numero Agtron em destaque, centralizado sob o gauge -- o
          protagonista visual do card, num instrumento real a leitura
          numerica e o que importa, apoiada pelo nome da fase logo abaixo. */}
      <div className="flex flex-col items-center -mt-2 gap-1 text-center">
        <AgtronBadge score={score} tamanho="grande" />
        <h2 className="font-heading text-xl font-semibold text-[var(--cor-texto-secundario)] leading-tight">
          {stage}
        </h2>
      </div>

      <div className="w-full max-w-[280px] flex justify-between mt-3 text-[10px] font-semibold text-[var(--cor-texto-secundario)] uppercase tracking-wide">
        <span>Cru</span>
        <span>Clara</span>
        <span>Média</span>
        <span>Escura</span>
      </div>
    </div>
  );
};
