import { useStore } from '../store/useStore'
import { BitProgressBar } from './BitProgressBar'
import { DeltaMDisplay } from './DeltaMDisplay'

export function CenterOutput() {
  const nodeInfo = useStore(s => s.nodeInfo)
  const deterministic = useStore(s => s.deterministic)
  const simulateFlips = useStore(s => s.simulateFlips)

  const bits = nodeInfo?.bits ?? ''
  const activeBit = deterministic?.max_stress_bit ?? null

  // Find next bits from flips (flip the active bit)
  let nextBits: string | null = null
  if (bits && activeBit !== null && simulateFlips.length > 0) {
    const flip = simulateFlips.find(f => f.bit === activeBit)
    if (flip) {
      nextBits = flip.new_bits
    }
  }

  return (
    <div className="absolute top-1/2 -translate-y-1/2 left-1/2 -translate-x-1/2 pointer-events-auto w-[380px] max-h-[88vh] overflow-y-auto">
      {/* Header */}
      <div className="mb-3 text-center">
        <span className="font-mono text-[9px] text-gray-400 uppercase tracking-[0.3em]">
          ENGINE OUTPUTS / 核心输出
        </span>
      </div>

      {/* Progress bars section */}
      <div className="mb-4 p-3 bg-white/20 border border-gray-200/30">
        <div className="font-mono text-[8px] text-gray-400 uppercase tracking-widest mb-2">
          &gt; LAYER VITALITY / 层级活力
        </div>
        <div className="flex flex-col gap-0.5">
          {[6, 5, 4, 3, 2, 1].map(bitIndex => {
            const idx = bitIndex - 1
            return (
              <BitProgressBar
                key={bitIndex}
                bitIndex={bitIndex}
                B={bits[idx] ? parseInt(bits[idx]) : 0}
                E={nodeInfo?.E?.[idx] ?? 1.0}
                E_initial={1.0}
                P={nodeInfo?.P?.[idx] ?? 0}
                tau={nodeInfo?.tau?.[idx] ?? 1.0}
                isActive={activeBit === bitIndex}
              />
            )
          })}
        </div>
      </div>

      {/* DeltaM Transition */}
      <div className="mb-4 p-3 bg-white/20 border border-gray-200/30">
        <DeltaMDisplay
          currentBits={bits}
          nextBits={nextBits}
          activeBit={activeBit}
        />
      </div>

      {/* Evolution path info */}
      {deterministic && (
        <div className="p-3 bg-white/20 border border-gray-200/30">
          <div className="font-mono text-[8px] text-gray-400 uppercase tracking-widest mb-2">
            &gt; EVOLUTION PATH / 演化路径
          </div>
          <div className="grid grid-cols-2 gap-x-4 gap-y-1">
            <div className="font-mono text-[8px] text-gray-400 uppercase">Path</div>
            <div className="font-mono text-[9px] text-[#9f1239] font-bold">
              {deterministic.evolution_path} — {deterministic.evolution_path_name}
            </div>
            <div className="font-mono text-[8px] text-gray-400 uppercase">动爻</div>
            <div className="font-mono text-[9px] text-gray-800">
              Bit {deterministic.max_stress_bit}
            </div>
            <div className="font-mono text-[8px] text-gray-400 uppercase">应力</div>
            <div className="font-mono text-[9px] text-gray-800">
              {deterministic.stress_type}
            </div>
            <div className="font-mono text-[8px] text-gray-400 uppercase">熵值</div>
            <div className="font-mono text-[9px] text-gray-800">
              {deterministic.current_node?.entropy_S?.toFixed(4) ?? '—'}
            </div>
          </div>
        </div>
      )}

      {/* Prediction Matrix - all 6 flips */}
      {simulateFlips.length > 0 && (
        <div className="mt-4 p-3 bg-white/20 border border-gray-200/30">
          <div className="font-mono text-[8px] text-gray-400 uppercase tracking-widest mb-2">
            &gt; ALL FLIPS / 全员变爻预览
          </div>
          <div className="flex flex-wrap gap-2">
            {simulateFlips.map(flip => (
              <div
                key={flip.bit}
                className={[
                  'flex flex-col items-center gap-0.5 px-2 py-1 border transition-all min-w-[56px]',
                  flip.bit === activeBit
                    ? 'border-[#9f1239]/60 bg-[#9f1239]/5'
                    : 'border-gray-300/40 bg-white/20',
                ].join(' ')}
              >
                <span className="font-mono text-[8px] text-gray-400">B{flip.bit}</span>
                <span
                  className="text-lg font-bold text-gray-900"
                  style={{ fontFamily: "'Noto Serif SC', serif" }}
                >
                  {flip.hexagram}
                </span>
                <span className="font-mono text-[7px] text-gray-400">
                  {flip.old_val}→{flip.new_val}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
