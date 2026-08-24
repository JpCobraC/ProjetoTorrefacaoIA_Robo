import React from 'react';
import { API_BASE_URL } from '../../utils/config';

// Feed de video ao vivo da camera apontada para o cafe. Sem estetica de
// vigilancia (sem ponto "REC" piscando, sem miras de canto de camera de
// seguranca) — so uma borda simples e um rotulo discreto, para nao
// intimidar quem nao e do meio tecnico.
export const CameraFeed = () => {
  return (
    <div className="entrada-card card-torra flex flex-col flex-1 bg-[var(--cor-superficie)] rounded-3xl border border-black/20 overflow-hidden w-full">

      {/* Sem aspect-video fixo: a area do video estica (flex-1) para preencher
          toda a altura disponivel na coluna, casando com a pilha de cards da
          Telemetria ao lado. min-h e so um piso de seguranca para telas onde
          a coluna de telemetria fica curta (ex: mobile empilhado). */}
      <div className="flex-1 min-h-[320px] bg-[#120D09] relative overflow-hidden">

        <img
          src={`${API_BASE_URL}/video_feed`}
          alt="Feed do Torrador"
          className="w-full h-full object-cover"
        />

        <span className="absolute bottom-4 left-4 bg-black/40 backdrop-blur-md px-3 py-1.5 rounded-full border border-white/10 text-[var(--cor-texto)] text-xs font-medium tracking-wide">
          Câmera ao vivo
        </span>

        <span className="absolute bottom-4 right-4 bg-black/40 backdrop-blur-md px-3 py-1.5 rounded-full border border-white/10 text-[var(--cor-texto-secundario)] text-xs font-mono">
          ML: CIELAB→Agtron
        </span>
      </div>
    </div>
  );
};
