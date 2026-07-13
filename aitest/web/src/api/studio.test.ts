import { describe, expect, it } from 'vitest'
import { normalizeRunStatus } from './studio'

describe('normalizeRunStatus', () => {
  it.each([
    ['completed', 'success'],
    ['succeeded', 'success'],
    ['timed_out', 'failed'],
    ['pending', 'running'],
    ['cancelled', 'warning'],
    ['unknown', 'idle'],
  ])('maps %s to %s', (input, expected) => {
    expect(normalizeRunStatus(input)).toBe(expected)
  })
})
