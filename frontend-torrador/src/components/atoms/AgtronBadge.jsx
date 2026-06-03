import React from 'react';

export const AgtronBadge = ({ score, stage }) => {
  return (
    <div className="bg-gradient-to-b from-[#292524] to-[#1c1917] rounded-3xl p-8 border border-stone-800 shadow-xl flex flex-col items-center justify-center relative overflow-hidden">
      {/* Brilho de fundo no topo (toque premium) */}
      <div className="absolute top-0 w-full h-1 bg-gradient-to-r from-transparent via-amber-500 to-transparent opacity-50"></div>

      <span className="text-stone-400 text-xs font-bold uppercase tracking-[0.2em] mb-4">
        Índice Agtron
      </span>

      <div className="flex items-baseline gap-1">
        <span className="text-7xl font-black text-transparent bg-clip-text bg-gradient-to-br from-amber-400 to-orange-600">
          {score.toFixed(1)}
        </span>
      </div>

      {/* Badge indicativo do ponto de torra */}
      <div className="mt-5 px-5 py-2 bg-stone-800/80 rounded-full border border-stone-700/50 flex items-center gap-2 shadow-inner">
        <div className="w-2.5 h-2.5 rounded-full bg-orange-500 shadow-[0_0_8px_rgba(249,115,22,0.8)]"></div>
        <span className="text-stone-300 text-sm font-medium">
          {stage}
        </span>
      </div>
    </div>
  );
};