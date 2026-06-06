import { useEffect, useMemo, useRef, useState } from 'react'

interface TypewriterLogProps {
  entries: string[]
}

interface Cursor {
  entry: number
  char: number
}

const SPEED_MS = 30

export function TypewriterLog({ entries }: TypewriterLogProps) {
  const [cursor, setCursor] = useState<Cursor>({ entry: 0, char: 0 })
  const bottomRef = useRef<HTMLDivElement>(null)
  const signature = useMemo(() => entries.join('\u001f'), [entries])

  useEffect(() => {
    const timeout = window.setTimeout(() => setCursor({ entry: 0, char: 0 }), 0)
    return () => window.clearTimeout(timeout)
  }, [signature])

  useEffect(() => {
    if (entries.length === 0 && (cursor.entry !== 0 || cursor.char !== 0)) {
      const timeout = window.setTimeout(() => setCursor({ entry: 0, char: 0 }), 0)
      return () => window.clearTimeout(timeout)
    }

    if (entries.length > 0 && cursor.entry > entries.length) {
      const timeout = window.setTimeout(() => setCursor({ entry: entries.length, char: 0 }), 0)
      return () => window.clearTimeout(timeout)
    }
  }, [cursor.char, cursor.entry, entries.length])

  useEffect(() => {
    if (entries.length === 0 || cursor.entry >= entries.length) return

    const timeout = window.setTimeout(() => {
      setCursor((prev) => {
        if (prev.entry >= entries.length) return { entry: entries.length, char: 0 }

        const current = entries[prev.entry] ?? ''
        if (prev.char < current.length) {
          return { entry: prev.entry, char: prev.char + 1 }
        }

        return { entry: prev.entry + 1, char: 0 }
      })
    }, SPEED_MS)

    return () => window.clearTimeout(timeout)
  }, [cursor.char, cursor.entry, entries])

  const completedEntries = useMemo(
    () => entries.slice(0, Math.min(cursor.entry, entries.length)),
    [cursor.entry, entries]
  )
  const currentText =
    cursor.entry < entries.length ? entries[cursor.entry].slice(0, cursor.char) : ''

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [completedEntries, currentText])

  return (
    <div className="flex max-h-36 flex-col gap-1 overflow-y-auto">
      {completedEntries.map((entry, index) => (
        <div key={`${index}-${entry}`} className="flex items-start gap-1">
          <span className="mt-0.5 shrink-0 font-mono text-[7px] text-[#9f1239]">&gt;</span>
          <span
            className="text-[10px] leading-relaxed text-[#4f5d6a]"
          >
            {entry}
          </span>
        </div>
      ))}

      {cursor.entry < entries.length && (
        <div className="flex items-start gap-1">
          <span className="mt-0.5 shrink-0 font-mono text-[7px] text-[#9f1239]">&gt;</span>
          <span
            className="text-[10px] leading-relaxed text-[#4f5d6a]"
          >
            {currentText}
            <span className="animate-pulse">|</span>
          </span>
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  )
}
