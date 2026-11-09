import { describe, expect, it } from 'vitest'

import { formatMinorUnits, toMinorUnits } from '../money'

describe('money helpers', () => {
  it('parses decimal strings to integer minor units without float arithmetic', () => {
    expect(toMinorUnits('9.90')).toBe(990)
    expect(toMinorUnits('12.5')).toBe(1250)
  })

  it('formats integer minor units with two decimal places', () => {
    expect(formatMinorUnits(990)).toBe('9.90')
    expect(formatMinorUnits(1250)).toBe('12.50')
  })
})
