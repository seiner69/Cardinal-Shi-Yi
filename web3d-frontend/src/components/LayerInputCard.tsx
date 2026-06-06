import { useState } from 'react'
import type { PhysicsLayer } from '../store/useStore'
import { eventLabel, ttlLabel } from '../utils/physicsLabels'

const BIT_LABELS: Record<number, string> = {
  6: '宏观天花板',
  5: '运行规则',
  4: '接口层',
  3: '核心意志',
  2: '传导网络',
  1: '物理底座',
}

interface LayerInputCardProps {
  bitIndex: number
  B: number
  E: number
  P: number
  R: number
  tau: number
  C?: number
  R_base?: number
  layer?: PhysicsLayer
  isActive?: boolean
  onToggle?: (bitIndex: number, newB: number) => void
  onParamChange?: (bitIndex: number, key: 'E' | 'P' | 'R' | 'R_base' | 'tau' | 'C', value: number) => void
}

export function LayerInputCard({
  bitIndex,
  B,
  E,
  P,
  R,
  tau,
  C = 0.15,
  R_base = R,
  layer,
  isActive = false,
  onToggle,
  onParamChange,
}: LayerInputCardProps) {
  const [collapsed, setCollapsed] = useState(false)
  const phase = layer?.phase ?? (B === 1 ? '1' : '0')
  const event = layer?.event ?? 'stable'
  const ttl = layer?.ttl

  const handleNumberChange = (
    key: 'E' | 'P' | 'R' | 'R_base' | 'tau' | 'C',
    rawValue: string
  ) => {
    const value = Number(rawValue)
    if (!Number.isFinite(value)) return
    onParamChange?.(bitIndex, key, Math.max(key === 'tau' ? 0.001 : 0, value))
  }

  return (
    <div
      className={[
        'rounded-md border transition-all',
        isActive ? 'border-[#9f1239]/50 bg-[#9f1239]/10 shadow-sm' : 'border-[#524639]/10 bg-white/50',
      ].join(' ')}
    >
      <button
        onClick={() => setCollapsed(c => !c)}
        className="flex w-full items-center gap-2 px-3 py-2 transition-colors hover:bg-white/60"
      >
        <span className="w-7 shrink-0 text-center font-mono text-[10px] font-bold text-[#26323f]">
          B{bitIndex}
        </span>
        <span className="flex-1 truncate text-left text-[12px] text-[#625950]">
          {BIT_LABELS[bitIndex]}
        </span>
        <span
          className={[
            'rounded border px-1.5 py-0.5 font-mono text-[9px]',
            phase.includes('*') ? 'border-[#9f1239]/40 text-[#9f1239]' : 'border-[#524639]/15 text-[#6b6259]',
          ].join(' ')}
        >
          {phase}
        </span>
        <div
          onClick={(event) => {
            event.stopPropagation()
            onToggle?.(bitIndex, B === 1 ? 0 : 1)
          }}
          className={[
            'relative h-5 w-9 shrink-0 cursor-pointer rounded-full transition-colors',
            B === 1 ? 'bg-[#26323f]' : 'bg-[#cfc8be]',
          ].join(' ')}
        >
          <div
            className={[
              'absolute top-0.5 h-4 w-4 rounded-full bg-white shadow transition-all',
              B === 1 ? 'left-[18px]' : 'left-0.5',
            ].join(' ')}
          />
        </div>
        <span className="shrink-0 font-mono text-[10px] text-[#8a8177]">
          {collapsed ? '+' : '-'}
        </span>
      </button>

      {!collapsed && (
        <div className="flex flex-col gap-2 px-3 pb-3">
          <div className="grid grid-cols-3 gap-1.5">
            <NumberField label="E" value={E} onChange={(value) => handleNumberChange('E', value)} />
            <NumberField label="P" value={P} onChange={(value) => handleNumberChange('P', value)} />
            <NumberField label="R" value={R} onChange={(value) => handleNumberChange('R', value)} />
            <NumberField label="tau" value={tau} onChange={(value) => handleNumberChange('tau', value)} />
            <NumberField label="C" value={C} onChange={(value) => handleNumberChange('C', value)} />
            <NumberField label="Rb" value={R_base} onChange={(value) => handleNumberChange('R_base', value)} />
          </div>

          <div className="flex items-center justify-between rounded bg-white/50 px-2 py-1 font-mono text-[8px] text-[#6b6259]">
            <span className={isActive ? 'text-[#9f1239] font-bold' : ''}>
              {eventLabel(event)}
            </span>
            <span>TTL {ttlLabel(ttl)}</span>
            <span>sigma {(layer?.sigma ?? 0).toFixed(2)}</span>
          </div>
        </div>
      )}
    </div>
  )
}

interface NumberFieldProps {
  label: string
  value: number
  onChange: (value: string) => void
}

function NumberField({ label, value, onChange }: NumberFieldProps) {
  return (
    <label className="flex items-center gap-1">
      <span className="w-6 shrink-0 font-mono text-[8px] text-[#8a8177]">{label}</span>
      <input
        type="number"
        step="0.01"
        min="0"
        value={Number.isFinite(value) ? value : 0}
        onChange={(event) => onChange(event.target.value)}
        className="field-input px-1.5 py-1 font-mono text-[9px]"
      />
    </label>
  )
}
