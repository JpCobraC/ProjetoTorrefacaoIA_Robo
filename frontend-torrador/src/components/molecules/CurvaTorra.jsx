import React from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from 'recharts';

// Ponto customizado da linha: por padrao nao desenha nada (o grafico fica
// limpo, so a linha), exceto no ultimo ponto do array -- ali marca a leitura
// mais recente com um nucleo solido + halo pulsante sutil (cor-torrada),
// reforcando a sensacao de instrumento medindo ao vivo. Definido fora do
// componente para nao ser recriado a cada render.
const PontoAoVivo = ({ cx, cy, ehUltimo }) => {
  if (cx == null || cy == null || !ehUltimo) return null;
  return (
    <g>
      <circle cx={cx} cy={cy} r={8} className="ponto-curva-glow" fill="var(--cor-torrada)" />
      <circle cx={cx} cy={cy} r={4} fill="var(--cor-cru)" stroke="var(--cor-superficie)" strokeWidth={2} />
    </g>
  );
};

// dados: array de { timestamp, score, stage, uniformidade }, onde 'timestamp' e o
// tempo decorrido em segundos desde o inicio da analise continua (nao epoch time),
// ja pronto para ser usado direto no eixo X. Cada nova leitura e acumulada em
// App.jsx via setHistoricoTorra(historico => [...historico, novoPonto]) -- o
// spread cria um novo array a cada leitura, mas preserva a MESMA referencia dos
// objetos de pontos ja existentes, o que e o que o recharts precisa para
// interpolar a transicao da linha em vez de redesenhar tudo do zero.
// tempoFormatado: string mm:ss do cronometro da torra atual, exibida junto ao titulo.
export const CurvaTorra = ({ dados, tempoFormatado }) => {
  return (
    <div
      className="entrada-card card-torra bg-[var(--cor-superficie)] rounded-3xl p-7 border border-black/20"
      style={{ animationDelay: '180ms' }}
    >
      <div className="flex items-center justify-between mb-5">
        <h3 className="text-[var(--cor-texto-secundario)] text-sm font-semibold uppercase tracking-wider">
          Curva da Torra
        </h3>
        {/* Leitura tecnica (cronometro) -> fonte monoespacada */}
        <span className="text-[var(--cor-texto-secundario)] text-xs font-mono bg-[var(--cor-superficie-clara)] px-2.5 py-1 rounded-full border border-black/20">
          {tempoFormatado}
        </span>
      </div>

      {/* Card mais rico em informacao visual da coluna: com os Comandos fora
          da coluna de Telemetria, ele herda mais espaco (altura do grafico
          maior, de 180 para 240px) para ganhar destaque frente aos outros. */}
      {dados.length < 2 ? (
        <div className="h-[240px] flex items-center justify-center text-[var(--cor-texto-secundario)] text-sm text-center px-6">
          Aguardando leituras para desenhar a curva da torra...
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={240}>
          <LineChart data={dados} margin={{ top: 5, right: 8, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--cor-superficie-clara)" />
            <XAxis
              dataKey="timestamp"
              type="number"
              domain={[0, 'dataMax']}
              allowDecimals={false}
              tickFormatter={(seg) => `${seg}s`}
              tick={{ fill: 'var(--cor-texto-secundario)', fontSize: 11, fontFamily: 'monospace' }}
              stroke="var(--cor-superficie-clara)"
            />
            <YAxis
              domain={[30, 100]}
              tick={{ fill: 'var(--cor-texto-secundario)', fontSize: 11, fontFamily: 'monospace' }}
              stroke="var(--cor-superficie-clara)"
            />
            <Tooltip
              contentStyle={{
                backgroundColor: 'var(--cor-fundo)',
                border: '1px solid var(--cor-superficie-clara)',
                borderRadius: '0.75rem',
              }}
              labelStyle={{ color: 'var(--cor-texto)' }}
              itemStyle={{ color: 'var(--cor-cru)' }}
              formatter={(valor) => [valor.toFixed(1), 'Agtron']}
              labelFormatter={(seg) => `t = ${seg}s`}
            />
            <Line
              type="monotone"
              dataKey="score"
              stroke="var(--cor-cru)"
              strokeWidth={2.5}
              dot={(props) => (
                <PontoAoVivo key={`ponto-${props.index}`} {...props} ehUltimo={props.index === dados.length - 1} />
              )}
              isAnimationActive={true}
              animationDuration={350}
              animationEasing="ease-out"
            />
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  );
};
