import type { ReactNode } from 'react'
import { useStore } from '../store/useStore'

export function HexagramName({
  name,
  className = '',
  children,
}: {
  name: string | null | undefined
  className?: string
  children?: ReactNode
}) {
  const openHexagramText = useStore((s) => s.openHexagramText)
  const cleanName = name?.trim()

  if (!cleanName) return <>{children ?? name ?? ''}</>

  return (
    <button
      type="button"
      onClick={() => void openHexagramText(cleanName)}
      className={[
        'cursor-pointer rounded px-1 text-left transition hover:bg-[#9f1239]/10 hover:text-[#9f1239] focus:outline-none focus:ring-2 focus:ring-[#9f1239]/20',
        className,
      ].join(' ')}
      title={`查看${cleanName}卦卦辞与六爻`}
    >
      {children ?? cleanName}
    </button>
  )
}

export function HexagramTextModal() {
  const selectedHexagramText = useStore((s) => s.selectedHexagramText)
  const hexagramTextError = useStore((s) => s.hexagramTextError)
  const isHexagramTextLoading = useStore((s) => s.isHexagramTextLoading)
  const closeHexagramText = useStore((s) => s.closeHexagramText)

  if (!selectedHexagramText && !hexagramTextError && !isHexagramTextLoading) return null

  return (
    <div className="absolute inset-0 z-50 pointer-events-none">
      <div className="absolute inset-0 bg-[#1f2933]/12 pointer-events-auto" onClick={closeHexagramText} />
      <div className="absolute right-4 top-24 bottom-6 pointer-events-auto w-[420px] max-w-[calc(100vw-32px)]">
        <div className="glass-panel flex h-full flex-col overflow-hidden">
          <div className="flex items-start justify-between gap-4 border-b border-[#524639]/10 px-5 py-4">
            <div>
              <div className="panel-title">周易原文</div>
              <div className="mt-2 flex items-baseline gap-3">
                <span className="text-3xl font-black text-[#26323f]">
                  {selectedHexagramText?.symbol}
                </span>
                <span className="text-2xl font-black text-[#26323f]">
                  {selectedHexagramText ? `${selectedHexagramText.name}卦` : '加载中'}
                </span>
                {selectedHexagramText?.index ? (
                  <span className="font-mono text-[10px] text-[#8a8177]">#{selectedHexagramText.index}</span>
                ) : null}
              </div>
            </div>
            <button
              type="button"
              onClick={closeHexagramText}
              className="rounded-md border border-[#524639]/10 bg-white/50 px-3 py-1.5 font-mono text-[11px] text-[#6b6259] transition hover:bg-white/80"
            >
              关闭
            </button>
          </div>

          <div className="flex-1 overflow-y-auto px-5 py-4">
            {isHexagramTextLoading && (
              <div className="font-mono text-[11px] text-[#8a8177]">正在加载卦辞...</div>
            )}

            {hexagramTextError && (
              <div className="rounded-md border border-[#9f1239]/20 bg-[#9f1239]/5 px-3 py-2 text-sm text-[#9f1239]">
                {hexagramTextError}
              </div>
            )}

            {selectedHexagramText && (
              <div className="flex flex-col gap-4">
                <TextSection title="卦辞" body={selectedHexagramText.gua_ci} />

                <section>
                  <div className="panel-title mb-2">六爻爻辞</div>
                  <div className="flex flex-col gap-2">
                    {selectedHexagramText.yao.map((line) => (
                      <div key={`${line.position}-${line.text}`} className="rounded-md border border-[#524639]/10 bg-white/50 px-3 py-2">
                        <div className="font-mono text-[10px] font-bold text-[#9f1239]">{line.position}</div>
                        <div className="mt-1 text-sm leading-relaxed text-[#26323f]">{line.text}</div>
                      </div>
                    ))}
                  </div>
                </section>

                <TextSection title="彖传" body={selectedHexagramText.tuan} />
                <TextSection title="大象" body={selectedHexagramText.da_xiang} />
                {selectedHexagramText.wen_yan && <TextSection title="文言" body={selectedHexagramText.wen_yan} />}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

function TextSection({ title, body }: { title: string; body: string }) {
  if (!body) return null

  return (
    <section className="rounded-md border border-[#524639]/10 bg-white/45 px-3 py-3">
      <div className="panel-title mb-2">{title}</div>
      <div className="text-sm leading-relaxed text-[#26323f]">{body}</div>
    </section>
  )
}
