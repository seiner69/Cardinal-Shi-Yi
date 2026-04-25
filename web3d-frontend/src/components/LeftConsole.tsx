import { useStore } from '../store/useStore'
import { LayerInputCard } from './LayerInputCard'

export function LeftConsole() {
  const nodeInfo = useStore(s => s.nodeInfo)
  const deterministic = useStore(s => s.deterministic)
  const isSimulating = useStore(s => s.isSimulating)
  const fetchNodeInfo = useStore(s => s.fetchNodeInfo)
  const simulateFlip = useStore(s => s.simulateFlip)

  const bits = nodeInfo?.bits ?? '000000'
  const activeBit = deterministic?.max_stress_bit ?? null

  const handleToggle = async (bitIndex: number, newB: number) => {
    // Build new bits by toggling one bit
    const bitsArr = bits.split('')
    bitsArr[bitIndex - 1] = String(newB)
    const newBits = bitsArr.join('')
    await fetchNodeInfo(newBits)
    await simulateFlip(newBits)
  }

  const handleExecute = async () => {
    if (!bits) return
    await simulateFlip(bits)
  }

  return (
    <div
      className="absolute top-1/2 -translate-y-1/2 left-4 pointer-events-auto w-[340px] max-h-[88vh] overflow-y-auto"
    >
      {/* Header */}
      <div className="mb-3">
        <span className="font-mono text-[9px] text-gray-400 uppercase tracking-[0.3em]">
          RAW INPUTS / 物理参数
        </span>
      </div>

      {/* Title bar */}
      <div className="flex items-center gap-3 mb-4">
        <div className="h-px flex-1 bg-gradient-to-r from-gray-300/30 to-transparent" />
        <span className="font-mono text-[10px] text-gray-600 uppercase tracking-[0.25em] whitespace-nowrap">
          SSOT CONTROL
        </span>
        <div className="h-px flex-1 bg-gradient-to-l from-gray-300/30 to-transparent" />
      </div>

      {/* Execute button */}
      <button
        onClick={handleExecute}
        disabled={isSimulating || !bits}
        className="w-full mb-4 bg-[#9f1239] hover:bg-[#7f1239] disabled:opacity-30 disabled:cursor-not-allowed text-white font-mono text-[10px] tracking-[0.3em] py-2 transition-colors"
      >
        {isSimulating ? '◌ EXECUTING...' : '▶ EXECUTE SIMULATION'}
      </button>

      {/* 6 Layer Cards */}
      <div className="flex flex-col gap-1">
        {[6, 5, 4, 3, 2, 1].map(bitIndex => {
          const idx = bitIndex - 1
          return (
            <LayerInputCard
              key={bitIndex}
              bitIndex={bitIndex}
              B={bits[idx] ? parseInt(bits[idx]) : 0}
              E={nodeInfo?.E?.[idx] ?? 1.0}
              P={nodeInfo?.P?.[idx] ?? 0}
              R={nodeInfo?.R?.[idx] ?? 0.1}
              tau={nodeInfo?.tau?.[idx] ?? 1.0}
              isActive={activeBit === bitIndex}
              onToggle={handleToggle}
            />
          )
        })}
      </div>

      {/* Current bits display */}
      <div className="mt-3 text-center">
        <span className="font-mono text-[8px] text-gray-400 uppercase tracking-widest">
          CURRENT STATE
        </span>
        <div className="font-mono text-xl text-gray-900 tracking-[0.2em] mt-1">
          {bits || '------'}
        </div>
      </div>
    </div>
  )
}
