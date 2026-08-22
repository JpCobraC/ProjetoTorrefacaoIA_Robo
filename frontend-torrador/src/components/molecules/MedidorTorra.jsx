import React from 'react';
import { AgtronBadge } from '../atoms/AgtronBadge';

// Extremos da escala Agtron que a barra representa: 95 = grao cru (dourado),
// 35 = torra escura (marrom quase preto). Mesmos limiares usados pelo
// backend (validar_sistema.py) para classificar a fase.
const AGTRON_CRU = 95;
const AGTRON_ESCURA = 35;

// Converte o score Agtron atual numa posicao de 0 a 100% sobre a barra,
// do lado do cru (esquerda) para o lado da torra escura (direita).
const calcularPosicaoPercentual = (score) => {
  if (!score) return 0;
  const bruto = ((AGTRON_CRU - score) / (AGTRON_CRU - AGTRON_ESCURA)) * 100;
  return Math.min(100, Math.max(0, bruto));
};

// Elemento de assinatura do painel. Em vez de um numero solto gigante, o
// protagonista visual e o nome da fase da torra (facil de reconhecer por
// quem trabalha com cafe mas nao com tecnologia), apoiado por uma barra em
// degrade continuo do dourado do grao cru ate o marrom escuro da torra
// pronta, com um marcador indicando o ponto atual.
export const MedidorTorra = ({ score, stage }) => {
  const posicao = calcularPosicaoPercentual(score);

  return (
    <div
      className="entrada-card card-torra bg-[var(--cor-superficie)] rounded-3xl p-8 border border-black/20 flex flex-col items-center gap-7"
      style={{ animationDelay: '90ms' }}
    >

      <span className="text-[var(--cor-texto-secundario)] text-xs font-semibold uppercase tracking-[0.2em]">
        Ponto da Torra
      </span>

      <div className="flex flex-col items-center gap-2 text-center">
        <h2 className="font-heading text-4xl md:text-5xl font-bold text-[var(--cor-texto)] leading-tight">
          {stage}
        </h2>
        <AgtronBadge score={score} />
      </div>

      <div className="w-full">
        <div
          className="relative h-4 rounded-full"
          style={{ background: 'linear-gradient(90deg, var(--cor-cru), var(--cor-torrada), var(--cor-escura))' }}
        >
          <div
            className="absolute top-1/2 w-5 h-5 rounded-full bg-[var(--cor-texto)] border-4 border-[var(--cor-superficie)] shadow-md transition-[left] duration-[600ms] ease-out"
            style={{ left: `${posicao}%`, transform: 'translate(-50%, -50%)' }}
          />
        </div>
        <div className="flex justify-between mt-2.5 text-[10px] font-semibold text-[var(--cor-texto-secundario)] uppercase tracking-wide">
          <span>Cru</span>
          <span>Clara</span>
          <span>Média</span>
          <span>Escura</span>
        </div>
      </div>

    </div>
  );
};
