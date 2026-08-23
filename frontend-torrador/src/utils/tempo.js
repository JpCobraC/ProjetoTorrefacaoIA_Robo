// Converte um total de segundos em "mm:ss", usado pelo cronometro da torra
// e pelos rotulos de tempo dos eventos marcados (CurvaTorra, EventosTorra).
export const formatarTempo = (segundosTotais) => {
  const minutos = Math.floor(segundosTotais / 60).toString().padStart(2, '0');
  const segundos = Math.floor(segundosTotais % 60).toString().padStart(2, '0');
  return `${minutos}:${segundos}`;
};
