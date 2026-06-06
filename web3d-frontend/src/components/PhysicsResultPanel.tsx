import { useStore } from '../store/useStore'
import { ConfidenceGauge } from './ConfidenceGauge'
import { MonteCarloChart } from './MonteCarloChart'
import { TypewriterLog } from './TypewriterLog'
import { eventLabel, phaseLabel, ttlLabel } from '../utils/physicsLabels'

const DISPLAY_BITS = [6, 5, 4, 3, 2, 1]

const BIT_LABELS_SHORT: Record<number, string> = {
  6: 'B6-宏观',
  5: 'B5-规则',
  4: 'B4-接口',
  3: 'B3-核心',
  2: 'B2-传导',
  1: 'B1-物理',
}

interface PhysicsResultPanelProps {
  cardClassName?: string
}

export function PhysicsResultPanel({
  cardClassName = 'glass-panel p-4',
}: PhysicsResultPanelProps) {
  const nodeInfo = useStore((s) => s.nodeInfo)
  const deterministic = useStore((s) => s.deterministic)
  const physicsSnapshot = useStore((s) => s.physicsSnapshot)
  const typewriterLogs = useStore((s) => s.typewriterLogs)

  const confM1 = physicsSnapshot?.confidence.conf_input ?? nodeInfo?.conf_m1 ?? deterministic?.current_node?.entropy_S ?? 0.5
  const focusLayer = physicsSnapshot?.layers.find(layer => layer.bit === physicsSnapshot.focus_bit)
  const stateDescription = deterministic?.current_node?.physics_description

  return (
    <>
      <div className={cardClassName}>
        <ConfidenceGauge value={confM1} size={140} />
      </div>

      <div className={cardClassName}>
        <MonteCarloChart confM1={confM1} outcomes={physicsSnapshot?.monte_carlo ?? []} />
      </div>

      <div className={cardClassName}>
        <div className="panel-title mb-3">
          原始状态 -&gt; 路由后继
        </div>
        {physicsSnapshot ? (
          <div className="flex flex-col gap-2">
            <div className="flex items-center justify-between rounded-md border border-[#524639]/10 bg-white/50 px-3 py-2 font-mono text-[11px] text-[#26323f]">
              <span>{physicsSnapshot.bits}</span>
              <span className="text-[#8a8177]">-&gt;</span>
              <span>{physicsSnapshot.selected_next_bits ?? '多后继'}</span>
            </div>
            <div className="grid grid-cols-2 gap-x-4 gap-y-1 font-mono text-[8px]">
              <span className="text-[#8a8177]">焦点</span>
              <span className="text-[#9f1239]">B{physicsSnapshot.focus_bit}</span>
              <span className="text-[#8a8177]">相位</span>
              <span className="text-[#26323f]">{phaseLabel(focusLayer?.phase)}</span>
              <span className="text-[#8a8177]">事件</span>
              <span className="text-[#26323f]">{eventLabel(physicsSnapshot.event)}</span>
              <span className="text-[#8a8177]">ttl</span>
              <span className="text-[#26323f]">{ttlLabel(physicsSnapshot.ttl)}</span>
              <span className="text-[#8a8177]">路径</span>
              <span className="text-[#26323f]">{physicsSnapshot.route.path_number} / {physicsSnapshot.route.path_name}</span>
              <span className="text-[#8a8177]">硬中断后继</span>
              <span className="text-[#26323f]">{physicsSnapshot.interrupt.next_bits}</span>
              <span className="text-[#8a8177]">路由后继</span>
              <span className="text-[#26323f]">{physicsSnapshot.route.next_bits ?? physicsSnapshot.selected_next_bits ?? '多后继'}</span>
            </div>
            {physicsSnapshot.route.alternatives.length > 0 && (
              <div className="flex flex-col gap-1 border-t border-[#524639]/10 pt-2">
                {physicsSnapshot.route.alternatives.map((item) => (
                  <div key={item.key} className="flex items-center justify-between font-mono text-[8px] text-[#4f5d6a]">
                    <span>{item.operation}</span>
                    <span>{item.bits}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        ) : (
          <div className="font-mono text-[9px] text-[#8a8177] italic">
            等待在“模拟”页执行物理计算...
          </div>
        )}
      </div>

      <div className={cardClassName}>
        <div className="panel-title mb-3">
          张量 T(e,p,t)
        </div>
        {physicsSnapshot ? (
          <div className="flex flex-col gap-1">
            {DISPLAY_BITS.map((bitIndex) => {
              const layer = physicsSnapshot.layers.find(item => item.bit === bitIndex)
              if (!layer) return null
              return (
                <div key={bitIndex} className="flex items-center gap-2 rounded bg-white/40 px-2 py-1 text-[8px]">
                  <span className="w-16 shrink-0 font-mono text-[7px] text-[#8a8177]">
                    {BIT_LABELS_SHORT[bitIndex]}
                  </span>
                  <div className="flex gap-3 flex-1">
                    <span className="font-mono text-[#6b6259]">
                      t=<span className="text-[#26323f]">{layer.tensor.t.toFixed(2)}</span>
                    </span>
                    <span className="font-mono text-[#6b6259]">
                      e=<span className="text-[#26323f]">{layer.tensor.e.toFixed(2)}</span>
                    </span>
                    <span className="font-mono text-[#6b6259]">
                      p=<span className={layer.tensor.p === 1 ? 'text-[#26323f]' : 'text-[#8a8177]'}>{layer.tensor.p}</span>
                    </span>
                  </div>
                </div>
              )
            })}
          </div>
        ) : (
          <div className="font-mono text-[9px] text-[#8a8177] italic">
            张量由 /api/physics 生成。
          </div>
        )}
      </div>

      <div className={cardClassName}>
        <div className="panel-title mb-3">
          RAG 日志
        </div>
        <TypewriterLog entries={typewriterLogs} />
        {typewriterLogs.length === 0 && (
          <div className="font-mono text-[9px] text-[#8a8177] italic">
            暂无事件...
          </div>
        )}
      </div>

      {(physicsSnapshot || stateDescription) && (
        <div className={cardClassName}>
          <div className="panel-title mb-3">
            状态
          </div>
          {physicsSnapshot && (
            <div className="mb-2 rounded-md border border-[#524639]/10 bg-white/50 px-3 py-2 font-mono text-[10px] text-[#26323f]">
              {physicsSnapshot.hexagram} / S={physicsSnapshot.entropy_S.toFixed(3)} / M={physicsSnapshot.mass_M.toFixed(3)}
            </div>
          )}
          {physicsSnapshot?.route.description && (
            <div className="mb-2 text-[11px] leading-relaxed text-[#6b6259]">
              {physicsSnapshot.route.description}
            </div>
          )}
          {stateDescription && (
            <div
              className="text-[11px] leading-relaxed text-[#4f5d6a]"
            >
              {stateDescription}
            </div>
          )}
        </div>
      )}
    </>
  )
}
