import React from 'react';

// Atom: apenas o numero Agtron cru, sem card proprio.
// tamanho 'padrao' (default): usado como apoio junto ao nome da fase.
// tamanho 'grande': protagonista do centro do gauge em MedidorTorra.jsx --
// o mesmo par numero+rotulo, so com peso tipografico bem maior.
export const AgtronBadge = ({ score, tamanho = 'padrao' }) => {
  const grande = tamanho === 'grande';

  return (
    <span
      className={
        grande
          ? 'font-heading text-5xl md:text-6xl font-semibold text-[var(--cor-texto)] leading-none'
          : 'font-heading text-2xl font-semibold text-[var(--cor-texto)]'
      }
    >
      {score.toFixed(1)}
      <span
        className={
          grande
            ? 'block mt-1 text-xs font-sans font-semibold text-[var(--cor-texto-secundario)] uppercase tracking-[0.2em]'
            : 'ml-1.5 text-xs font-sans font-medium text-[var(--cor-texto-secundario)] uppercase tracking-wider'
        }
      >
        Agtron
      </span>
    </span>
  );
};
