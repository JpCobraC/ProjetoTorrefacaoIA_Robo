import React from 'react';
import { formatarTempo } from '../../utils/tempo';

// Barra de marcacao de eventos da torra: traz o conceito de "marcadores de
// evento" do software Artisan (CHARGE, DRY END, crackers, DROP) para dentro
// do proprio painel, sem depender de nenhuma integracao externa. A lista de
// eventos (EVENTOS_TORRA) e definida em App.jsx e passada via prop, junto
// com o registro atual (eventosRegistrados) e os handlers de clique.
//
// eventos: array fixo de { id, rotulo }.
// eventosRegistrados: objeto { [id]: { timestamp, score, stage, origem } } com
// os eventos ja marcados nesta torra -- ausencia da chave = ainda nao marcado.
// 'origem' e 'manual' (clique do usuario) ou 'auto' (detectado por App.jsx a
// partir da transicao de fase retornada pela IA); so muda o selo "(auto)"
// exibido junto ao horario, a logica de marcacao/bloqueio e a mesma para os dois.
// podeRegistrar: true enquanto a analise continua estiver ativa; controla se
// os botoes ainda-nao-marcados ficam clicaveis.
// onRegistrarEvento(id) / onReiniciarTorra(): handlers definidos em App.jsx.
export const EventosTorra = ({ eventos, eventosRegistrados, podeRegistrar, onRegistrarEvento, onReiniciarTorra }) => {
  return (
    <div
      className="entrada-card card-torra bg-[var(--cor-superficie)] rounded-3xl p-6 border border-black/20"
      style={{ animationDelay: '210ms' }}
    >
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-[var(--cor-texto-secundario)] text-sm font-semibold uppercase tracking-wider">
          Eventos da Torra
        </h3>
        <button
          onClick={onReiniciarTorra}
          className="text-[var(--cor-texto-secundario)] text-xs font-mono bg-[var(--cor-superficie-clara)] hover:bg-[var(--cor-alerta-10)] hover:text-[var(--cor-alerta)] px-2.5 py-1 rounded-full border border-black/20 transition-colors active:scale-95"
        >
          ↺ Reiniciar Torra
        </button>
      </div>

      <div className="flex flex-wrap gap-2">
        {eventos.map((evento) => {
          const registro = eventosRegistrados[evento.id];
          const marcado = !!registro;

          const auto = marcado && registro.origem === 'auto';

          return (
            <button
              key={evento.id}
              onClick={() => onRegistrarEvento(evento.id)}
              disabled={marcado || !podeRegistrar}
              title={auto ? 'Marcado automaticamente pela IA a partir da transicao de fase' : undefined}
              className={`flex-1 min-w-[6.5rem] flex flex-col items-center justify-center gap-0.5 py-2.5 px-2 rounded-2xl text-[11px] font-bold uppercase tracking-wide border transition-all active:scale-95 ${
                marcado
                  ? 'text-[var(--cor-fundo)] border-transparent cursor-default'
                  : podeRegistrar
                    ? 'text-[var(--cor-texto-secundario)] border-[var(--cor-superficie-clara)] hover:bg-[var(--cor-superficie-clara)] hover:text-[var(--cor-texto)] cursor-pointer'
                    : 'text-[var(--cor-texto-secundario)] border-[var(--cor-superficie-clara)] opacity-40 cursor-not-allowed'
              }`}
              style={marcado ? { backgroundColor: 'var(--cor-cru)' } : undefined}
            >
              <span>{marcado ? `✓ ${evento.rotulo}` : evento.rotulo}</span>
              {marcado && (
                <span className="font-mono font-medium normal-case flex items-center gap-1">
                  {formatarTempo(registro.timestamp)}
                  {/* Selo discreto para diferenciar marcacao automatica (deteccao de
                      transicao de fase) da marcacao manual (clique do usuario) --
                      importante numa demonstracao, para deixar claro o que a IA
                      identificou sozinha. */}
                  {auto && <span className="opacity-75 font-sans">(auto)</span>}
                </span>
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
};
