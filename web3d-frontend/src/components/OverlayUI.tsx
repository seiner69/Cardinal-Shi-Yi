import { useStore } from '../store/useStore'
import { TopNav } from './TopNav'
import { AnalysisView } from './AnalysisView'
import { SimulationView } from './SimulationView'
import { EvolutionView } from './EvolutionView'

export default function OverlayUI() {
  const viewMode = useStore((s) => s.viewMode)

  return (
    <div className="absolute inset-0 pointer-events-none">
      <div className="absolute top-4 left-4 pointer-events-none hidden sm:block">
        <div className="glass-panel px-4 py-3">
          <div className="text-[15px] font-bold text-[#26323f]">历史演化状态机</div>
          <div className="mt-1 font-mono text-[9px] tracking-[0.18em] text-[#6b6259]">
            6-BIT FSM TOPOLOGY ENGINE
          </div>
        </div>
      </div>

      <TopNav />

      {viewMode === 'analysis' && <AnalysisView />}
      {viewMode === 'simulation' && <SimulationView />}
      {viewMode === 'evolution' && <EvolutionView />}
    </div>
  )
}
