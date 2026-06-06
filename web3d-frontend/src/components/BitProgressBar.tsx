import { useMemo } from 'react'

interface BitProgressBarProps {
  bitIndex: number
  B: number
  E: number
  E_initial: number
  P: number
  tau: number
  isActive: boolean
}

const BIT_LABELS_SHORT: Record<number, string> = {
  6: 'B6',
  5: 'B5',
  4: 'B4',
  3: 'B3',
  2: 'B2',
  1: 'B1',
}

export function BitProgressBar({
  bitIndex,
  B,
  E,
  E_initial,
  P,
  tau,
  isActive,
}: BitProgressBarProps) {
  const progress = useMemo(() => {
    if (B === 1) {
      const ratio = E_initial > 0 ? Math.max(0, E / E_initial) : 0
      return { type: 'energy' as const, value: ratio * 100 }
    }
    const ratio = tau > 0 ? Math.max(0, Math.min(100, (P / tau) * 100)) : 0
    return { type: 'pressure' as const, value: ratio }
  }, [B, E, E_initial, P, tau])

  const isDanger = progress.value > 80

  return (
    <div
      className={[
        'flex items-center gap-2 rounded-md px-2 py-1.5 transition-all',
        isActive ? 'bg-[#9f1239]/10' : 'bg-white/35',
      ].join(' ')}
    >
      <span className="w-6 shrink-0 font-mono text-[8px] text-[#8a8177]">
        {BIT_LABELS_SHORT[bitIndex]}
      </span>

      <div className="relative h-2 flex-1 overflow-hidden rounded bg-[#e6dfd4]/70">
        <div
          className={[
            'h-full transition-all duration-500',
            progress.type === 'energy' ? 'bg-[#0f766e]/70' : 'bg-[#6b6259]/70',
            isDanger ? 'animate-pulse' : '',
          ].join(' ')}
          style={{ width: `${Math.min(100, progress.value)}%` }}
        />
        <div
          className="absolute top-0 bottom-0 w-px bg-[#9f1239]/60"
          style={{ left: '80%' }}
        />
      </div>

      <span
        className={[
          'w-10 shrink-0 text-right font-mono text-[8px]',
          isDanger ? 'text-[#9f1239] font-bold' : 'text-[#6b6259]',
        ].join(' ')}
      >
        {progress.value.toFixed(0)}%
      </span>

      {isActive && (
        <span className="shrink-0 animate-pulse font-mono text-[7px] text-[#9f1239]">
          当前
        </span>
      )}
    </div>
  )
}
