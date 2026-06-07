import { useStore } from '../store/useStore'

const EXPERT_TABS = [
  { key: 'analysis' as const, label: '分析', sub: '语义入卦' },
  { key: 'simulation' as const, label: '模拟', sub: '物理演算' },
  { key: 'evolution' as const, label: '演化', sub: '后继分布' },
]

export function TopNav() {
  const { interfaceMode, viewMode, setInterfaceMode, setViewMode } = useStore()

  return (
    <div className="absolute top-4 left-1/2 -translate-x-1/2 pointer-events-auto">
      <div className="glass-panel flex flex-col items-center gap-1 p-1 sm:flex-row">
        <div className="flex items-center gap-1">
          {[
            { key: 'practical' as const, label: '实用', sub: '判断建议' },
            { key: 'expert' as const, label: '专家', sub: '参数调试' },
          ].map((tab) => {
            const active = interfaceMode === tab.key
            return (
              <button
                key={tab.key}
                onClick={() => setInterfaceMode(tab.key)}
                className={[
                  'min-w-[78px] rounded-md px-4 py-2 transition-all cursor-pointer',
                  active ? 'bg-[#26323f] text-white shadow-sm' : 'text-[#625950] hover:bg-white/60',
                ].join(' ')}
              >
                <span className="block text-[13px] font-bold leading-none">{tab.label}</span>
                <span className={['mt-1 block font-mono text-[8px] leading-none', active ? 'text-white/70' : 'text-[#625950]/60'].join(' ')}>
                  {tab.sub}
                </span>
              </button>
            )
          })}
        </div>

        {interfaceMode === 'expert' && (
          <div className="flex items-center gap-1 border-t border-[#524639]/10 pt-1 sm:border-l sm:border-t-0 sm:pl-1 sm:pt-0">
            {EXPERT_TABS.map((tab) => {
              const active = viewMode === tab.key
              return (
                <button
                  key={tab.key}
                  onClick={() => setViewMode(tab.key)}
                  className={[
                    'min-w-[74px] rounded-md px-3 py-2 transition-all cursor-pointer',
                    active ? 'bg-[#9f1239] text-white shadow-sm' : 'text-[#625950] hover:bg-white/60',
                  ].join(' ')}
                >
                  <span className="block text-[12px] font-bold leading-none">{tab.label}</span>
                  <span className={['mt-1 block font-mono text-[7px] leading-none', active ? 'text-white/70' : 'text-[#625950]/60'].join(' ')}>
                    {tab.sub}
                  </span>
                </button>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
