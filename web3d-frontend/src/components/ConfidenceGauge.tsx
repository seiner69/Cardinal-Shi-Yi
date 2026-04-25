interface ConfidenceGaugeProps {
  value: number   // 0-1
  size?: number
}

export function ConfidenceGauge({ value, size = 120 }: ConfidenceGaugeProps) {
  const clampedValue = Math.max(0, Math.min(1, value))
  const isLow = clampedValue < 0.8

  // SVG arc parameters
  const cx = size / 2
  const cy = size / 2
  const r = size * 0.4
  const strokeWidth = size * 0.08

  // Arc from 180° to 0° (semicircle, bottom-open)
  const startAngle = 180
  const endAngle = 0
  const totalRange = startAngle - endAngle // 180 degrees

  // Value mapped to angle
  const valueAngle = startAngle - clampedValue * totalRange

  // Compute SVG arc path
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

  // Needle
  const needleAngle = startAngle - clampedValue * totalRange
  const needleTip = polarToCartesian(needleAngle)
  const needleBase1 = polarToCartesian(needleAngle - 3)
  const needleBase2 = polarToCartesian(needleAngle + 3)
  const needlePath = `M ${needleTip.x} ${needleTip.y} L ${needleBase1.x} ${needleBase1.y} L ${needleBase2.x} ${needleBase2.y} Z`

  // Tick marks
  const ticks = [0, 0.2, 0.4, 0.6, 0.8, 1.0].map(t => {
    const angle = startAngle - t * totalRange
    const inner = polarToCartesian(angle)
    const outer = {
      x: cx + (r + strokeWidth * 0.8) * Math.cos((angle * Math.PI) / 180),
      y: cy - (r + strokeWidth * 0.8) * Math.sin((angle * Math.PI) / 180),
    }
    return { t, inner, outer, angle }
  })

  return (
    <div className="flex flex-col items-center gap-1">
      <div className="font-mono text-[8px] text-gray-400 uppercase tracking-widest">
        SYSTEM CONFIDENCE
      </div>

      <svg
        width={size}
        height={size * 0.65}
        viewBox={`0 0 ${size} ${size * 0.65}`}
        className={isLow ? 'animate-pulse' : ''}
      >
        {/* Background track */}
        <path
          d={describeArc(startAngle, endAngle)}
          fill="none"
          stroke="#e5e5e5"
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        />

        {/* Red zone (0-0.5) */}
        <path
          d={describeArc(startAngle, startAngle - 90)}
          fill="none"
          stroke="#ef4444"
          strokeWidth={strokeWidth * 0.3}
          opacity={0.3}
        />

        {/* Yellow zone (0.5-0.8) */}
        <path
          d={describeArc(startAngle - 90, startAngle - 36)}
          fill="none"
          stroke="#eab308"
          strokeWidth={strokeWidth * 0.3}
          opacity={0.3}
        />

        {/* Green zone (0.8-1.0) */}
        <path
          d={describeArc(startAngle - 36, endAngle)}
          fill="none"
          stroke="#22c55e"
          strokeWidth={strokeWidth * 0.3}
          opacity={0.3}
        />

        {/* Value arc — color based on value */}
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

        {/* Tick marks */}
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

        {/* Needle */}
        <path
          d={needlePath}
          fill={isLow ? '#ef4444' : '#374151'}
          transform={`rotate(0 ${cx} ${cy})`}
          style={{ transform: `rotate(${needleAngle - startAngle}deg)`, transformOrigin: `${cx}px ${cy}px` }}
        />

        {/* Center circle */}
        <circle
          cx={cx}
          cy={cy}
          r={strokeWidth * 0.4}
          fill={isLow ? '#ef4444' : '#374151'}
        />

        {/* Value text */}
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

      {/* Low confidence warning */}
      {isLow && (
        <div className="font-mono text-[8px] text-[#ef4444] animate-pulse uppercase tracking-widest">
          ⚠ LOW CONF — MONTE CARLO ADVISED
        </div>
      )}
    </div>
  )
}
