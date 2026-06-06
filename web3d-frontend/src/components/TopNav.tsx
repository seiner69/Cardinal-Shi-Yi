import { useStore } from '../store/useStore'

const TABS = [
  { key: 'analysis' as const, label: '分析', sub: '语义入卦' },
  { key: 'simulation' as const, label: '模拟', sub: '物理演算' },
  { key: 'evolution' as const, label: '演化', sub: '后继分布' },
]

export function TopNav() {
  const { viewMode, setViewMode } = useStore()

  return (
    <div className="absolute top-4 left-1/2 -translate-x-1/2 pointer-events-auto">
      <div className="glass-panel flex items-center gap-1 p-1">
        {TABS.map((tab) => {
          const active = viewMode === tab.key
          return (
            <button
              key={tab.key}
              onClick={() => setViewMode(tab.key)}
              className={[
                'min-w-[84px] rounded-md px-4 py-2 transition-all cursor-pointer',
                active ? 'bg-[#9f1239] text-white shadow-sm' : 'text-[#625950] hover:bg-white/60',
              ].join(' ')}
            >
              <span className="block text-[13px] font-bold leading-none">{tab.label}</span>
              <span
                className={[
                  'mt-1 block font-mono text-[8px] leading-none',
                  active ? 'text-white/70' : 'text-[#625950]/60',
                ].join(' ')}
              >
                {tab.sub}
              </span>
            </button>
          )
        })}
      </div>
    </div>
  )
}
