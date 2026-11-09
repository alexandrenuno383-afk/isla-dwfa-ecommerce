export function toMinorUnits(amount: string): number {
  const match = /^(\d+)(?:\.(\d{1,2}))?$/.exec(amount)
  if (!match) throw new Error(`Valor monetário inválido: ${amount}`)

  const whole = Number(match[1])
  const fraction = Number((match[2] ?? '').padEnd(2, '0'))
  return whole * 100 + fraction
}

export function formatMinorUnits(amount: number): string {
  const sign = amount < 0 ? '-' : ''
  const absolute = Math.abs(amount)
  const whole = Math.floor(absolute / 100)
  const fraction = String(absolute % 100).padStart(2, '0')
  return `${sign}${whole}.${fraction}`
}
