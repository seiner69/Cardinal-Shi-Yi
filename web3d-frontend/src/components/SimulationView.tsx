import { useStore } from '../store/useStore'
import { LayerInputCard } from './LayerInputCard'
import { BitProgressBar } from './BitProgressBar'
import { eventLabel, ttlLabel } from '../utils/physicsLabels'

const DISPLAY_BITS = [6, 5, 4, 3, 2, 1]

export function SimulationView() {
  const physicsInputs = useStore((s) => s.physicsInputs)
  const physicsSnapshot = useStore((s) => s.physicsSnapshot)
  const isSimulating = useStore((s) => s.isSimulating)
  const runPhysics = useStore((s) => s.runPhysics)
  const updatePhysicsBit = useStore((s) => s.updatePhysicsBit)
  const updatePhysicsLayer = useStore((s) => s.updatePhysicsLayer)
  const updatePhysicsUncertainty = useStore((s) => s.updatePhysicsUncertainty)
  const updatePhysicsRoute = useStore((s) => s.updatePhysicsRoute)

  const bits = physicsSnapshot?.bits ?? physicsInputs.bits
  const activeBit = physicsSnapshot?.focus_bit ?? null
  const nextBits = physicsSnapshot?.selected_next_bits ?? null

  return (
    <div className="absolute inset-0 pointer-events-none">
      <div className="absolute top-[92px] left-1/2 -translate-x-1/2 pointer-events-auto w-[780px] max-w-[94vw]">
        <div className="glass-panel px-4 py-3">
          <div className="flex flex-col items-center gap-3">
            <div className="flex flex-col items-center gap-2 sm:flex-row sm:gap-3">
              <BitStrip bits={bits} activeBit={activeBit} />
              <span className="font-mono text-sm text-[#8a8177] sm:rotate-0">-&gt;</span>
              <BitStrip bits={nextBits ?? bits} activeBit={activeBit} muted={!nextBits} />
            </div>

            {physicsSnapshot ? (
              <div className="flex flex-wrap items-center justify-center gap-x-5 gap-y-2 font-mono text-[10px] text-[#6b6259]">
                <span>焦点 <b className="text-[#9f1239]">B{physicsSnapshot.focus_bit}</b></span>
                <span>事件 <b className="text-[#26323f]">{eventLabel(physicsSnapshot.event)}</b></span>
                <span>TTL <b className="text-[#26323f]">{ttlLabel(physicsSnapshot.ttl)}</b></span>
                <span>路径 <b className="text-[#26323f]">{physicsSnapshot.route.path_number}</b></span>
                <span>后继 <b className="text-[#26323f]">{physicsSnapshot.selected_next_bits ?? '多后继'}</b></span>
                <span>置信 <b className="text-[#26323f]">{physicsSnapshot.confidence.conf_input.toFixed(2)}</b></span>
              </div>
            ) : (
              <div className="font-mono text-[10px] text-[#8a8177]">
                调整六层参数后执行模拟，系统会返回硬中断、路径路由与后继分布。
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="absolute top-[260px] bottom-4 left-4 right-4 pointer-events-none overflow-y-auto md:top-[205px] md:overflow-visible">
        <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
          <div className="pointer-events-auto w-full md:w-[380px] md:max-h-[calc(100vh-220px)] md:overflow-y-auto">
            <div className="glass-panel p-3">
              <div className="mb-3 flex items-center justify-between gap-3">
                <div>
                  <div className="panel-title">原始物理输入</div>
                  <div className="mt-1 text-[11px] text-[#8a8177]">B1-B6 内部码，界面按 B6 到 B1 展示</div>
                </div>
                <button
                  onClick={() => void runPhysics()}
                  disabled={isSimulating}
                  className="action-button px-3 py-2 font-mono text-[9px] tracking-[0.16em]"
                >
                  {isSimulating ? '计算中' : '执行模拟'}
                </button>
              </div>

              <div className="flex flex-col gap-2">
                {DISPLAY_BITS.map((bitIndex) => {
                  const idx = bitIndex - 1
                  const layer = physicsSnapshot?.layers.find(item => item.bit === bitIndex)
                  return (
                    <LayerInputCard
                      key={bitIndex}
                      bitIndex={bitIndex}
                      B={Number(physicsInputs.bits[idx] ?? '0')}
                      E={physicsInputs.E[idx]}
                      P={physicsInputs.P[idx]}
                      R={physicsInputs.R[idx]}
                      R_base={physicsInputs.R_base[idx]}
                      tau={physicsInputs.tau[idx]}
                      C={physicsInputs.C[idx]}
                      layer={layer}
                      isActive={activeBit === bitIndex}
                      onToggle={(targetBit, value) => updatePhysicsBit(targetBit, value)}
                      onParamChange={(targetBit, key, value) => updatePhysicsLayer(targetBit, { [key]: value })}
                    />
                  )
                })}
              </div>
            </div>
          </div>

          <div className="pointer-events-auto w-full md:w-[380px] md:max-h-[calc(100vh-220px)] md:overflow-y-auto">
            <div className="glass-panel p-3">
              <div className="mb-3">
                <div className="panel-title">路径上下文</div>
                <div className="mt-1 text-[11px] text-[#8a8177]">外部注能、停留时间与不确定性会影响路由判断</div>
              </div>

              <div className="flex flex-col gap-3">
                <NumberField
                  label="外部注能"
                  value={physicsInputs.delta_E_ext}
                  onChange={(value) => updatePhysicsRoute({ delta_E_ext: value })}
                />
                <NumberField
                  label="停留时间"
                  value={physicsInputs.time_in_state}
                  onChange={(value) => updatePhysicsRoute({ time_in_state: Math.max(0, Math.round(value)) })}
                />
                <NumberField
                  label="MC 样本数"
                  value={physicsInputs.monte_carlo_N}
                  onChange={(value) => updatePhysicsRoute({ monte_carlo_N: Math.max(1, Math.min(10000, Math.round(value))) })}
                />
                <label className="flex items-center justify-between rounded-md border border-[#524639]/10 bg-white/50 px-3 py-2 font-mono text-[10px] text-[#6b6259]">
                  死锁
                  <input
                    type="checkbox"
                    checked={physicsInputs.deadlock_flag}
                    onChange={(event) => updatePhysicsRoute({ deadlock_flag: event.target.checked })}
                    className="h-4 w-4 accent-[#9f1239]"
                  />
                </label>
                <div className="grid grid-cols-2 gap-2">
                  {[
                    ['能量误差', 'U_E', physicsInputs.U.U_E],
                    ['压力误差', 'U_P', physicsInputs.U.U_P],
                    ['耗散误差', 'U_R', physicsInputs.U.U_R],
                    ['阈值误差', 'U_tau', physicsInputs.U.U_tau],
                  ].map(([label, key, value]) => (
                    <NumberField
                      key={key}
                      label={String(label)}
                      value={Number(value)}
                      onChange={(nextValue) => {
                        updatePhysicsUncertainty({ [key as 'U_E' | 'U_P' | 'U_R' | 'U_tau']: Math.max(0, Math.min(1, nextValue)) })
                      }}
                    />
                  ))}
                </div>
              </div>

              {physicsSnapshot && (
                <div className="mt-4 border-t border-[#524639]/10 pt-3">
                  <div className="panel-title mb-2">层级活性</div>
                  <div className="flex flex-col gap-1">
                    {DISPLAY_BITS.map((bitIndex) => {
                      const idx = bitIndex - 1
                      return (
                        <BitProgressBar
                          key={bitIndex}
                          bitIndex={bitIndex}
                          B={Number(physicsSnapshot.bits[idx] ?? '0')}
                          E={physicsInputs.E[idx]}
                          E_initial={physicsInputs.E_initial[idx]}
                          P={physicsInputs.P[idx]}
                          tau={physicsInputs.tau[idx]}
                          isActive={activeBit === bitIndex}
                        />
                      )
                    })}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function BitStrip({ bits, activeBit, muted = false }: { bits: string; activeBit: number | null; muted?: boolean }) {
  return (
    <div className="flex gap-1.5">
      {DISPLAY_BITS.map((bitNum) => {
        const value = bits[bitNum - 1] ?? '0'
        const active = activeBit === bitNum
        return (
          <div
            key={bitNum}
            className={[
              'flex h-8 w-8 flex-col items-center justify-center rounded-md border-2 font-mono font-bold transition-all sm:h-10 sm:w-10',
              active ? 'border-[#9f1239] bg-[#9f1239]/10 text-[#9f1239]' : 'border-[#524639]/15 bg-white/50',
              value === '1' && !muted ? 'text-[#26323f]' : 'text-[#8a8177]',
              muted ? 'opacity-55' : '',
            ].join(' ')}
          >
            <span className="text-[7px] leading-none opacity-65">B{bitNum}</span>
            <span className="text-sm leading-none sm:text-base">{value}</span>
          </div>
        )
      })}
    </div>
  )
}

function NumberField({ label, value, onChange }: { label: string; value: number; onChange: (value: number) => void }) {
  return (
    <label className="flex items-center justify-between gap-3 rounded-md border border-[#524639]/10 bg-white/50 px-3 py-2">
      <span className="text-[11px] text-[#6b6259]">{label}</span>
      <input
        type="number"
        step="0.01"
        value={Number.isFinite(value) ? value : 0}
        onChange={(event) => onChange(Number(event.target.value))}
        className="field-input w-24 px-2 py-1 text-right font-mono text-[10px]"
      />
    </label>
  )
}
