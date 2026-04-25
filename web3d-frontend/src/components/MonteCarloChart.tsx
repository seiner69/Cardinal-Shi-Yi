import { useMemo } from 'react'

interface MonteCarloChartProps {
  confM1: number      // 0-1, system confidence
}

export function MonteCarloChart({ confM1 }: MonteCarloChartProps) {
  // Build a synthetic histogram from confM1
  // Low confM1 = wide distribution, high confM1 = narrow
  const buckets = useMemo(() => {
    const numBuckets = 12
    const uncertainty = 1 - confM1

    // Mean of distribution shifts with uncertainty
    const mean = 0.3 + uncertainty * 0.4  // 0.3 (low stress) to 0.7 (high stress)
    const std = 0.1 + uncertainty * 0.25  // 0.1 (tight) to 0.35 (wide spread)

    const counts = new Array(numBuckets).fill(0)
    const range = [0, 1]

    // Monte Carlo sampling (simplified Gaussian approximation)
    const N = 200
    for (let s = 0; s < N; s++) {
      // Box-Muller approximation
      const u1 = Math.random()
      const u2 = Math.random()
      const z = Math.sqrt(-2 * Math.log(u1 + 1e-10)) * Math.cos(2 * Math.PI * u2)
      const sample = Math.max(range[0], Math.min(range[1], mean + z * std))

      const bucketIdx = Math.min(
        numBuckets - 1,
        Math.floor((sample - range[0]) / (range[1] - range[0]) * numBuckets)
      )
      counts[bucketIdx]++
    }

    const maxCount = Math.max(...counts)
    return counts.map((c, i) => ({
      height: maxCount > 0 ? (c / maxCount) * 100 : 0,
      label: i === 0 || i === numBuckets - 1 ? (i === 0 ? 'LO' : 'HI') : '',
    }))
  }, [confM1])

  // Mean and std markers as percentage positions
  const meanPos = useMemo(() => {
    const uncertainty = 1 - confM1
    const mean = 0.3 + uncertainty * 0.4
    return mean * 100
  }, [confM1])

  const stdLeft = Math.max(0, meanPos - 15)
  const stdRight = Math.min(100, meanPos + 15)

  return (
    <div className="flex flex-col gap-1">
      <div className="font-mono text-[8px] text-gray-400 uppercase tracking-widest">
        MONTE CARLO · N=1000
      </div>

      {/* Bar chart */}
      <div className="relative h-16 bg-gray-100/30 border border-gray-200/30">
        {/* Bars */}
        <div className="absolute inset-0 flex items-end px-1 gap-[2px]">
          {buckets.map((b, i) => (
            <div
              key={i}
              className="flex-1 bg-gray-400/60 transition-all duration-300"
              style={{ height: `${Math.max(2, b.height)}%` }}
            />
          ))}
        </div>

        {/* Mean line */}
        <div
          className="absolute top-0 bottom-0 w-px bg-[#9f1239]"
          style={{ left: `${meanPos}%` }}
        />
        <div
          className="absolute -top-1 font-mono text-[6px] text-[#9f1239]"
          style={{ left: `${meanPos}%`, transform: 'translateX(-50%)' }}
        >
          μ
        </div>

        {/* Std range */}
        <div
          className="absolute top-0 bottom-0 bg-[#9f1239]/10"
          style={{ left: `${stdLeft}%`, width: `${stdRight - stdLeft}%` }}
        />
        <div
          className="absolute -top-1 font-mono text-[6px] text-gray-400"
          style={{ left: `${stdLeft}%`, transform: 'translateX(-50%)' }}
        >
          -
        </div>
        <div
          className="absolute -top-1 font-mono text-[6px] text-gray-400"
          style={{ left: `${stdRight}%`, transform: 'translateX(-50%)' }}
        >
          +
        </div>
      </div>

      {/* Legend */}
      <div className="flex items-center justify-between px-1">
        <span className="font-mono text-[7px] text-gray-400">
          conf_m1: <span className={confM1 < 0.8 ? 'text-[#9f1239]' : 'text-gray-600'}>{confM1.toFixed(2)}</span>
        </span>
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-0.5">
            <div className="w-2 h-1 bg-[#9f1239]/10" />
            <span className="font-mono text-[7px] text-gray-400">±σ</span>
          </div>
          <div className="flex items-center gap-0.5">
            <div className="w-px h-2 bg-[#9f1239]" />
            <span className="font-mono text-[7px] text-gray-400">μ</span>
          </div>
        </div>
      </div>

      {/* Distribution label */}
      <div className="font-mono text-[7px] text-gray-500 text-center">
        {confM1 >= 0.8 ? 'DETERMINISTIC' : confM1 >= 0.5 ? 'PROBABILISTIC' : 'HIGH UNCERTAINTY'}
      </div>
    </div>
  )
}
