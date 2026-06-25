type FlowStep = {
  key: 'analysis' | 'simulation' | 'evolution'
  title: string
  detail: string
}

const FLOW_STEPS: FlowStep[] = [
  { key: 'analysis', title: '分析', detail: '材料定界 / B1-B6' },
  { key: 'simulation', title: '模拟', detail: 'E/P/R/tau 硬算' },
  { key: 'evolution', title: '演化', detail: '后继路径 / 分布' },
]

export function PrincipleFlow({
  active,
  compact = false,
}: {
  active?: FlowStep['key']
  compact?: boolean
}) {
  return (
    <div className={[
      'rounded-md border border-[#524639]/10 bg-white/45',
      compact ? 'px-3 py-2' : 'px-4 py-3',
    ].join(' ')}>
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div className="panel-title">原理链路</div>
        <div className="flex flex-wrap items-center gap-1.5">
          {FLOW_STEPS.map((step, index) => {
            const isActive = active === step.key
            return (
              <div key={step.key} className="flex items-center gap-1.5">
                <div
                  className={[
                    'rounded-md border px-2 py-1 transition-colors',
                    isActive
                      ? 'border-[#9f1239]/35 bg-[#9f1239]/10 text-[#9f1239]'
                      : 'border-[#524639]/10 bg-white/40 text-[#4f5d6a]',
                  ].join(' ')}
                >
                  <div className="text-[11px] font-bold leading-none">{step.title}</div>
                  {!compact && (
                    <div className="mt-1 font-mono text-[8px] leading-none opacity-70">{step.detail}</div>
                  )}
                </div>
                {index < FLOW_STEPS.length - 1 && (
                  <span className="font-mono text-[10px] text-[#8a8177]">-&gt;</span>
                )}
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
