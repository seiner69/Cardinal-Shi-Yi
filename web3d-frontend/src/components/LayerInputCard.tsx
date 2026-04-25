import { useState } from 'react'

const BIT_LABELS: Record<number, string> = {
  6: 'MACRO-CEILING / 宏观天花板',
  5: 'OPERATING-RULES / 运行规则',
  4: 'INTERFACE-LAYER / 基层接口',
  3: 'CORE-EGO / 核心意志',
  2: 'CONDUCTION-NET / 传导网络',
  1: 'PHYSICAL-BASE / 物理底座',
}

interface LayerInputCardProps {
  bitIndex: number    // 1-6
  B: number          // 0 or 1
  E?: number         // energy (0-1)
  P?: number         // pressure
  R?: number         // dissipation
  tau?: number       // yield
  isActive?: boolean // is max stress bit?
  onToggle?: (bitIndex: number, newB: number) => void
}

export function LayerInputCard({
  bitIndex,
  B,
  E = 1.0,
  P = 0,
  R = 0.1,
  tau = 1.0,
  isActive = false,
  onToggle,
}: LayerInputCardProps) {
  const [collapsed, setCollapsed] = useState(false)

  const handleToggle = () => {
    if (onToggle) {
      onToggle(bitIndex, B === 1 ? 0 : 1)
    }
  }

  return (
    <div
      className={[
        'border transition-all',
        isActive ? 'border-[#9f1239]/50 bg-[#9f1239]/3' : 'border-gray-200/40 bg-white/20',
        collapsed ? '' : 'mb-1',
      ].join(' ')}
    >
      {/* Header */}
      <button
        onClick={() => setCollapsed(c => !c)}
        className="w-full flex items-center gap-2 px-2 py-1.5 hover:bg-gray-100/20 transition-colors"
      >
        {/* BIT number */}
        <span
          className={[
            'font-mono text-[9px] font-bold w-5 text-center shrink-0',
            B === 1 ? 'text-gray-900' : 'text-gray-400',
          ].join(' ')}
        >
          B{bitIndex}
        </span>

        {/* Layer name */}
        <span
          className={[
            'font-mono text-[7px] flex-1 text-left truncate',
            B === 1 ? 'text-gray-700' : 'text-gray-400',
          ].join(' ')}
        >
          {BIT_LABELS[bitIndex]}
        </span>

        {/* Boolean switch */}
        <div
          onClick={(e) => { e.stopPropagation(); handleToggle() }}
          className={[
            'w-8 h-4 rounded-full relative cursor-pointer transition-colors shrink-0',
            B === 1 ? 'bg-gray-800' : 'bg-gray-300',
          ].join(' ')}
        >
          <div
            className={[
              'absolute top-0.5 w-3 h-3 rounded-full bg-white shadow transition-all',
              B === 1 ? 'left-4' : 'left-0.5',
            ].join(' ')}
          />
        </div>

        {/* Collapse indicator */}
        <span className="font-mono text-[8px] text-gray-400 shrink-0">
          {collapsed ? '▶' : '▼'}
        </span>
      </button>

      {/* Expanded content */}
      {!collapsed && (
        <div className="px-2 pb-2 flex flex-col gap-1.5">
          <Divider />

          {/* E - Fuel */}
          <ParamRow label="E 燃料" value={E} max={1} unit="" color={B === 1 ? '#111' : '#9ca3af'} />

          {/* P - Pressure */}
          <ParamRow label="P 压强" value={P} max={tau} unit="" color={B === 0 ? '#374151' : '#9ca3af'} />

          {/* R - Dissipation */}
          <ParamRow label="R 耗散" value={R} max={1} unit="" color="#6b7280" />

          {/* τ - Threshold */}
          <ParamRow label="τ 阈值" value={tau} max={1} unit="" color="#9ca3af" />

          {/* Active indicator */}
          {isActive && (
            <div className="text-center font-mono text-[7px] text-[#9f1239] animate-pulse tracking-widest">
              ◀ EXECUTE POINTER
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function Divider() {
  return <div className="h-px bg-gray-200/30" />
}

interface ParamRowProps {
  label: string
  value: number
  max: number
  unit: string
  color?: string
}

function ParamRow({ label, value, max, unit, color = '#374151' }: ParamRowProps) {
  const pct = max > 0 ? Math.min(100, (value / max) * 100) : 0

  return (
    <div className="flex items-center gap-1.5">
      <span className="font-mono text-[7px] text-gray-400 w-14 shrink-0">{label}</span>
      <div className="flex-1 h-1 bg-gray-200/40 relative overflow-hidden">
        <div
          className="h-full transition-all"
          style={{ width: `${pct}%`, backgroundColor: color, opacity: 0.6 }}
        />
      </div>
      <span className="font-mono text-[7px] text-gray-500 w-10 text-right" style={{ color }}>
        {value.toFixed(2)}{unit}
      </span>
    </div>
  )
}
