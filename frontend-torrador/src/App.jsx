import { useState, useEffect } from 'react';
import { AgtronBadge } from './components/atoms/AgtronBadge';
import { CameraFeed } from './components/molecules/CameraFeed';

function App() {
  const [dadosTorra, setDadosTorra] = useState({
    score: 0,
    stage: "Aguardando...",
    uniformidade: 0
  });
  const [isOnline, setIsOnline] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  
  const [modoContinuo, setModoContinuo] = useState(false);

  useEffect(() => {
    const verificarConexao = async () => {
      try {
        const resposta = await fetch('http://127.0.0.1:8000/status');
        if (resposta.ok) {
          setIsOnline(true);
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


  const capturarEAnalisar = async (isAuto = false) => {
    if (!isAuto) setIsProcessing(true); 
    
    try {
      const resposta = await fetch('http://127.0.0.1:8000/analisar');
      const dados = await resposta.json();
      
    
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

    } catch (erro) {
      console.error("Erro ao contactar a IA:", erro);
      if (!modoContinuo) {
        alert("Não foi possível contactar o servidor Python. Ele está a rodar?");
      }
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

  return (
    <div className="min-h-screen bg-[#1c1917] text-stone-100 font-sans selection:bg-amber-500/30">
      
      <nav className="bg-[#292524] border-b border-stone-800 px-8 py-4 flex items-center justify-between shadow-sm">
        <div className="flex items-center gap-3">
          <div className="bg-amber-500/10 p-2 rounded-xl border border-amber-500/20">
            <svg className="w-6 h-6 text-amber-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>
          <div>
            <h1 className="text-xl font-bold text-white tracking-wide">Torrefação<span className="text-amber-500">IA</span></h1>
            <p className="text-xs text-stone-400 font-medium">Painel de Controlo Automático</p>
          </div>
        </div>
        
       <div className={`flex items-center gap-2 px-4 py-2 rounded-full border cursor-default transition-all duration-300 ${
          isOnline 
            ? 'bg-emerald-500/10 border-emerald-500/20' 
            : 'bg-red-500/10 border-red-500/20'
        }`}>
          <div className={`w-2 h-2 rounded-full transition-colors duration-300 ${
            isOnline 
              ? 'bg-emerald-500 animate-pulse shadow-[0_0_8px_rgba(16,185,129,0.8)]' 
              : 'bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.8)]'
          }`}></div>
          <span className={`text-sm font-semibold transition-colors duration-300 ${
            isOnline ? 'text-emerald-400' : 'text-red-400'
          }`}>
            {isOnline ? 'Motor IA Online' : 'Motor IA Offline'}
          </span>
        </div>
      </nav>

      <main className="p-8 max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        <div className="lg:col-span-8 flex flex-col gap-6">
          <h2 className="text-lg font-semibold text-stone-200 px-1">Inspeção Visual (Grãos)</h2>
          <CameraFeed />
        </div>

        <div className="lg:col-span-4 flex flex-col gap-6">
          <h2 className="text-lg font-semibold text-stone-200 px-1">Telemetria</h2>
          
          <AgtronBadge score={dadosTorra.score} stage={dadosTorra.stage} />

          <div className="bg-[#292524] rounded-3xl p-6 border border-stone-800 shadow-xl flex items-center justify-between">
            <div>
              <p className="text-stone-400 text-sm font-medium mb-1">Uniformidade do Lote</p>
              <div className="flex items-end gap-1">
                <p className="text-3xl font-bold text-stone-100">{dadosTorra.uniformidade}</p>
                <span className="text-lg text-stone-500 font-medium mb-1">%</span>
              </div>
            </div>
            <div className="bg-amber-500/10 p-3 rounded-2xl border border-amber-500/20">
              <svg className="w-8 h-8 text-amber-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
          </div>

          <div className="bg-[#292524] rounded-3xl p-6 border border-stone-800 shadow-xl mt-2">
            <h3 className="text-stone-400 text-sm font-semibold mb-4 uppercase tracking-wider">Comandos</h3>
            <div className="flex flex-col gap-3">
              
            
              <button 
                onClick={() => {
                  setModoContinuo(!modoContinuo);
                  if (!modoContinuo) capturarEAnalisar(); 
                }}
                disabled={isProcessing && !modoContinuo}
                className={`w-full flex justify-center py-3.5 px-4 rounded-2xl font-bold transition-all shadow-lg active:scale-95 ${
                  modoContinuo 
                    ? 'bg-red-500 text-white hover:bg-red-600 animate-pulse' 
                    : isProcessing 
                      ? 'bg-amber-500/50 text-stone-900 cursor-not-allowed' 
                      : 'bg-amber-500 text-stone-900 hover:bg-amber-400'
                }`}
              >
                {modoContinuo 
                  ? '⏹ Parar Análise Contínua' 
                  : isProcessing 
                    ? 'A Processar...' 
                    : '▶️ Iniciar Análise em Tempo Real'}
              </button>

              <button 
                onClick={handleCalibrarSensor}
                className="w-full flex justify-center py-3.5 px-4 rounded-2xl text-stone-300 bg-transparent border border-stone-600 hover:bg-stone-800 hover:text-white font-semibold transition-all active:scale-95"
              >
                Calibrar Sensor
              </button>

            </div>
          </div>

        </div>
      </main>
    </div>
  );
}

export default App;