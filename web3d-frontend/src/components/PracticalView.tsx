import { useEffect, useMemo, useRef, useState } from 'react'
import { useStore, type FSMAnalysis, type PhysicsSnapshot } from '../store/useStore'
import { eventLabel } from '../utils/physicsLabels'

const BIT_LABELS: Record<number, string> = {
  6: '宏观环境',
  5: '规则秩序',
  4: '接口通道',
  3: '核心意志',
  2: '传导网络',
  1: '物质底座',
}

const EVENT_MEANING: Record<string, string> = {
  collapse: '原有支撑正在衰减，需要补能或收缩战线。',
  crush: '压力超过承载，短期内要先降压再行动。',
  explosion: '压抑能量正在外溢，适合疏导、开口或换通道。',
  stable: '结构暂时稳定，重点是维持节奏并观察下一层变化。',
}

const EVENT_ACTION: Record<string, string> = {
  collapse: '先补足关键资源，减少非必要消耗，把动作集中到一两个核心点。',
  crush: '先降低外部压力或重新划分边界，不宜继续硬推。',
  explosion: '给能量一个可控出口，优先处理接口、沟通、发布、转换路径。',
  stable: '维持当前结构，同时准备一套备选路径，避免稳定变成僵化。',
}

function safeText(value: string | null | undefined, fallback: string) {
  return value && value.trim() ? value : fallback
}

function confidenceLevel(value: number | undefined) {
  if (value === undefined) return { label: '待生成', tone: 'text-[#6b6259]', note: '输入材料后会生成可信度和分支判断。' }
  const conf = value ?? 0
  if (conf >= 0.82) return { label: '高', tone: 'text-[#0f766e]', note: '主路径较集中，可以把建议当作主要行动方向。' }
  if (conf >= 0.65) return { label: '中', tone: 'text-[#b45309]', note: '主路径可参考，但需要保留分支预案。' }
  return { label: '低', tone: 'text-[#9f1239]', note: '分支较多，建议查看专家模式里的蒙特卡洛分布。' }
}

function buildPracticalSummary(fsmData: FSMAnalysis | null, snapshot: PhysicsSnapshot | null) {
  const focusBit = snapshot?.focus_bit ?? fsmData?.energy_focus.focus_bit ?? 0
  const event = snapshot?.event ?? 'stable'
  const conf = snapshot?.confidence.conf_input
  const level = confidenceLevel(conf)
  const layerName = BIT_LABELS[focusBit] ?? '关键层'

  return {
    title: snapshot?.hexagram ?? safeText(fsmData?.target_hexagram, '待判断'),
    current: safeText(
      fsmData?.hexagram_reason,
      snapshot ? `${snapshot.hexagram} 对应当前系统的主要状态。` : '输入材料后，系统会给出当前局势判断。'
    ),
    conflict: safeText(
      fsmData?.energy_focus.focus_description,
      focusBit ? `当前最敏感的是 B${focusBit}：${layerName}。` : '等待识别关键矛盾。'
    ),
    risk: `${focusBit ? `B${focusBit} ${layerName}` : '系统'} 出现「${eventLabel(event)}」倾向。${EVENT_MEANING[event] ?? '需要结合分支结果继续判断。'}`,
    action: safeText(fsmData?.mutation_suggestion, EVENT_ACTION[event] ?? '先降低不确定性，再选择主路径推进。'),
    next: snapshot?.selected_next_bits
      ? `主后继：${snapshot.selected_next_bits}${snapshot.route.path_name ? `（${snapshot.route.path_name}）` : ''}`
      : '后继：等待模拟结果',
    confidence: conf,
    level,
  }
}

export function PracticalView() {
  const [input, setInput] = useState('')
  const simulatedKeyRef = useRef('')
  const {
    isLoading,
    inferError,
    fsmData,
    physicsSeed,
    physicsSnapshot,
    fetchInfer,
    setQuery,
    runPhysics,
    setInterfaceMode,
    setViewMode,
  } = useStore()

  const bits = useMemo(() => {
    if (!fsmData) return ''
    const nextBits = `${fsmData.inner_bits}${fsmData.outer_bits}`
    return /^[01]{6}$/.test(nextBits) ? nextBits : ''
  }, [fsmData])

  useEffect(() => {
    if (!physicsSeed || !bits) return
    const key = `${bits}:${physicsSeed.E.join(',')}:${physicsSeed.P.join(',')}`
    if (simulatedKeyRef.current === key) return
    simulatedKeyRef.current = key
    void runPhysics({ ...physicsSeed, bits })
  }, [bits, physicsSeed, runPhysics])

  const summary = buildPracticalSummary(fsmData, physicsSnapshot)

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault()
    if (!input.trim() || isLoading) return
    simulatedKeyRef.current = ''
    setQuery(input)
    await fetchInfer(input)
  }

  const openExpert = (mode: 'analysis' | 'simulation' | 'evolution') => {
    setInterfaceMode('expert')
    setViewMode(mode)
  }

  return (
    <div className="absolute top-24 bottom-6 left-1/2 w-[960px] max-w-[94vw] -translate-x-1/2 overflow-y-auto pointer-events-auto pr-1">
      <div className="grid grid-cols-1 gap-3 lg:grid-cols-[1.15fr_0.85fr]">
        <section className="glass-panel p-5">
          <div className="panel-title">实用判断</div>
          <div className="mt-3 text-3xl font-black text-[#26323f]">{summary.title}</div>
          <div className="mt-3 text-sm leading-relaxed text-[#4f5d6a]">{summary.current}</div>

          <form onSubmit={handleSubmit} className="mt-5 rounded-lg border border-[#524639]/10 bg-white/55 p-2">
            <div className="flex items-center gap-3">
              <span className="shrink-0 font-mono text-[12px] text-[#9f1239]">&gt;</span>
              <input
                value={input}
                onChange={(event) => setInput(event.target.value)}
                placeholder="输入一个事件、困局、项目、关系或市场状态"
                className="flex-1 bg-transparent px-1 py-2 text-sm text-[#26323f] placeholder:text-[#8a8177] outline-none"
              />
              <button
                type="submit"
                disabled={isLoading || !input.trim()}
                className="action-button shrink-0 px-4 py-2 font-mono text-[10px] tracking-[0.16em]"
              >
                {isLoading ? '判断中' : '生成判断'}
              </button>
            </div>
            {inferError && (
              <div className="mt-2 rounded-md border border-[#9f1239]/20 bg-[#9f1239]/5 px-3 py-2 text-xs text-[#9f1239]">
                分析请求失败：{inferError}
              </div>
            )}
          </form>

          <div className="mt-5 grid grid-cols-1 gap-3 md:grid-cols-2">
            <PracticalCard title="关键矛盾" body={summary.conflict} />
            <PracticalCard title="下一步风险" body={summary.risk} />
            <PracticalCard title="建议动作" body={summary.action} className="md:col-span-2" />
          </div>
        </section>

        <aside className="flex flex-col gap-3">
          <section className="glass-panel p-4">
            <div className="panel-title">结果可信度</div>
            <div className="mt-3 flex items-end justify-between gap-4">
              <div>
                <div className={`text-3xl font-black ${summary.level.tone}`}>{summary.level.label}</div>
                <div className="mt-1 font-mono text-[11px] text-[#6b6259]">
                  {summary.confidence === undefined ? '等待模拟' : summary.confidence.toFixed(2)}
                </div>
              </div>
              <div className="text-right text-xs leading-relaxed text-[#6b6259]">{summary.level.note}</div>
            </div>
          </section>

          <section className="glass-panel p-4">
            <div className="panel-title">后继方向</div>
            <div className="mt-3 rounded-md border border-[#524639]/10 bg-white/50 px-3 py-3 font-mono text-[12px] text-[#26323f]">
              {summary.next}
            </div>
            {physicsSnapshot?.monte_carlo?.length ? (
              <div className="mt-3 flex flex-col gap-2">
                {physicsSnapshot.monte_carlo.slice(0, 3).map((item) => (
                  <div key={item.bits} className="grid grid-cols-[64px_1fr_42px] items-center gap-2">
                    <span className="font-mono text-[9px] text-[#4f5d6a]">{item.hexagram || item.bits}</span>
                    <div className="h-2 overflow-hidden rounded bg-[#e6dfd4]/70">
                      <div className="h-full bg-[#0f766e]/70" style={{ width: `${Math.max(2, item.probability * 100)}%` }} />
                    </div>
                    <span className="text-right font-mono text-[8px] text-[#6b6259]">{(item.probability * 100).toFixed(0)}%</span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="mt-3 text-xs text-[#8a8177]">完成判断后会显示主要分支。</div>
            )}
          </section>

          <section className="glass-panel p-4">
            <div className="panel-title">打开专家层</div>
            <div className="mt-3 grid grid-cols-3 gap-2">
              <button onClick={() => openExpert('analysis')} className="rounded-md border border-[#524639]/10 bg-white/50 px-3 py-2 text-xs font-bold text-[#26323f] transition hover:bg-white/75">依据</button>
              <button onClick={() => openExpert('simulation')} className="rounded-md border border-[#524639]/10 bg-white/50 px-3 py-2 text-xs font-bold text-[#26323f] transition hover:bg-white/75">参数</button>
              <button onClick={() => openExpert('evolution')} className="rounded-md border border-[#524639]/10 bg-white/50 px-3 py-2 text-xs font-bold text-[#26323f] transition hover:bg-white/75">分布</button>
            </div>
          </section>
        </aside>
      </div>
    </div>
  )
}

function PracticalCard({ title, body, className = '' }: { title: string; body: string; className?: string }) {
  return (
    <div className={`rounded-lg border border-[#524639]/10 bg-white/50 p-4 ${className}`}>
      <div className="panel-title mb-2">{title}</div>
      <div className="text-sm leading-relaxed text-[#4f5d6a]">{body}</div>
    </div>
  )
}
