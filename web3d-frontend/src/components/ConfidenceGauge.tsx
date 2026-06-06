interface ConfidenceGaugeProps {
  value: number
  size?: number
}

export function ConfidenceGauge({ value, size = 120 }: ConfidenceGaugeProps) {
  const clampedValue = Math.max(0, Math.min(1, value))
  const isLow = clampedValue < 0.8

  const cx = size / 2
  const cy = size / 2
  const r = size * 0.4
  const strokeWidth = size * 0.08
  const startAngle = 180
  const endAngle = 0
  const valueAngle = startAngle - clampedValue * (startAngle - endAngle)

  const polarToCartesian = (angle: number) => {
    const rad = (angle * Math.PI) / 180
    return {
      x: cx + r * Math.cos(rad),
      y: cy - r * Math.sin(rad),
    }
  }

  const describeArc = (fromAngle: number, toAngle: number) => {
    const from = polarToCartesian(fromAngle)
    const to = polarToCartesian(toAngle)
    const largeArcFlag = toAngle - fromAngle <= 180 ? '0' : '1'
    return `M ${from.x} ${from.y} A ${r} ${r} 0 ${largeArcFlag} 1 ${to.x} ${to.y}`
  }

  const needleTip = polarToCartesian(valueAngle)
  const needleBase1 = polarToCartesian(valueAngle - 3)
  const needleBase2 = polarToCartesian(valueAngle + 3)
  const needlePath = `M ${needleTip.x} ${needleTip.y} L ${needleBase1.x} ${needleBase1.y} L ${needleBase2.x} ${needleBase2.y} Z`

  const ticks = [0, 0.2, 0.4, 0.6, 0.8, 1.0].map(t => {
    const angle = startAngle - t * (startAngle - endAngle)
    const inner = polarToCartesian(angle)
    const outer = {
      x: cx + (r + strokeWidth * 0.8) * Math.cos((angle * Math.PI) / 180),
      y: cy - (r + strokeWidth * 0.8) * Math.sin((angle * Math.PI) / 180),
    }
    return { t, inner, outer }
  })

  return (
    <div className="flex flex-col items-center gap-1">
      <div className="panel-title">
        系统置信度
      </div>

      <svg
        width={size}
        height={size * 0.65}
        viewBox={`0 0 ${size} ${size * 0.65}`}
        className={isLow ? 'animate-pulse' : ''}
      >
        <path
          d={describeArc(startAngle, endAngle)}
          fill="none"
          stroke="#e6dfd4"
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        />
        <path
          d={describeArc(startAngle, startAngle - 90)}
          fill="none"
          stroke="#ef4444"
          strokeWidth={strokeWidth * 0.3}
          opacity={0.3}
        />
        <path
          d={describeArc(startAngle - 90, startAngle - 36)}
          fill="none"
          stroke="#eab308"
          strokeWidth={strokeWidth * 0.3}
          opacity={0.3}
        />
        <path
          d={describeArc(startAngle - 36, endAngle)}
          fill="none"
          stroke="#22c55e"
          strokeWidth={strokeWidth * 0.3}
          opacity={0.3}
        />

        {clampedValue >= 0.8 && (
          <path
            d={describeArc(valueAngle, endAngle)}
            fill="none"
            stroke="#22c55e"
            strokeWidth={strokeWidth}
            strokeLinecap="round"
          />
        )}
        {clampedValue >= 0.5 && clampedValue < 0.8 && (
          <path
            d={describeArc(valueAngle, endAngle)}
            fill="none"
            stroke="#eab308"
            strokeWidth={strokeWidth}
            strokeLinecap="round"
          />
        )}
        {clampedValue < 0.5 && (
          <path
            d={describeArc(valueAngle, endAngle)}
            fill="none"
            stroke="#ef4444"
            strokeWidth={strokeWidth}
            strokeLinecap="round"
          />
        )}

        {ticks.map(({ t, inner, outer }) => (
          <g key={t}>
            <line
              x1={inner.x}
              y1={inner.y}
              x2={outer.x}
              y2={outer.y}
              stroke="#9ca3af"
              strokeWidth={1}
            />
          </g>
        ))}

        <path
          d={needlePath}
          fill={isLow ? '#ef4444' : '#374151'}
          style={{ transform: `rotate(${valueAngle - startAngle}deg)`, transformOrigin: `${cx}px ${cy}px` }}
        />
        <circle
          cx={cx}
          cy={cy}
          r={strokeWidth * 0.4}
          fill={isLow ? '#ef4444' : '#374151'}
        />
        <text
          x={cx}
          y={cy + r * 0.5}
          textAnchor="middle"
          className={`font-mono text-sm font-bold ${isLow ? 'fill-[#ef4444]' : 'fill-gray-700'}`}
          style={{ fontFamily: "'JetBrains Mono', monospace" }}
        >
          {clampedValue.toFixed(2)}
        </text>
      </svg>

      {isLow && (
        <div className="font-mono text-[8px] text-[#9f1239] animate-pulse uppercase tracking-widest">
          低置信，建议查看蒙特卡洛
        </div>
      )}
    </div>
  )
}
