import React from 'react';

// Atom: apenas o numero Agtron cru, sem card proprio. E usado como apoio
// dentro do MedidorTorra — o nome da fase (ex: "Torra Média") e quem carrega
// o destaque visual principal, por ser o que o produtor reconhece de imediato.
export const AgtronBadge = ({ score }) => {
  return (
    <span className="font-heading text-2xl font-semibold text-[var(--cor-texto)]">
      {score.toFixed(1)}
      <span className="ml-1.5 text-xs font-sans font-medium text-[var(--cor-texto-secundario)] uppercase tracking-wider">
        Agtron
      </span>
    </span>
  );
};
