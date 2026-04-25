import { useEffect, useState } from 'react'

interface DeltaMDisplayProps {
  currentBits: string    // e.g. "111000"
  nextBits: string | null
  activeBit: number | null  // 1-6, the one that will flip
}

export function DeltaMDisplay({ currentBits, nextBits, activeBit }: DeltaMDisplayProps) {
  const [blink, setBlink] = useState(true)

  // Blink animation for active bit
  useEffect(() => {
    if (activeBit === null) return
    const interval = setInterval(() => setBlink(b => !b), 600)
    return () => clearInterval(interval)
  }, [activeBit])

  if (!currentBits) return null

  const bits = currentBits.split('')

  return (
    <div className="flex flex-col gap-2">
      {/* Label */}
      <div className="font-mono text-[8px] text-gray-400 uppercase tracking-widest">
        &gt; ΔM STATE TRANSITION
      </div>

      {/* Current bits → Next bits */}
      <div className="flex items-center gap-2">
        {/* Current state */}
        <div className="flex gap-1">
          {[6, 5, 4, 3, 2, 1].map((bitNum) => {
            const isActive = bitNum === activeBit
            return (
              <span
                key={bitNum}
                className={[
                  'font-mono text-lg font-bold w-5 text-center',
                  bits[bitNum - 1] === '1' ? 'text-gray-900' : 'text-gray-400',
                  isActive && blink ? 'text-[#9f1239] animate-pulse' : '',
                ].join(' ')}
              >
                {bits[bitNum - 1]}
              </span>
            )
          })}
        </div>

        {/* Arrow */}
        <span className="font-mono text-gray-400">→</span>

        {/* Next state */}
        {nextBits ? (
          <div className="flex gap-1">
            {nextBits.split('').map((b, idx) => {
              const bitNum = idx + 1
              const isActive = bitNum === activeBit
              return (
                <span
                  key={bitNum}
                  className={[
                    'font-mono text-lg font-bold w-5 text-center transition-colors',
                    b === '1' ? 'text-gray-900' : 'text-gray-400',
                    isActive && blink ? 'text-[#9f1239] animate-pulse' : '',
                  ].join(' ')}
                >
                  {b}
                </span>
              )
            })}
          </div>
        ) : (
          <span className="font-mono text-gray-400 text-sm">— —</span>
        )}
      </div>

      {/* Active bit annotation */}
      {activeBit !== null && (
        <div className="font-mono text-[8px] text-[#9f1239] animate-pulse">
          ◀ BIT {activeBit} — {blink ? '【ACTIVE FLIP】' : '【─────────】'}
        </div>
      )}
    </div>
  )
}
