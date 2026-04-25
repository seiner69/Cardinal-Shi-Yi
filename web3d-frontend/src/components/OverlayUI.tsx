import { useState, useEffect } from 'react'
import { useStore } from '../store/useStore'
import type { SimulateFlip } from '../store/useStore'

// =============================================================================
// Constants
// =============================================================================

const BIT_LABELS: Record<number, string> = {
  6: 'MACRO-CEILING / 宏观天花板',
  5: 'OPERATING-RULES / 运行规则',
  4: 'INTERFACE-LAYER / 基层接口',
  3: 'CORE-EGO / 核心意志',
  2: 'CONDUCTION-NET / 传导网络',
  1: 'PHYSICAL-BASE / 物理底座',
}

// =============================================================================
// Sub-components
// =============================================================================

function PanelShell({
  title,
  stepLabel,
  children,
  side,
}: {
  title: string
  stepLabel: string
  children: React.ReactNode
  side: 'left' | 'right'
}) {
  return (
    <div
      className={`absolute top-1/2 -translate-y-1/2 pointer-events-auto w-[340px] max-h-[88vh] overflow-y-auto ${
        side === 'left' ? 'left-4' : 'right-4'
      }`}
    >
      {/* Header label */}
      <div className="mb-3">
        <span className="font-mono text-[9px] text-gray-400 uppercase tracking-[0.3em]">
          {stepLabel}
        </span>
      </div>

      {/* Title bar */}
      <div className="flex items-center gap-3 mb-4">
        <div className="h-px flex-1 bg-gradient-to-r from-gray-300/30 to-transparent" />
        <span className="font-mono text-[10px] text-gray-600 uppercase tracking-[0.25em] whitespace-nowrap">
          {title}
        </span>
        <div className="h-px flex-1 bg-gradient-to-l from-gray-300/30 to-transparent" />
      </div>

      {/* Body: 文字直接写在宣纸上，无白色卡片 */}
      <div className="relative p-4">
        {children}
      </div>
    </div>
  )
}

function Divider({ label }: { label?: string }) {
  return (
    <div className="flex items-center gap-2 my-4">
      <div className="h-px flex-1 border-t border-gray-300/30" />
      {label && (
        <span className="font-mono text-[8px] text-gray-400 uppercase tracking-widest px-2">
          {label}
        </span>
      )}
      <div className="h-px flex-1 border-t border-gray-300/30" />
    </div>
  )
}

// =============================================================================
// Left Panel: 卷一：空间拓扑解剖
// =============================================================================

function LeftPanel() {
  const fsmData = useStore((s) => s.fsmData)
  const deterministic = useStore((s) => s.deterministic)
  const simulateFlips = useStore((s) => s.simulateFlips)
  const simulateFlip = useStore((s) => s.simulateFlip)
  const evolve = useStore((s) => s.evolve)

  if (!fsmData) return null

  const allBits = (fsmData.inner_bits + fsmData.outer_bits).split('')

  // 当 fsmData 变化时，加载变爻预览
  useEffect(() => {
    const bits = fsmData.inner_bits + fsmData.outer_bits
    simulateFlip(bits)
  }, [fsmData, simulateFlip])

  const handleFlipSelect = async (flip: SimulateFlip) => {
    try {
      await evolve(flip.new_bits, 1)
    } catch (err) {
      console.error('evolve error:', err)
    }
  }

  return (
    <PanelShell
      stepLabel="卷一：空间拓扑解剖 / 6-BIT CORE DUMP"
      title="MODULE 1: CORE DUMP"
      side="left"
    >
      {/* Step 1: 参照系划定 */}
      <div className="mb-3">
        <span className="font-mono text-[9px] text-gray-600 uppercase tracking-widest">
          &gt; STEP 1: 参照系划定
        </span>
      </div>

      {/* 内/外系统：直接写在宣纸上，用下划线分隔 */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className="border-b border-[#d4d4d8] pb-3">
          <div className="font-mono text-[8px] text-gray-400 uppercase tracking-widest mb-2">
            INNER / 内系统
          </div>
          <div
            className="text-xs text-gray-700 leading-relaxed"
            style={{ fontFamily: "'Noto Serif SC', serif" }}
          >
            {fsmData.inner_system}
          </div>
        </div>
        <div className="border-b border-[#d4d4d8] pb-3">
          <div className="font-mono text-[8px] text-gray-400 uppercase tracking-widest mb-2">
            OUTER / 外系统
          </div>
          <div
            className="text-xs text-gray-700 leading-relaxed"
            style={{ fontFamily: "'Noto Serif SC', serif" }}
          >
            {fsmData.outer_system}
          </div>
        </div>
      </div>

      <Divider label="STEP 2: MACHINE CODE EXTRACT" />

      {/* Step 2: 机器码提取 */}
      <div className="mb-2">
        <span className="font-mono text-[9px] text-gray-600 uppercase tracking-widest">
          &gt; STEP 2: 机器码提取
        </span>
      </div>

      {/* 表头 */}
      <div className="flex items-center gap-2 mb-2 px-1 font-mono text-[8px] text-gray-400 uppercase tracking-widest">
        <span className="w-5 text-center">BIT</span>
        <span className="w-5 text-center">VAL</span>
        <span>LAYER ARCHITECTURE</span>
      </div>

      {/* B1-B6 列表 */}
      <div className="flex flex-col gap-[2px]">
        {[6, 5, 4, 3, 2, 1].map((bitNum) => {
          const idx = bitNum - 1
          const val = allBits[idx] ?? '?'
          const isYang = val === '1'
          const isFocused = fsmData.energy_focus.focus_bit === bitNum

          return (
            <div
              key={bitNum}
              className={[
                'flex items-center gap-2 px-2 py-1.5 border-b border-transparent transition-colors',
                isFocused ? 'border-[#9f1239]/30' : '',
              ].join(' ')}
            >
              {/* BIT 编号 */}
              <span className="w-5 text-center font-mono text-[10px] text-gray-400">
                B{bitNum}
              </span>

              {/* 数值：墨黑色 */}
              <span
                className={`w-5 text-center font-mono text-lg font-bold ${
                  isYang ? 'text-gray-900' : 'text-gray-500'
                }`}
              >
                {val}
              </span>

              {/* 层级名 */}
              <span
                className={[
                  'font-mono text-[9px] tracking-wide flex-1',
                  isYang ? 'text-gray-700' : 'text-gray-400',
                ].join(' ')}
              >
                {BIT_LABELS[bitNum]}
              </span>

              {/* PC 指针 — 深朱砂红 */}
              {isFocused && (
                <span
                  className="font-mono text-[8px] text-[#9f1239] tracking-widest animate-pulse"
                >
                  ◀ PC
                </span>
              )}
            </div>
          )
        })}
      </div>

      <Divider label="TARGET HEXAGRAM" />

      {/* 目标卦象：直接写字，无卡片 */}
      <div className="grid grid-cols-2 gap-4">
        <div className="border-b border-[#d4d4d8] pb-3 text-center">
          <div className="font-mono text-[8px] text-gray-400 uppercase tracking-widest mb-2">
            目标卦象
          </div>
          <div
            className="text-2xl text-gray-900"
            style={{ fontFamily: "'Noto Serif SC', serif" }}
          >
            {fsmData.target_hexagram}
          </div>
          <div className="font-mono text-[7px] text-gray-400 uppercase tracking-widest mt-1">
            HEXAGRAM
          </div>
        </div>
        <div className="border-b border-[#d4d4d8] pb-3 text-center">
          <div className="font-mono text-[8px] text-gray-400 uppercase tracking-widest mb-2">
            推导理由
          </div>
          <div
            className="text-[10px] text-gray-800 leading-relaxed"
            style={{ fontFamily: "'Noto Serif SC', serif" }}
          >
            {fsmData.hexagram_reason}
          </div>
        </div>
      </div>

      <Divider label="BIT FLIP PREVIEW / 变爻预览" />

      {/* 6 种变爻预览：确定性硬算 */}
      <div className="mb-4">
        <div className="font-mono text-[8px] text-gray-400 uppercase tracking-widest mb-2">
          &gt; V2.0 确定性演化 — 选择变爻
        </div>
        <div className="flex flex-wrap gap-2">
          {simulateFlips.length > 0 ? simulateFlips.map((flip) => (
            <button
              key={flip.bit}
              onClick={() => handleFlipSelect(flip)}
              className="flex flex-col items-center gap-1 px-3 py-2 border border-gray-300/40 hover:border-[#9f1239]/60 hover:bg-[#9f1239]/5 transition-all cursor-pointer min-w-[72px]"
            >
              <div className="font-mono text-[9px] text-gray-500">
                B{flip.bit}
              </div>
              <div
                className="text-lg text-gray-900 font-bold"
                style={{ fontFamily: "'Noto Serif SC', serif" }}
              >
                {flip.hexagram}
              </div>
              <div className="font-mono text-[8px] text-gray-400">
                {flip.old_val}→{flip.new_val}
              </div>
            </button>
          )) : (
            <div className="font-mono text-[9px] text-gray-400 italic">
              {fsmData ? '加载变爻预览中...' : '—'}
            </div>
          )}
        </div>
      </div>

      {/* 确定性硬算层信息（V2.0） */}
      {deterministic && (
        <div className="border-t border-gray-300/30 pt-3">
          <div className="font-mono text-[8px] text-gray-400 uppercase tracking-widest mb-2">
            &gt; DETERMINISTIC KERNEL / 影子协议 V2.0
          </div>
          <div className="grid grid-cols-2 gap-x-4 gap-y-1">
            <div className="font-mono text-[8px] text-gray-400 uppercase">演化路径</div>
            <div className="font-mono text-[9px] text-[#9f1239] font-bold">
              {deterministic.evolution_path_name}
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
              {deterministic.current_node.entropy_S.toFixed(2)}
            </div>
          </div>
        </div>
      )}
    </PanelShell>
  )
}

// =============================================================================
// Right Panel: 卷二：时间动力与推演
// =============================================================================

function RightPanel() {
  const fsmData = useStore((s) => s.fsmData)
  if (!fsmData) return null

  const stressType = fsmData.stress_analysis.stress_type

  return (
    <PanelShell
      stepLabel="卷二：时间动力与推演 / FSM TOPOLOGY DYNAMICS"
      title="MODULE 2: DYNAMICS"
      side="right"
    >
      {/* Step 3: 执行指针 */}
      <div className="mb-3">
        <span className="font-mono text-[9px] text-gray-600 uppercase tracking-widest">
          &gt; STEP 3: 执行指针
        </span>
      </div>

      {/* 算力焦点：无卡片，直接写字 */}
      <div className="mb-3">
        <div className="flex items-center justify-between">
          <div>
            <div className="font-mono text-[8px] text-gray-400 uppercase tracking-widest mb-2">
              算力当前位置
            </div>
            {/* 深朱砂红焦点字 */}
            <div
              className="text-4xl font-black"
              style={{
                fontFamily: "'Noto Serif SC', serif",
                color: '#9f1239',
                letterSpacing: '0.05em',
              }}
            >
              Bit {fsmData.energy_focus.focus_bit}
            </div>
          </div>
          <div className="text-right">
            <div className="font-mono text-[8px] text-gray-400 uppercase tracking-widest mb-2">
              层级名称
            </div>
            <div
              className="text-sm text-gray-700"
              style={{ fontFamily: "'Noto Serif SC', serif" }}
            >
              {BIT_LABELS[fsmData.energy_focus.focus_bit]}
            </div>
          </div>
        </div>
        <div className="mt-3 pt-2 border-t border-gray-300/30">
          <div className="font-mono text-[8px] text-gray-400 uppercase tracking-widest mb-2">
            核心症结
          </div>
          <div
            className="text-xs text-gray-800 leading-relaxed"
            style={{ fontFamily: "'Noto Serif SC', serif" }}
          >
            {fsmData.energy_focus.focus_description}
          </div>
        </div>
      </div>

      {/* Step 4: 物理力学 */}
      <div className="mb-3">
        <span className="font-mono text-[9px] text-gray-600 uppercase tracking-widest">
          &gt; STEP 4: 物理力学 / STRESS CALCULATION
        </span>
      </div>
      <div className="mb-3">
        <div className="mb-2">
          <div className="font-mono text-[8px] text-gray-400 uppercase tracking-widest mb-1">
            &gt; 重力/阻力测试...
          </div>
          <div className="font-mono text-[8px] text-gray-400 uppercase tracking-widest mb-2">
            应力状态
          </div>
          <div
            className="text-base font-bold text-gray-800"
            style={{ fontFamily: "'Noto Serif SC', serif" }}
          >
            {stressType}
          </div>
        </div>
        <div
          className="text-xs text-gray-800 leading-relaxed"
          style={{ fontFamily: "'Noto Serif SC', serif" }}
        >
          {fsmData.stress_analysis.analysis}
        </div>
      </div>

      {/* Step 5: 影子断言 */}
      <div className="mb-3">
        <span className="font-mono text-[9px] text-gray-600 uppercase tracking-widest">
          &gt; STEP 5: 影子断言 / SHADOW ASSERTION
        </span>
      </div>
      <div className="mb-4">
        <div className="font-mono text-[8px] text-gray-400 uppercase tracking-widest mb-2">
          &gt; PATCH: 推演策略
        </div>
        <div
          className="text-sm text-gray-800 leading-relaxed"
          style={{ fontFamily: "'Noto Serif SC', serif" }}
        >
          {fsmData.mutation_suggestion}
        </div>
      </div>

      {/* 开发者日志 / Hash Table 匹配 */}
      <details
        className="border-t border-gray-300/30"
      >
        <summary
          className="font-mono text-[8px] text-gray-400 uppercase tracking-widest cursor-pointer py-2"
        >
          [ 开发者日志 / HASH TABLE MATCHING ]
        </summary>
        <div className="pb-2">
          <div className="mt-2 space-y-3">
            <div>
              <div className="font-mono text-[8px] text-gray-400 uppercase tracking-widest mb-1">
                引用的爻辞
              </div>
              <div
                className="text-xs text-gray-800 italic leading-relaxed"
                style={{ fontFamily: "'Noto Serif SC', serif" }}
              >
                "{fsmData.referenced_yao || '—'}"
              </div>
            </div>
            <div>
              <div className="font-mono text-[8px] text-gray-400 uppercase tracking-widest mb-1">
                易理映射
              </div>
              <div
                className="text-xs text-gray-800 leading-relaxed"
                style={{ fontFamily: "'Noto Serif SC', serif" }}
              >
                {fsmData.yao_interpretation || '—'}
              </div>
            </div>
          </div>
        </div>
      </details>
    </PanelShell>
  )
}

// =============================================================================
// Bottom Console
// =============================================================================

function BottomConsole() {
  const [input, setInput] = useState('')
  const { isLoading, fetchInfer, setQuery } = useStore()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return
    setQuery(input)
    await fetchInfer(input)
  }

  return (
    <div className="absolute bottom-8 left-1/2 -translate-x-1/2 pointer-events-auto w-[540px] max-w-[92vw]">
      <form onSubmit={handleSubmit} className="relative">
        {/* 主输入框：极简边框，文字写在宣纸上 */}
        <div
          className="relative flex items-center gap-4 bg-transparent border border-gray-300/40 px-6 py-4"
        >
          {/* 太极符号 */}
          <span
            className="text-xl text-gray-400/50 shrink-0"
            style={{ fontFamily: "'Noto Serif SC', serif" }}
          >
            ☯
          </span>

          {/* 输入提示符 */}
          <span className="font-mono text-[10px] text-gray-400/50 shrink-0">&gt;</span>

          {/* 输入框 */}
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="输入历史事件 | 推演宇宙拓扑"
            disabled={isLoading}
            className="flex-1 bg-transparent font-mono text-sm text-gray-800 placeholder:text-gray-400 outline-none disabled:opacity-40"
          />

          {/* 加载动画 */}
          <div className="flex items-center gap-2 shrink-0">
            {isLoading && (
              <div className="flex gap-1 items-center">
                <span className="w-1 h-1 rounded-full bg-gray-400 animate-bounce [animation-delay:0ms]" />
                <span className="w-1 h-1 rounded-full bg-gray-400 animate-bounce [animation-delay:150ms]" />
                <span className="w-1 h-1 rounded-full bg-gray-400 animate-bounce [animation-delay:300ms]" />
              </div>
            )}

            {/* 朱砂印章按钮：空心方印章 */}
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

      <LeftPanel />
      <RightPanel />
      <BottomConsole />
    </div>
  )
}