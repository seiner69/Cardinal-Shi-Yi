import { useStore } from '../store/useStore'
import { ConfidenceGauge } from './ConfidenceGauge'
import { MonteCarloChart } from './MonteCarloChart'
import { TypewriterLog } from './TypewriterLog'

const BIT_LABELS_SHORT: Record<number, string> = {
  6: 'B6-MACRO',
  5: 'B5-RULES',
  4: 'B4-INFACE',
  3: 'B3-CORE',
  2: 'B2-CONDO',
  1: 'B1-PHYS',
}

export function RightConsole() {
  const nodeInfo = useStore(s => s.nodeInfo)
  const deterministic = useStore(s => s.deterministic)
  const typewriterLogs = useStore(s => s.typewriterLogs)

  const confM1 = nodeInfo?.conf_m1 ?? deterministic?.current_node?.entropy_S ?? 0.5

  return (
    <div
      className="absolute top-1/2 -translate-y-1/2 right-4 pointer-events-auto w-[340px] max-h-[88vh] overflow-y-auto"
    >
      {/* Header */}
      <div className="mb-3">
        <span className="font-mono text-[9px] text-gray-400 uppercase tracking-[0.3em]">
          SEMANTIC TERMINAL / 语义终端
        </span>
      </div>

      {/* Title bar */}
      <div className="flex items-center gap-3 mb-4">
        <div className="h-px flex-1 bg-gradient-to-r from-gray-300/30 to-transparent" />
        <span className="font-mono text-[10px] text-gray-600 uppercase tracking-[0.25em] whitespace-nowrap">
          RAG OS
        </span>
        <div className="h-px flex-1 bg-gradient-to-l from-gray-300/30 to-transparent" />
      </div>

      {/* Confidence Gauge */}
      <div className="mb-4 p-3 bg-white/20 border border-gray-200/30">
        <ConfidenceGauge value={confM1} size={140} />
      </div>

      {/* Monte Carlo Distribution */}
      <div className="mb-4 p-3 bg-white/20 border border-gray-200/30">
        <MonteCarloChart confM1={confM1} />
      </div>

      {/* T(e,p,t) Tensor Display */}
      <div className="mb-4 p-3 bg-white/20 border border-gray-200/30">
        <div className="font-mono text-[8px] text-gray-400 uppercase tracking-widest mb-2">
          &gt; TENSOR T(e,p,t) / 三维张量
        </div>
        <div className="flex flex-col gap-1">
          {[6, 5, 4, 3, 2, 1].map(bitIndex => {
            const idx = bitIndex - 1
            const E = nodeInfo?.E?.[idx] ?? 1.0
            const B = deterministic?.current_node?.code?.[idx]

            // Simplified t, e, p values
            const t = Math.max(0, Math.min(1, 1 - E))
            const e = B === '1' ? 0.2 : 0.8  // simplified
            const p = (bitIndex % 2 === 1) === (B === '1') ? 1 : -1

            return (
              <div key={bitIndex} className="flex items-center gap-2 text-[8px]">
                <span className="font-mono text-gray-400 w-14 shrink-0">
                  {BIT_LABELS_SHORT[bitIndex]}
                </span>
                <div className="flex gap-2 flex-1">
                  <span className="text-gray-500">
                    t=<span className="text-gray-700 font-mono">{t.toFixed(2)}</span>
                  </span>
                  <span className="text-gray-500">
                    e=<span className="text-gray-700 font-mono">{e.toFixed(2)}</span>
                  </span>
                  <span className="text-gray-500">
                    p=<span className={p === 1 ? 'text-gray-900' : 'text-gray-400'}>{p}</span>
                  </span>
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Typewriter Log */}
      <div className="mb-4 p-3 bg-white/20 border border-gray-200/30">
        <div className="font-mono text-[8px] text-gray-400 uppercase tracking-widest mb-2">
          &gt; RAG LOG / 历史报错日志
        </div>
        <TypewriterLog entries={typewriterLogs} />
        {typewriterLogs.length === 0 && (
          <div className="font-mono text-[8px] text-gray-400 italic">
            No events yet...
          </div>
        )}
      </div>

      {/* Physics description */}
      {deterministic?.current_node?.physics_description && (
        <div className="mb-4 p-3 bg-white/20 border border-gray-200/30">
          <div className="font-mono text-[8px] text-gray-400 uppercase tracking-widest mb-2">
            &gt; STATE DESC / 状态描述
          </div>
          <div
            className="text-[9px] text-gray-700 leading-relaxed"
            style={{ fontFamily: "'Noto Serif SC', serif" }}
          >
            {deterministic.current_node.physics_description}
          </div>
        </div>
      )}
    </div>
  )
}
