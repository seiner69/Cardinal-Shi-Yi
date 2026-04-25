import { useEffect, useRef, useState } from 'react'

interface LogEntry {
  id: string
  text: string
  done?: boolean
}

interface TypewriterLogProps {
  entries: string[]
}

export function TypewriterLog({ entries }: TypewriterLogProps) {
  const [visibleEntries, setVisibleEntries] = useState<LogEntry[]>([])
  const [currentText, setCurrentText] = useState('')
  const [currentIndex, setCurrentIndex] = useState(0)
  const [currentEntryIdx, setCurrentEntryIdx] = useState(0)
  const bottomRef = useRef<HTMLDivElement>(null)
  const speed = 30 // ms per character

  useEffect(() => {
    if (entries.length === 0) {
      setVisibleEntries([])
      setCurrentText('')
      setCurrentIndex(0)
      setCurrentEntryIdx(0)
      return
    }

    // Start fresh if entries changed
    const newEntry: LogEntry = { id: `log-${Date.now()}`, text: entries[entries.length - 1] }
    if (visibleEntries.length === 0 && entries.length > 0) {
      setVisibleEntries([{ ...newEntry, done: false }])
      setCurrentEntryIdx(entries.length - 1)
      setCurrentIndex(0)
    } else if (entries.length > visibleEntries.length) {
      // Add new entry
      setVisibleEntries(prev => [...prev.map(e => ({ ...e, done: true })), { ...newEntry, done: false }])
      setCurrentEntryIdx(entries.length - 1)
      setCurrentIndex(0)
    }
  }, [entries])

  useEffect(() => {
    if (currentEntryIdx >= entries.length) return

    const text = entries[currentEntryIdx]
    if (currentIndex >= text.length) {
      // Move to next entry
      setVisibleEntries(prev =>
        prev.map((e, i) => (i === prev.length - 1 ? { ...e, done: true } : e))
      )
      setCurrentEntryIdx(prev => prev + 1)
      setCurrentIndex(0)
      setCurrentText('')
      return
    }

    const timeout = setTimeout(() => {
      setCurrentText(text.slice(0, currentIndex + 1))
      setCurrentIndex(prev => prev + 1)
    }, speed)

    return () => clearTimeout(timeout)
  }, [currentIndex, currentEntryIdx, entries])

  // Auto scroll to bottom
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [visibleEntries, currentText])

  return (
    <div className="flex flex-col gap-0.5 max-h-32 overflow-y-auto">
      {visibleEntries.map((entry) => (
        <div key={entry.id} className="flex items-start gap-1">
          <span className="font-mono text-[7px] text-gray-400 shrink-0 mt-0.5">›</span>
          <span
            className="font-mono text-[9px] text-gray-600 leading-relaxed"
            style={{ fontFamily: "'Noto Serif SC', serif" }}
          >
            {entry.text}
          </span>
        </div>
      ))}

      {/* Current typing entry */}
      {currentEntryIdx < entries.length && (
        <div className="flex items-start gap-1">
          <span className="font-mono text-[7px] text-gray-400 shrink-0 mt-0.5">›</span>
          <span
            className="font-mono text-[9px] text-gray-600 leading-relaxed"
            style={{ fontFamily: "'Noto Serif SC', serif" }}
          >
            {currentText}
            <span className="animate-pulse">▌</span>
          </span>
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  )
}
