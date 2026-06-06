import { useStore } from '../store/useStore'
import { PhysicsResultPanel } from './PhysicsResultPanel'

export function EvolutionView() {
  const physicsSnapshot = useStore((s) => s.physicsSnapshot)

  return (
    <div className="absolute inset-0 pointer-events-none">
      <div className="absolute top-24 left-1/2 w-[920px] max-w-[94vw] -translate-x-1/2 pointer-events-auto">
        <div className="glass-panel px-5 py-4">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <div className="panel-title">演化结果</div>
              <div className="mt-2 text-2xl font-black text-[#26323f]">
                {physicsSnapshot ? `${physicsSnapshot.hexagram} / ${physicsSnapshot.bits}` : '等待一次物理模拟'}
              </div>
            </div>
            <div className="max-w-[480px] text-sm leading-relaxed text-[#6b6259]">
              {physicsSnapshot
                ? '这里展示真实 /api/physics 返回的后继、路径分支、置信度和采样分布。'
                : '先到“分析”生成物理初值，或到“模拟”手动录入六层参数并执行。'}
            </div>
          </div>
        </div>
      </div>

      <div className="absolute top-[190px] bottom-6 left-1/2 w-[920px] max-w-[94vw] -translate-x-1/2 pointer-events-auto overflow-y-auto pr-1">
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-3">
          <PhysicsResultPanel />
        </div>
      </div>
    </div>
  )
}
