import { useEffect, useMemo, useRef, useState } from 'react'
import { useStore, type FSMAnalysis, type PhysicsSnapshot } from '../store/useStore'
import { eventLabel } from '../utils/physicsLabels'
import { formatBits } from '../utils/bitOrder'
import { HexagramName } from './HexagramTextModal'
import { PrincipleFlow } from './PrincipleFlow'

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
  if (!fsmData && !snapshot) {
    const level = confidenceLevel(undefined)
    return {
      title: '待判断',
      current: '输入材料后，系统会先识别内外系统与 B1-B6，再生成物理初值并给出行动建议。',
      conflict: '等待识别关键矛盾。',
      risk: '尚未形成风险判断。需要先完成语义分析和物理模拟。',
      action: '先输入一个具体事件、困局、项目、关系或市场状态。',
      next: '后继：等待模拟结果',
      confidence: undefined,
      level,
    }
  }

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
      ? `主后继：${formatBits(snapshot.selected_next_bits, snapshot.display_selected_next_bits)}${snapshot.route.path_name ? `（${snapshot.route.path_name}）` : ''}`
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
  const summaryHexName = physicsSnapshot?.hexagram ?? fsmData?.target_hexagram ?? null

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
    <div className="absolute left-4 right-4 top-[44vh] bottom-4 pointer-events-none overflow-y-auto pr-1 md:top-24 md:bottom-6 lg:left-6 lg:right-6 lg:overflow-visible">
      <div className="flex min-h-full flex-col gap-3 pointer-events-auto lg:min-h-0 lg:flex-row lg:items-start lg:justify-between lg:pointer-events-none">
        <section className="glass-panel pointer-events-auto p-4 lg:max-h-[calc(100vh-128px)] lg:w-[390px] lg:overflow-y-auto xl:w-[420px] 2xl:w-[440px]">
          <div className="panel-title">实用判断</div>
          <div className="mt-3 text-2xl font-black text-[#26323f] xl:text-3xl">
            {summaryHexName ? (
              <HexagramName name={summaryHexName}>{summary.title}</HexagramName>
            ) : (
              summary.title
            )}
          </div>
          <div className="mt-3 text-sm leading-relaxed text-[#4f5d6a]">{summary.current}</div>

          <div className="mt-4">
            <PrincipleFlow compact />
          </div>

          <form onSubmit={handleSubmit} className="mt-5 rounded-lg border border-[#524639]/10 bg-white/55 p-2">
            <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:gap-3 lg:flex-col lg:items-stretch xl:flex-row xl:items-center">
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

          <div className="mt-5 grid grid-cols-1 gap-3 sm:grid-cols-2">
            <PracticalCard title="关键矛盾" body={summary.conflict} />
            <PracticalCard title="下一步风险" body={summary.risk} />
            <PracticalCard title="建议动作" body={summary.action} className="sm:col-span-2" />
          </div>
        </section>

        <aside className="pointer-events-auto flex flex-col gap-3 lg:max-h-[calc(100vh-128px)] lg:w-[390px] lg:overflow-y-auto xl:w-[420px] 2xl:w-[440px]">
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
                    {item.hexagram ? (
                      <HexagramName name={item.hexagram} className="font-mono text-[9px] text-[#4f5d6a]">
                        {item.hexagram}
                      </HexagramName>
                    ) : (
                      <span className="font-mono text-[9px] text-[#4f5d6a]">{formatBits(item.bits, item.display_bits)}</span>
                    )}
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
              <ExpertShortcut label="分析" sub="六层依据" onClick={() => openExpert('analysis')} />
              <ExpertShortcut label="模拟" sub="物理参数" onClick={() => openExpert('simulation')} />
              <ExpertShortcut label="演化" sub="后继分布" onClick={() => openExpert('evolution')} />
            </div>
          </section>
        </aside>
      </div>
    </div>
  )
}

function ExpertShortcut({ label, sub, onClick }: { label: string; sub: string; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className="rounded-md border border-[#524639]/10 bg-white/50 px-3 py-2 text-xs font-bold text-[#26323f] transition hover:bg-white/75"
    >
      <span className="block leading-none">{label}</span>
      <span className="mt-1 block font-mono text-[8px] font-normal leading-none text-[#6b6259]">{sub}</span>
    </button>
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
