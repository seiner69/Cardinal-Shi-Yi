import { useMemo } from 'react'
import type { MonteCarloOutcome } from '../store/useStore'

interface MonteCarloChartProps {
  confM1: number
  outcomes?: MonteCarloOutcome[]
}

function seededRandom(seed: number) {
  const x = Math.sin(seed) * 10000
  return x - Math.floor(x)
}

export function MonteCarloChart({ confM1, outcomes = [] }: MonteCarloChartProps) {
  const buckets = useMemo(() => {
    const numBuckets = 12
    const uncertainty = 1 - confM1
    const mean = 0.3 + uncertainty * 0.4
    const std = 0.1 + uncertainty * 0.25
    const counts = new Array<number>(numBuckets).fill(0)

    for (let s = 0; s < 200; s += 1) {
      const seedBase = Math.round(confM1 * 10000) + s * 2
      const u1 = seededRandom(seedBase + 1)
      const u2 = seededRandom(seedBase + 2)
      const z = Math.sqrt(-2 * Math.log(u1 + 1e-10)) * Math.cos(2 * Math.PI * u2)
      const sample = Math.max(0, Math.min(1, mean + z * std))
      counts[Math.min(numBuckets - 1, Math.floor(sample * numBuckets))] += 1
    }

    const maxCount = Math.max(...counts)
    return counts.map(count => (maxCount > 0 ? (count / maxCount) * 100 : 0))
  }, [confM1])

  return (
    <div className="flex flex-col gap-1">
      <div className="panel-title">
        蒙特卡洛 / 主要后继状态
      </div>

      {outcomes.length > 0 ? (
        <div className="flex flex-col gap-1">
          {outcomes.map((outcome) => (
            <div key={outcome.bits} className="grid grid-cols-[64px_1fr_42px] items-center gap-2">
              <span className="font-mono text-[8px] text-[#4f5d6a]">{outcome.bits}</span>
              <div className="h-2 overflow-hidden rounded bg-[#e6dfd4]/70">
                <div
                  className="h-full bg-[#0f766e]/70"
                  style={{ width: `${Math.max(2, outcome.probability * 100)}%` }}
                />
              </div>
              <span className="text-right font-mono text-[8px] text-[#6b6259]">
                {(outcome.probability * 100).toFixed(0)}%
              </span>
            </div>
          ))}
        </div>
      ) : (
        <div className="relative h-16 overflow-hidden rounded-md border border-[#524639]/10 bg-white/40">
          <div className="absolute inset-0 flex items-end px-1 gap-[2px]">
            {buckets.map((height, index) => (
              <div
                key={index}
                className="flex-1 bg-[#6b6259]/50 transition-all duration-300"
                style={{ height: `${Math.max(2, height)}%` }}
              />
            ))}
          </div>
        </div>
      )}

      <div className="flex items-center justify-between px-1">
        <span className="font-mono text-[7px] text-[#8a8177]">
          置信: <span className={confM1 < 0.8 ? 'text-[#9f1239]' : 'text-[#26323f]'}>{confM1.toFixed(2)}</span>
        </span>
        <span className="font-mono text-[7px] text-[#8a8177]">
          {outcomes.length > 0 ? `${outcomes.length} 个结果` : '预览分布'}
        </span>
      </div>
    </div>
  )
}
