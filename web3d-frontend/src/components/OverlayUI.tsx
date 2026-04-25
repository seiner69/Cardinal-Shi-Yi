import { useState, useEffect } from 'react'
import { useStore } from '../store/useStore'
import { LeftConsole } from './LeftConsole'
import { CenterOutput } from './CenterOutput'
import { RightConsole } from './RightConsole'

// =============================================================================
// Bottom Console — LLM Query Input (preserved)
// =============================================================================

function BottomConsole() {
  const [input, setInput] = useState('')
  const { isLoading, fetchInfer, setQuery, fsmData } = useStore()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return
    setQuery(input)
    await fetchInfer(input)
  }

  return (
    <div className="absolute bottom-8 left-1/2 -translate-x-1/2 pointer-events-auto w-[540px] max-w-[92vw]">
      <form onSubmit={handleSubmit} className="relative">
        <div
          className="relative flex items-center gap-4 bg-transparent border border-gray-300/40 px-6 py-4"
        >
          <span
            className="text-xl text-gray-400/50 shrink-0"
            style={{ fontFamily: "'Noto Serif SC', serif" }}
          >
            ☯
          </span>

          <span className="font-mono text-[10px] text-gray-400/50 shrink-0">&gt;</span>

          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={fsmData ? '输入历史事件 | SSOT模式已激活' : '输入历史事件 | 推演宇宙拓扑'}
            disabled={isLoading}
            className="flex-1 bg-transparent font-mono text-sm text-gray-800 placeholder:text-gray-400 outline-none disabled:opacity-40"
          />

          <div className="flex items-center gap-2 shrink-0">
            {isLoading && (
              <div className="flex gap-1 items-center">
                <span className="w-1 h-1 rounded-full bg-gray-400 animate-bounce [animation-delay:0ms]" />
                <span className="w-1 h-1 rounded-full bg-gray-400 animate-bounce [animation-delay:150ms]" />
                <span className="w-1 h-1 rounded-full bg-gray-400 animate-bounce [animation-delay:300ms]" />
              </div>
            )}

            <button
              type="submit"
              disabled={isLoading || !input.trim()}
              className="bg-transparent border-[4px] border-[#9f1239] text-[#9f1239] hover:bg-[#9f1239] hover:text-[#f5f5f0] font-serif font-black tracking-[0.5em] px-10 py-2 transition-colors cursor-pointer disabled:opacity-30 disabled:cursor-not-allowed"
            >
              推演
            </button>
          </div>
        </div>
      </form>
    </div>
  )
}

// =============================================================================
// Legacy LLM Panel (shown when fsmData is available from /api/infer)
// =============================================================================

function LegacyPanel() {
  const fsmData = useStore((s) => s.fsmData)
  const deterministic = useStore((s) => s.deterministic)
  const simulateFlips = useStore((s) => s.simulateFlips)
  const simulateFlip = useStore((s) => s.simulateFlip)
  const evolve = useStore((s) => s.evolve)

  // Load simulation when fsmData arrives
  useEffect(() => {
    if (!fsmData) return
    const bits = fsmData.inner_bits + fsmData.outer_bits
    simulateFlip(bits)
  }, [fsmData, simulateFlip])

  if (!fsmData) return null

  const bits = fsmData.inner_bits + fsmData.outer_bits

  const handleFlipSelect = async (flip: any) => {
    try {
      await evolve(flip.new_bits, 1)
    } catch (err) {
      console.error('evolve error:', err)
    }
  }

  return (
    <div className="absolute bottom-36 left-1/2 -translate-x-1/2 pointer-events-auto w-[700px] max-w-[92vw]">
      <div className="bg-white/30 backdrop-blur-sm border border-gray-300/30 p-4">
        {/* Header */}
        <div className="flex items-center gap-3 mb-3">
          <div className="h-px flex-1 bg-gradient-to-r from-gray-300/30 to-transparent" />
          <span className="font-mono text-[10px] text-gray-600 uppercase tracking-[0.25em] whitespace-nowrap">
            LLM ANALYSIS · 语义分析层
          </span>
          <div className="h-px flex-1 bg-gradient-to-l from-gray-300/30 to-transparent" />
        </div>

        {/* System definitions */}
        <div className="grid grid-cols-2 gap-4 mb-3">
          <div className="border-b border-[#d4d4d8] pb-2">
            <div className="font-mono text-[8px] text-gray-400 uppercase tracking-widest mb-1">
              INNER / 内系统
            </div>
            <div className="text-xs text-gray-700 leading-relaxed" style={{ fontFamily: "'Noto Serif SC', serif" }}>
              {fsmData.inner_system}
            </div>
          </div>
          <div className="border-b border-[#d4d4d8] pb-2">
            <div className="font-mono text-[8px] text-gray-400 uppercase tracking-widest mb-1">
              OUTER / 外系统
            </div>
            <div className="text-xs text-gray-700 leading-relaxed" style={{ fontFamily: "'Noto Serif SC', serif" }}>
              {fsmData.outer_system}
            </div>
          </div>
        </div>

        {/* Stress analysis */}
        <div className="grid grid-cols-2 gap-4 mb-3">
          <div>
            <div className="font-mono text-[8px] text-gray-400 uppercase tracking-widest mb-1">
              执行指针 · {fsmData.energy_focus.focus_bit}
            </div>
            <div className="text-xs text-gray-800 leading-relaxed" style={{ fontFamily: "'Noto Serif SC', serif" }}>
              {fsmData.energy_focus.focus_description}
            </div>
          </div>
          <div>
            <div className="font-mono text-[8px] text-gray-400 uppercase tracking-widest mb-1">
              应力状态 · {fsmData.stress_analysis.stress_type}
            </div>
            <div className="text-xs text-gray-800 leading-relaxed" style={{ fontFamily: "'Noto Serif SC', serif" }}>
              {fsmData.stress_analysis.analysis}
            </div>
          </div>
        </div>

        {/* Target hexagram + mutation */}
        <div className="grid grid-cols-3 gap-4 mb-3">
          <div className="text-center">
            <div className="font-mono text-[8px] text-gray-400 uppercase tracking-widest mb-1">目标卦</div>
            <div className="text-2xl text-gray-900 font-bold" style={{ fontFamily: "'Noto Serif SC', serif" }}>
              {fsmData.target_hexagram}
            </div>
          </div>
          <div className="col-span-2">
            <div className="font-mono text-[8px] text-gray-400 uppercase tracking-widest mb-1">推演策略</div>
            <div className="text-xs text-gray-800 leading-relaxed" style={{ fontFamily: "'Noto Serif SC', serif" }}>
              {fsmData.mutation_suggestion}
            </div>
          </div>
        </div>

        {/* 6-bit code display */}
        <div className="flex items-center justify-center gap-2 mb-3">
          <span className="font-mono text-[8px] text-gray-400 uppercase">CODE</span>
          <div className="flex gap-1">
            {[6, 5, 4, 3, 2, 1].map((bitNum) => {
              const idx = bitNum - 1
              const val = bits[idx] ?? '?'
              const isFocused = fsmData.energy_focus.focus_bit === bitNum
              return (
                <div
                  key={bitNum}
                  className={[
                    'w-7 h-7 flex items-center justify-center border',
                    isFocused ? 'border-[#9f1239] bg-[#9f1239]/5' : 'border-gray-300/40',
                  ].join(' ')}
                >
                  <span className={`font-mono text-sm font-bold ${val === '1' ? 'text-gray-900' : 'text-gray-400'}`}>
                    {val}
                  </span>
                </div>
              )
            })}
          </div>
          <span className="font-mono text-[8px] text-gray-400 ml-2">
            {fsmData.target_hexagram}
          </span>
        </div>

        {/* Flips preview */}
        {simulateFlips.length > 0 && (
          <div className="flex flex-wrap gap-2 justify-center">
            {simulateFlips.map((flip) => (
              <button
                key={flip.bit}
                onClick={() => handleFlipSelect(flip)}
                className="flex flex-col items-center gap-0.5 px-3 py-1.5 border border-gray-300/40 hover:border-[#9f1239]/60 hover:bg-[#9f1239]/5 transition-all cursor-pointer min-w-[60px]"
              >
                <span className="font-mono text-[8px] text-gray-400">B{flip.bit}</span>
                <span className="text-base text-gray-900 font-bold" style={{ fontFamily: "'Noto Serif SC', serif" }}>
                  {flip.hexagram}
                </span>
              </button>
            ))}
          </div>
        )}

        {/* Deterministic kernel info */}
        {deterministic && (
          <div className="mt-3 pt-2 border-t border-gray-300/20 grid grid-cols-4 gap-2 text-center">
            <div>
              <div className="font-mono text-[7px] text-gray-400 uppercase">路径</div>
              <div className="font-mono text-[9px] text-[#9f1239] font-bold">
                {deterministic.evolution_path}
              </div>
            </div>
            <div>
              <div className="font-mono text-[7px] text-gray-400 uppercase">动爻</div>
              <div className="font-mono text-[9px] text-gray-800">Bit {deterministic.max_stress_bit}</div>
            </div>
            <div>
              <div className="font-mono text-[7px] text-gray-400 uppercase">应力</div>
              <div className="font-mono text-[9px] text-gray-800">{deterministic.stress_type}</div>
            </div>
            <div>
              <div className="font-mono text-[7px] text-gray-400 uppercase">熵值</div>
              <div className="font-mono text-[9px] text-gray-800">
                {deterministic.current_node?.entropy_S?.toFixed(4) ?? '—'}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

// =============================================================================
// Root Export
// =============================================================================

export default function OverlayUI() {
  return (
    <div className="absolute inset-0 pointer-events-none">
      {/* 顶部标题 */}
      <div className="absolute top-6 left-1/2 -translate-x-1/2 pointer-events-none">
        <div className="flex flex-col items-center gap-1">
          <div className="flex items-center gap-4">
            <div className="w-10 h-px bg-gradient-to-r from-transparent via-gray-400/20 to-transparent" />
            <span className="font-mono text-[11px] text-gray-500/60 uppercase tracking-[0.5em]">
              史易枢机
            </span>
            <div className="w-10 h-px bg-gradient-to-r from-transparent via-gray-400/20 to-transparent" />
          </div>
          <span
            className="text-[7px] text-gray-400/60 uppercase tracking-[0.4em]"
            style={{ fontFamily: "'Noto Serif SC', serif" }}
          >
            6-Bit FSM Topology Engine
          </span>
        </div>
      </div>

      {/* Three-column SSOT consoles */}
      <LeftConsole />
      <CenterOutput />
      <RightConsole />

      {/* LLM analysis overlay (when available) */}
      <LegacyPanel />

      {/* Bottom console */}
      <BottomConsole />
    </div>
  )
}
