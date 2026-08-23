import { useState, useEffect, useRef } from 'react';
import { CameraFeed } from './components/molecules/CameraFeed';
import { CurvaTorra } from './components/molecules/CurvaTorra';
import { MedidorTorra } from './components/molecules/MedidorTorra';
import { EventosTorra } from './components/molecules/EventosTorra';
import { formatarTempo } from './utils/tempo';
import './App.css';

// Marcadores de evento da torra, no mesmo padrao usado por torrefadores
// profissionais (e pelo software Artisan) -- CHARGE (inicio), DRY END (fim da
// secagem), FC START/END (1o crack) e SC START (2o crack), ate o DROP (fim da
// torra). Fixa aqui e passada tanto para EventosTorra (botoes de marcacao)
// quanto para CurvaTorra (linhas de referencia no grafico).
const EVENTOS_TORRA = [
  { id: 'charge', rotulo: 'Charge' },
  { id: 'dry_end', rotulo: 'Dry End' },
  { id: 'fc_start', rotulo: 'FC Start' },
  { id: 'fc_end', rotulo: 'FC End' },
  { id: 'sc_start', rotulo: 'SC Start' },
  { id: 'drop', rotulo: 'Drop' },
];

function App() {
  const [dadosTorra, setDadosTorra] = useState({
    score: 0,
    stage: "Aguardando...",
    uniformidade: 0
  });
  const [isOnline, setIsOnline] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [servidorOffline, setServidorOffline] = useState(false);

  const [modoContinuo, setModoContinuo] = useState(false);

  // Historico da torra atual, usado pelo grafico CurvaTorra. Cada entrada guarda
  // 'timestamp' como segundos decorridos desde o inicio da analise continua (nao
  // epoch time), ja no formato que o eixo X do grafico espera.
  const [historicoTorra, setHistoricoTorra] = useState([]);
  const [tempoDecorridoSeg, setTempoDecorridoSeg] = useState(0);
  // Eventos da torra ja marcados: { [id]: { timestamp, score, stage, origem } },
  // onde origem e 'manual' (clique do usuario) ou 'auto' (detectado a partir da
  // transicao de fase, ver capturarEAnalisar). Ausencia da chave = evento ainda
  // nao registrado nesta torra (ver EventosTorra.jsx).
  const [eventosRegistrados, setEventosRegistrados] = useState({});
  // Guarda o instante (Date.now()) em que a analise continua atual comecou. Fica em
  // ref (nao state) porque precisa de leitura sincrona imediatamente apos ser
  // definido, no mesmo clique que dispara a primeira captura -- um state so
  // atualizaria no proximo render, chegando tarde de mais para aquela chamada.
  const tempoInicioRef = useRef(null);
  // Ultima fase valida (Cru/Clara/Media/Escura) vista nesta sessao de analise
  // continua, usada so para detectar as transicoes de auto-marcacao de evento
  // (ver capturarEAnalisar). Fica em ref pelo mesmo motivo de tempoInicioRef:
  // o setInterval de captura roda dentro de um closure fixado quando
  // modoContinuo vira true (efeito com dependencia [modoContinuo]), entao
  // precisa de leitura/escrita sincrona que nao dependa de um novo render.
  // null = ainda sem leitura valida nesta sessao (nao dispara nenhuma transicao).
  const stageAnteriorRef = useRef(null);

  useEffect(() => {
    const verificarConexao = async () => {
      try {
        const resposta = await fetch('http://127.0.0.1:8000/status');
        if (resposta.ok) {
          setIsOnline(true);
          setServidorOffline(false);
        } else {
          setIsOnline(false);
        }
      } catch (erro) {
        setIsOnline(false);
      }
    };

    verificarConexao();
    const intervalo = setInterval(verificarConexao, 3000);
    return () => clearInterval(intervalo);
  }, []);

  useEffect(() => {
    let intervalo;
    if (modoContinuo) {
      intervalo = setInterval(() => {
        capturarEAnalisar(true);
      }, 2000);
    }
    return () => clearInterval(intervalo);
  }, [modoContinuo]);

  // Cronometro da torra (mm:ss): atualiza a cada segundo enquanto a analise
  // continua estiver ativa. Ao parar, o intervalo e limpo e o valor fica
  // congelado mostrando o tempo total daquela torra.
  useEffect(() => {
    let cronometro;
    if (modoContinuo) {
      cronometro = setInterval(() => {
        if (tempoInicioRef.current) {
          setTempoDecorridoSeg(Math.floor((Date.now() - tempoInicioRef.current) / 1000));
        }
      }, 1000);
    }
    return () => clearInterval(cronometro);
  }, [modoContinuo]);


  const capturarEAnalisar = async (isAuto = false) => {
    if (!isAuto) setIsProcessing(true);

    try {
      const resposta = await fetch('http://127.0.0.1:8000/analisar');
      const dados = await resposta.json();
      setServidorOffline(false);


      if (dados.score === 0) {
        setDadosTorra({ score: 0, stage: "Sem grãos", uniformidade: 0 });
        if (!isAuto) setIsProcessing(false);
        return;
      }
      const tolerancia_agtron = 4.0;

      setDadosTorra(estadoAtual => {
        if (Math.abs(dados.score - estadoAtual.score) > tolerancia_agtron || estadoAtual.score === 0) {
          return {
            score: dados.score,
            stage: dados.stage,
            uniformidade: dados.uniformidade
          };
        }
        return estadoAtual;
      });

      // Acumula no historico da torra (para o grafico) sempre que houver uma
      // leitura valida dentro de uma analise continua em andamento.
      if (dados.score > 0 && tempoInicioRef.current) {
        const segundosDecorridos = Math.round((Date.now() - tempoInicioRef.current) / 1000);
        setHistoricoTorra(historico => [
          ...historico,
          {
            timestamp: segundosDecorridos,
            score: dados.score,
            stage: dados.stage,
            uniformidade: dados.uniformidade,
          }
        ]);

        // Auto-marcacao de evento a partir da transicao de fase: so dispara na
        // PRIMEIRA leitura em que a fase avanca de uma categoria pra proxima
        // (Cru -> Clara -> Media -> Escura). Comparar sempre contra a fase da
        // leitura anterior (nao contra "ja passou por Cru alguma vez") garante
        // um disparo unico mesmo que o classificador oscile entre categorias
        // depois -- ex.: Clara -> Media -> Clara -> Media so marca FC START na
        // primeira vez, porque a segunda vez a fase anterior ja e "Media", nao
        // "Clara". registrarEvento() tem ainda uma segunda trava (nao
        // sobrescreve evento ja existente), entao mesmo uma oscilacao Cru ->
        // Clara -> Cru -> Clara nao re-dispara o DRY END.
        const faseAnterior = stageAnteriorRef.current;
        if (faseAnterior === 'Cru' && dados.stage === 'Clara') {
          registrarEvento('dry_end', { timestamp: segundosDecorridos, score: dados.score, stage: dados.stage, origem: 'auto' });
        } else if (faseAnterior === 'Clara' && dados.stage === 'Media') {
          registrarEvento('fc_start', { timestamp: segundosDecorridos, score: dados.score, stage: dados.stage, origem: 'auto' });
        } else if (faseAnterior === 'Media' && dados.stage === 'Escura') {
          registrarEvento('sc_start', { timestamp: segundosDecorridos, score: dados.score, stage: dados.stage, origem: 'auto' });
        }
        stageAnteriorRef.current = dados.stage;
      }

    } catch (erro) {
      console.error("Erro ao contactar a IA:", erro);
      setServidorOffline(true);
    }

    if (!isAuto) setIsProcessing(false);
  };

  const handleCalibrarSensor = async () => {
    try {
      await fetch("http://127.0.0.1:8000/calibrar");
      console.log("Hardware resetado!");
    } catch (error) {
      console.error("Erro ao resetar hardware:", error);
    }
  };

  const alternarAnaliseContinua = () => {
    const iniciando = !modoContinuo;
    setModoContinuo(iniciando);

    if (iniciando) {
      // Decisao: ao iniciar uma nova torra do zero, o historico e o cronometro
      // sao resetados automaticamente, em vez de depender de um botao manual
      // "Limpar historico". Isso evita um passo extra (e um possivel esquecimento)
      // durante a demonstracao ao vivo -- cada "Iniciar Análise em Tempo Real"
      // sempre comeca com um grafico limpo, representando a nova torra.
      setHistoricoTorra([]);
      setTempoDecorridoSeg(0);
      stageAnteriorRef.current = null;
      tempoInicioRef.current = Date.now();
      // CHARGE e o unico evento auto-marcado que nao depende de uma leitura da
      // API: ele representa o inicio da propria sessao, entao e registrado
      // aqui, no clique de "Iniciar Análise em Tempo Real", com timestamp 0.
      setEventosRegistrados({
        charge: { timestamp: 0, score: dadosTorra.score, stage: dadosTorra.stage, origem: 'auto' },
      });
      capturarEAnalisar();
    }
  };

  // Registra um evento (manual ou automatico) com os dados informados. Trava
  // central de idempotencia: se o evento ja existe -- veio de um clique manual
  // anterior OU de uma auto-marcacao -- o registro e ignorado e o estado
  // anterior e preservado. Decisao (item 6 da tarefa): nao ha popup de
  // "sobrescrever?"; o clique simplesmente nao tem efeito, porque o botao
  // correspondente ja fica desabilitado assim que o evento e marcado (ver
  // EventosTorra.jsx) -- chegar aqui com o evento ja marcado so aconteceria
  // por uma condicao de corrida (ex.: auto-marcacao no mesmo instante do
  // clique), e nesse caso a marcacao que chegou primeiro deve prevalecer.
  const registrarEvento = (idEvento, dadosRegistro) => {
    setEventosRegistrados(atual => {
      if (atual[idEvento]) return atual;
      return { ...atual, [idEvento]: dadosRegistro };
    });
  };

  // Clique manual num botao de evento: usa o tempo decorrido e o Agtron/fase
  // atuais, marcados com origem 'manual' (ver selo "(auto)" em EventosTorra.jsx).
  const handleRegistrarEvento = (idEvento) => {
    registrarEvento(idEvento, {
      timestamp: tempoDecorridoSeg,
      score: dadosTorra.score,
      stage: dadosTorra.stage,
      origem: 'manual',
    });
  };

  // Limpa o historico do grafico e os eventos marcados (manuais e
  // automaticos) para comecar uma nova torra do zero, sem precisar parar e
  // reiniciar a analise continua. Tambem zera a deteccao de transicao de fase
  // -- senao a proxima leitura comparada contra a ultima fase da torra
  // anterior poderia disparar um evento auto na hora errada (ex.: a torra
  // anterior tinha terminado em "Escura" e a nova comecaria com o grao ainda
  // "Cru", o que nao e uma transicao Media -> Escura de verdade).
  const handleReiniciarTorra = () => {
    setHistoricoTorra([]);
    setEventosRegistrados({});
    setTempoDecorridoSeg(0);
    stageAnteriorRef.current = null;
    if (modoContinuo) {
      tempoInicioRef.current = Date.now();
    }
  };

  return (
    <div className="textura-fundo min-h-screen bg-[var(--cor-fundo)] text-[var(--cor-texto)] font-sans selection:bg-[var(--cor-torrada-20)]">

      {servidorOffline && (
        <div className="bg-[var(--cor-alerta)] text-[var(--cor-texto)] text-sm font-semibold text-center py-2 px-4 shadow-lg">
          ⚠ Servidor Python offline — verifique se o api_teste.py está rodando
        </div>
      )}

      <nav className="bg-[var(--cor-superficie)] border-b border-black/20 px-8 py-4 flex items-center justify-between shadow-sm">
        <div className="flex items-center gap-3">
          <div className="bg-[var(--cor-torrada-10)] p-2 rounded-xl border border-[var(--cor-torrada-20)]">
            {/* Simbolo de marca: grao de cafe (oval + fenda central), no lugar
                do raio generico anterior -- mesmo tamanho, posicao e cor de acento. */}
            <svg className="w-6 h-6 text-[var(--cor-cru)]" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round" viewBox="0 0 24 24">
              <g transform="rotate(-20 12 12)">
                <ellipse cx="12" cy="12" rx="7" ry="9" />
                <path d="M12 3.8c-2 3.2-2 5 0 8.2s2 5 0 8.2" />
              </g>
            </svg>
          </div>
          <div>
            <h1 className="font-heading text-xl font-bold text-[var(--cor-texto)] tracking-wide">
              Torrefação<span className="text-[var(--cor-cru)]">IA</span>
            </h1>
            <p className="text-xs text-[var(--cor-texto-secundario)] font-medium">Painel de Controlo Automático</p>
          </div>
        </div>

       <div className={`flex items-center gap-2 px-4 py-2 rounded-full border cursor-default transition-all duration-300`}
         style={{
           backgroundColor: isOnline ? 'var(--cor-sucesso-10)' : 'var(--cor-alerta-10)',
           borderColor: isOnline ? 'var(--cor-sucesso-20)' : 'var(--cor-alerta-20)',
         }}
       >
          <div className={`w-2 h-2 rounded-full transition-colors duration-300 ${isOnline ? 'animate-pulse' : ''}`}
            style={{ backgroundColor: isOnline ? 'var(--cor-sucesso)' : 'var(--cor-alerta)' }}
          ></div>
          <span className="text-sm font-semibold transition-colors duration-300"
            style={{ color: isOnline ? 'var(--cor-sucesso)' : 'var(--cor-alerta)' }}
          >
            {isOnline ? 'Motor IA Online' : 'Motor IA Offline'}
          </span>
        </div>
      </nav>

      <main className="pt-10 px-8 md:px-12 pb-28 md:pb-24 max-w-screen-2xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-10 items-stretch">

        <div className="lg:col-span-8 flex flex-col gap-6">
          <h2 className="text-lg font-semibold text-[var(--cor-texto)] px-1">Inspeção Visual (Grãos)</h2>
          <CameraFeed />
        </div>

        <div className="lg:col-span-4 flex flex-col gap-6">
          <h2 className="text-lg font-semibold text-[var(--cor-texto)] px-1">Telemetria</h2>

          {/* 1) Medidor de Torra — elemento principal: fase da torra em destaque */}
          <MedidorTorra score={dadosTorra.score} stage={dadosTorra.stage} />

          {/* 2) Curva da torra ao longo do tempo — card com mais destaque agora
              que os Comandos sairam da coluna (ver CurvaTorra.jsx) */}
          <CurvaTorra
            dados={historicoTorra}
            tempoFormatado={formatarTempo(tempoDecorridoSeg)}
            eventos={EVENTOS_TORRA}
            eventosRegistrados={eventosRegistrados}
          />

          {/* 3) Eventos da torra — marcacao manual dos pontos-chave (CHARGE,
              DRY END, cracks, DROP), trazendo o conceito do Artisan para
              dentro do proprio painel (ver EventosTorra.jsx) */}
          <EventosTorra
            eventos={EVENTOS_TORRA}
            eventosRegistrados={eventosRegistrados}
            podeRegistrar={modoContinuo}
            onRegistrarEvento={handleRegistrarEvento}
            onReiniciarTorra={handleReiniciarTorra}
          />

          {/* 4) Uniformidade do lote */}
          <div
            className="entrada-card card-torra bg-[var(--cor-superficie)] rounded-3xl p-6 border border-black/20 flex items-center justify-between"
            style={{ animationDelay: '270ms' }}
          >
            <div>
              <p className="text-[var(--cor-texto-secundario)] text-sm font-medium mb-1">Uniformidade do Lote</p>
              <div className="flex items-end gap-1">
                <p className="font-heading text-3xl font-bold text-[var(--cor-texto)]">{dadosTorra.uniformidade}</p>
                <span className="text-lg text-[var(--cor-texto-secundario)] font-medium mb-1">%</span>
              </div>
            </div>
            <div className="bg-[var(--cor-torrada-10)] p-3 rounded-2xl border border-[var(--cor-torrada-20)]">
              <svg className="w-8 h-8 text-[var(--cor-cru)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
          </div>

        </div>
      </main>

      {/* Barra de Comandos fixa no rodape: numa demonstracao ao vivo, os botoes
          de acao principal (Iniciar/Parar, Calibrar) precisam estar sempre
          visiveis, mesmo com a coluna de Telemetria crescendo com mais cards
          — por isso saiu do fluxo normal da coluna e virou uma barra propria. */}
      <footer className="fixed bottom-0 inset-x-0 z-20 bg-[var(--cor-superficie)] border-t border-black/20 shadow-[0_-12px_30px_-8px_rgba(0,0,0,0.45)]">
        <div className="max-w-screen-2xl mx-auto px-8 md:px-12 py-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <h3 className="hidden sm:block text-[var(--cor-texto-secundario)] text-xs font-semibold uppercase tracking-wider shrink-0">
            Comandos
          </h3>

          <div className="flex flex-col sm:flex-row gap-3 w-full sm:w-auto">
            <button
              onClick={alternarAnaliseContinua}
              disabled={isProcessing && !modoContinuo}
              className={`sm:w-80 flex justify-center py-3.5 px-4 rounded-2xl font-bold transition-all shadow-lg active:scale-95 ${
                modoContinuo
                  ? 'text-[var(--cor-texto)] animate-pulse'
                  : isProcessing
                    ? 'text-[var(--cor-texto-secundario)] cursor-not-allowed'
                    : 'text-[var(--cor-fundo)]'
              }`}
              style={{
                backgroundColor: modoContinuo
                  ? 'var(--cor-alerta)'
                  : isProcessing
                    ? 'var(--cor-superficie-clara)'
                    : 'var(--cor-torrada)',
              }}
            >
              {modoContinuo
                ? '⏹ Parar Análise Contínua'
                : isProcessing
                  ? 'A Processar...'
                  : '▶️ Iniciar Análise em Tempo Real'}
            </button>

            <button
              onClick={handleCalibrarSensor}
              className="sm:w-56 flex justify-center py-3.5 px-4 rounded-2xl text-[var(--cor-texto-secundario)] bg-transparent border border-[var(--cor-superficie-clara)] hover:bg-[var(--cor-superficie-clara)] hover:text-[var(--cor-texto)] font-semibold transition-all active:scale-95"
            >
              Calibrar Sensor
            </button>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
