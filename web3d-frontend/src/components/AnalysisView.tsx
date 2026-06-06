import { useEffect, useMemo, useState } from 'react'
import { useStore, type SimulateFlip } from '../store/useStore'

const DISPLAY_BITS = [6, 5, 4, 3, 2, 1]

const BIT_NAMES: Record<number, string> = {
  6: '宏观天花板',
  5: '运行规则',
  4: '接口层',
  3: '核心意志',
  2: '传导网络',
  1: '物理底座',
}

function safeText(value: string | null | undefined, fallback = '待分析') {
  return value && value.trim() ? value : fallback
}

function QueryInput() {
  const [input, setInput] = useState('')
  const isLoading = useStore((s) => s.isLoading)
  const inferError = useStore((s) => s.inferError)
  const fsmData = useStore((s) => s.fsmData)
  const fetchInfer = useStore((s) => s.fetchInfer)
  const setQuery = useStore((s) => s.setQuery)

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault()
    if (!input.trim() || isLoading) return
    setQuery(input)
    await fetchInfer(input)
  }

  return (
    <div className="absolute bottom-6 left-1/2 -translate-x-1/2 pointer-events-auto w-[720px] max-w-[94vw]">
      <form onSubmit={handleSubmit} className="glass-panel p-2">
        <div className="flex items-center gap-3">
          <span className="font-mono text-[12px] text-[#9f1239] shrink-0">&gt;</span>
          <input
            type="text"
            value={input}
            onChange={(event) => setInput(event.target.value)}
            placeholder={fsmData ? '继续输入历史事件、现实困局或推演材料' : '输入历史事件 / 现实困局 / 博弈场景'}
            disabled={isLoading}
            className="flex-1 bg-transparent px-1 py-2 text-sm text-[#26323f] placeholder:text-[#8a8177] outline-none disabled:opacity-40"
          />
          {isLoading && (
            <div className="flex gap-1 items-center shrink-0">
              <span className="h-1.5 w-1.5 rounded-full bg-[#9f1239]/70 animate-bounce [animation-delay:0ms]" />
              <span className="h-1.5 w-1.5 rounded-full bg-[#9f1239]/70 animate-bounce [animation-delay:150ms]" />
              <span className="h-1.5 w-1.5 rounded-full bg-[#9f1239]/70 animate-bounce [animation-delay:300ms]" />
            </div>
          )}
          <button
            type="submit"
            disabled={isLoading || !input.trim()}
            className="action-button shrink-0 px-4 py-2 font-mono text-[10px] tracking-[0.16em]"
          >
            {isLoading ? '分析中' : '开始分析'}
          </button>
        </div>
        {inferError && (
          <div className="mt-2 rounded-md border border-[#9f1239]/20 bg-[#9f1239]/5 px-3 py-2 text-[12px] text-[#9f1239]">
            分析请求失败：{inferError}
          </div>
        )}
      </form>
    </div>
  )
}

function ResultsPanel() {
  const fsmData = useStore((s) => s.fsmData)
  const deterministic = useStore((s) => s.deterministic)
  const retrievalResults = useStore((s) => s.retrievalResults)
  const simulateFlips = useStore((s) => s.simulateFlips)
  const physicsSeed = useStore((s) => s.physicsSeed)
  const simulateFlip = useStore((s) => s.simulateFlip)
  const applyPhysicsSeed = useStore((s) => s.applyPhysicsSeed)
  const setViewMode = useStore((s) => s.setViewMode)

  const bits = useMemo(() => {
    if (!fsmData) return ''
    const nextBits = `${fsmData.inner_bits}${fsmData.outer_bits}`
    return /^[01]{6}$/.test(nextBits) ? nextBits : '000000'
  }, [fsmData])

  useEffect(() => {
    if (!bits) return
    void simulateFlip(bits)
  }, [bits, simulateFlip])

  if (!fsmData) {
    return (
      <div className="absolute top-24 left-1/2 -translate-x-1/2 pointer-events-auto w-[760px] max-w-[94vw]">
        <div className="glass-panel px-6 py-5 text-center">
          <div className="text-base font-bold text-[#26323f]">从材料进入六层状态机</div>
          <div className="mt-2 text-sm leading-relaxed text-[#6b6259]">
            输入一个历史事件、现实系统或博弈困局，系统会先抽取内外系统与 B1-B6 状态，再生成可带入模拟页的原始物理输入。
          </div>
        </div>
      </div>
    )
  }

  const sendBitsToSimulation = (nextBits = bits) => {
    applyPhysicsSeed(physicsSeed, nextBits)
    setViewMode('simulation')
  }

  const handleFlipSelect = (flip: SimulateFlip) => {
    sendBitsToSimulation(flip.new_bits)
  }

  return (
    <div className="absolute top-24 bottom-28 left-1/2 -translate-x-1/2 pointer-events-auto w-[940px] max-w-[94vw] overflow-y-auto pr-1">
      <div className="flex flex-col gap-3">
        <section className="glass-panel p-5">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <div className="panel-title">语义分析层</div>
              <div className="mt-2 text-2xl font-black text-[#26323f]">
                {safeText(fsmData.target_hexagram, deterministic?.current_node?.name ?? '未知态')}
              </div>
              <div className="mt-1 max-w-[560px] text-sm leading-relaxed text-[#6b6259]">
                {safeText(fsmData.hexagram_reason, '等待模型返回目标卦理由。')}
              </div>
            </div>
            <button
              onClick={() => sendBitsToSimulation()}
              className="rounded-md border border-[#9f1239]/40 px-4 py-2 font-mono text-[10px] tracking-[0.14em] text-[#9f1239] transition hover:bg-[#9f1239]/10"
            >
              带入模拟
            </button>
          </div>

          <div className="mt-5">
            <BitStrip bits={bits} activeBit={fsmData.energy_focus.focus_bit} />
          </div>

          <div className="mt-4 flex flex-wrap items-center justify-center gap-x-4 gap-y-2 rounded-md border border-[#524639]/10 bg-white/50 px-3 py-2 font-mono text-[10px] text-[#6b6259]">
            <span>
              物理初值：
              <b className={physicsSeed ? 'text-[#0f766e]' : 'text-[#9f1239]'}>
                {physicsSeed ? '已由分析材料生成' : '未生成，仅同步 bit'}
              </b>
            </span>
            {physicsSeed && (
              <>
                <span>E {physicsSeed.E.map((value) => value.toFixed(2)).join('/')}</span>
                <span>P {physicsSeed.P.map((value) => value.toFixed(2)).join('/')}</span>
              </>
            )}
          </div>
        </section>

        <section className="grid grid-cols-1 gap-3 md:grid-cols-2">
          <InfoBlock title="内系统" body={safeText(fsmData.inner_system, '未识别内系统')} />
          <InfoBlock title="外系统" body={safeText(fsmData.outer_system, '未识别外系统')} />
        </section>

        <section className="grid grid-cols-1 gap-3 md:grid-cols-2">
          <InfoBlock
            title={`执行焦点 B${fsmData.energy_focus.focus_bit || '-'}`}
            body={safeText(fsmData.energy_focus.focus_description, '暂无焦点说明')}
          />
          <InfoBlock
            title={`应力状态 / ${safeText(fsmData.stress_analysis.stress_type, '稳定')}`}
            body={safeText(fsmData.stress_analysis.analysis, '暂无应力说明')}
          />
        </section>

        <section className="glass-panel p-4">
          <div className="panel-title mb-3">六层赋值依据</div>
          {fsmData.bit_analysis.length > 0 ? (
            <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
              {fsmData.bit_analysis.map((item) => (
                <div key={item.bit_position} className="rounded-md border border-[#524639]/10 bg-white/50 p-3">
                  <div className="mb-1 flex items-center justify-between gap-2">
                    <span className="font-mono text-[10px] font-bold text-[#26323f]">
                      B{item.bit_position} = {item.value}
                    </span>
                    <span className="text-[11px] text-[#8a8177]">{BIT_NAMES[item.bit_position]}</span>
                  </div>
                  <div className="text-xs leading-relaxed text-[#4f5d6a]">
                    {item.description}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-xs text-[#6b6259]">本次未返回逐层依据，可先使用硬算结果进入模拟。</div>
          )}
        </section>

        <section className="grid grid-cols-1 gap-3 md:grid-cols-3">
          <InfoBlock title="推演策略" body={safeText(fsmData.mutation_suggestion, '暂无策略')} className="md:col-span-2" />
          <InfoBlock title="目标理由" body={safeText(fsmData.hexagram_reason, '暂无理由')} />
        </section>

        {simulateFlips.length > 0 && (
          <section className="glass-panel p-4">
            <div className="panel-title mb-3">翻转预览</div>
            <div className="flex flex-wrap gap-2">
              {simulateFlips.map((flip) => (
                <button
                  key={flip.bit}
                  onClick={() => handleFlipSelect(flip)}
                  className="min-w-[72px] rounded-md border border-[#524639]/15 bg-white/50 px-3 py-2 text-center transition hover:border-[#9f1239]/50 hover:bg-[#9f1239]/10"
                >
                  <span className="block font-mono text-[8px] text-[#8a8177]">B{flip.bit}</span>
                  <span className="block text-base font-bold text-[#26323f]">{flip.hexagram}</span>
                  <span className="block font-mono text-[8px] text-[#8a8177]">{flip.new_bits}</span>
                </button>
              ))}
            </div>
          </section>
        )}

        {deterministic && (
          <section className="glass-panel grid grid-cols-2 gap-2 p-4 text-center md:grid-cols-4">
            <Metric label="路径" value={`${deterministic.evolution_path}`} />
            <Metric label="动爻" value={`B${deterministic.max_stress_bit}`} />
            <Metric label="应力" value={deterministic.stress_type} />
            <Metric label="熵值" value={deterministic.current_node?.entropy_S?.toFixed(3) ?? '-'} />
          </section>
        )}

        {retrievalResults.length > 0 && (
          <section className="glass-panel p-4">
            <div className="panel-title mb-3">RAG 检索</div>
            <div className="flex flex-col gap-2">
              {retrievalResults.slice(0, 3).map((item, index) => (
                <div key={`${item.hexagram_name}-${index}`} className="text-xs leading-relaxed text-[#4f5d6a]">
                  <span className="font-mono text-[10px] text-[#8a8177]">
                    [{item.hexagram_name ?? '未知'} / {item.text_type ?? '文本'}]
                  </span>
                  {' '}
                  {item.context ?? item.content ?? '无内容'}
                </div>
              ))}
            </div>
          </section>
        )}
      </div>
    </div>
  )
}

function BitStrip({ bits, activeBit }: { bits: string; activeBit: number }) {
  return (
    <div className="flex flex-wrap items-center justify-center gap-2">
      {DISPLAY_BITS.map((bitNum) => {
        const value = bits[bitNum - 1] ?? '0'
        const active = activeBit === bitNum
        return (
          <div
            key={bitNum}
            className={[
              'flex h-14 w-14 flex-col items-center justify-center rounded-md border-2 font-mono font-bold transition-all',
              active ? 'border-[#9f1239] bg-[#9f1239]/10 text-[#9f1239] shadow-sm' : 'border-[#524639]/15 bg-white/50',
              value === '1' ? 'text-[#26323f]' : 'text-[#8a8177]',
            ].join(' ')}
          >
            <span className="text-[8px] leading-none opacity-65">B{bitNum}</span>
            <span className="mt-1 text-xl leading-none">{value}</span>
          </div>
        )
      })}
    </div>
  )
}

function InfoBlock({ title, body, className = '' }: { title: string; body: string; className?: string }) {
  return (
    <div className={`glass-panel p-4 ${className}`}>
      <div className="panel-title mb-2">{title}</div>
      <div className="text-sm leading-relaxed text-[#4f5d6a]">
        {body}
      </div>
    </div>
  )
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-[#524639]/10 bg-white/40 px-3 py-2">
      <div className="font-mono text-[8px] text-[#8a8177]">{label}</div>
      <div className="mt-1 font-mono text-[12px] font-bold text-[#26323f]">{value}</div>
    </div>
  )
}

export function AnalysisView() {
  return (
    <>
      <ResultsPanel />
      <QueryInput />
    </>
  )
}
