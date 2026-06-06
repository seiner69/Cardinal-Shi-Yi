export function eventLabel(event: string | undefined) {
  switch (event) {
    case 'collapse':
      return '坍缩'
    case 'crush':
      return '压碎'
    case 'explosion':
      return '爆发'
    case 'stable':
      return '稳定'
    default:
      return event ?? '-'
  }
}

export function phaseLabel(phase: string | undefined) {
  return phase ? `相位 ${phase}` : '相位 -'
}

export function ttlLabel(ttl: number | null | undefined) {
  return ttl ?? '无穷'
}
