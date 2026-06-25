export function toDisplayBits(bits: string | null | undefined) {
  return bits && /^[01]{6}$/.test(bits) ? bits.split('').reverse().join('') : bits ?? '-'
}

export function formatBits(bits: string | null | undefined, displayBits?: string | null) {
  if (displayBits && /^[01]{6}$/.test(displayBits)) return displayBits
  return toDisplayBits(bits)
}
