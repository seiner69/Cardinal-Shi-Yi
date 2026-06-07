import { useStore } from '../store/useStore'
import { TopNav } from './TopNav'
import { AnalysisView } from './AnalysisView'
import { SimulationView } from './SimulationView'
import { EvolutionView } from './EvolutionView'
import { PracticalView } from './PracticalView'

export default function OverlayUI() {
  const interfaceMode = useStore((s) => s.interfaceMode)
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

      {interfaceMode === 'practical' && <PracticalView />}
      {interfaceMode === 'expert' && viewMode === 'analysis' && <AnalysisView />}
      {interfaceMode === 'expert' && viewMode === 'simulation' && <SimulationView />}
      {interfaceMode === 'expert' && viewMode === 'evolution' && <EvolutionView />}
    </div>
  )
}
