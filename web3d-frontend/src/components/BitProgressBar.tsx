import { useMemo } from 'react'

interface BitProgressBarProps {
  bitIndex: number       // 1-6
  B: number              // 0 or 1
  E: number              // current energy (0-1)
  E_initial: number      // initial energy (0-1)
  P: number              // current pressure
  tau: number            // yield threshold
  isActive: boolean      // is this the max stress bit?
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
  // Compute progress percentage
  // For B=1 (energy depletion): E/E_initial
  // For B=0 (pressure buildup): P/tau
  const progress = useMemo(() => {
    if (B === 1) {
      const ratio = E_initial > 0 ? Math.max(0, E / E_initial) : 0
      return { type: 'energy' as const, value: ratio * 100 }
    } else {
      const ratio = tau > 0 ? Math.max(0, Math.min(100, (P / tau) * 100)) : 0
      return { type: 'pressure' as const, value: ratio }
    }
  }, [B, E, E_initial, P, tau])

  const isDanger = progress.value > 80

  return (
    <div
      className={[
        'flex items-center gap-2 px-2 py-1.5 border-b border-transparent transition-all',
        isActive ? 'border-[#9f1239]/40 bg-[#9f1239]/5' : '',
      ].join(' ')}
    >
      {/* BIT label */}
      <span className="font-mono text-[8px] text-gray-400 w-6 shrink-0">
        {BIT_LABELS_SHORT[bitIndex]}
      </span>

      {/* Progress bar track */}
      <div className="flex-1 h-2 bg-gray-200/40 relative overflow-hidden">
        <div
          className={[
            'h-full transition-all duration-500',
            progress.type === 'energy' ? 'bg-gray-400' : 'bg-gray-600',
            isDanger ? 'animate-pulse' : '',
          ].join(' ')}
          style={{ width: `${Math.min(100, progress.value)}%` }}
        />
        {/* Threshold line at ~80% */}
        <div
          className="absolute top-0 bottom-0 w-px bg-[#9f1239]/60"
          style={{ left: '80%' }}
        />
      </div>

      {/* Percentage */}
      <span
        className={[
          'font-mono text-[8px] w-10 text-right shrink-0',
          isDanger ? 'text-[#9f1239] font-bold' : 'text-gray-500',
        ].join(' ')}
      >
        {progress.value.toFixed(0)}%
      </span>

      {/* Active indicator */}
      {isActive && (
        <span className="font-mono text-[7px] text-[#9f1239] animate-pulse shrink-0">
          ◀ PC
        </span>
      )}
    </div>
  )
}
