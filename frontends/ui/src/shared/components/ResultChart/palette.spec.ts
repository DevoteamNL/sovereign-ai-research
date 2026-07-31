// SPDX-FileCopyrightText: Copyright (c) 2025-2026, NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: Apache-2.0

import { describe, expect, test } from 'vitest'
import { CYCLE, GAIN, LOSS, PALETTE, seriesColor } from './palette'

describe('seriesColor', () => {
  test('honors an explicit color', () => {
    expect(seriesColor('secondary', 0)).toBe(PALETTE.secondary)
  })

  test('cycles through the default order when unset', () => {
    expect(seriesColor(undefined, 0)).toBe(PALETTE.primary)
    expect(seriesColor(undefined, 1)).toBe(PALETTE.secondary)
    expect(seriesColor(undefined, 5)).toBe(PALETTE.primary)
  })
})

describe('diverging colors', () => {
  test('gain and loss are visually distinct', () => {
    // Regression guard. Upstream set GAIN = PALETTE.green, which resolves to
    // var(--color-brand) -- #EE0000 in this fork -- making gain and loss both red.
    expect(GAIN).not.toBe(LOSS)
  })

  test('loss carries the brand red, gain does not', () => {
    expect(LOSS).toContain('--result-chart-loss')
    expect(GAIN).toContain('--result-chart-gain')
  })
})

describe('palette integrity', () => {
  test('every cycle slot resolves to a palette entry', () => {
    for (const slot of CYCLE) {
      expect(PALETTE[slot]).toBeTruthy()
    }
  })

  test('slots are named by role, never by hue', () => {
    // Hue names caused the defect this palette fixes: a slot called "green" that
    // painted Red Hat red, while the agent prompts told the model to say "green".
    const hueNames = ['green', 'blue', 'amber', 'red', 'orange', 'purple']
    for (const name of Object.keys(PALETTE)) {
      expect(hueNames).not.toContain(name)
    }
  })

  test('no two slots share a value', () => {
    const values = Object.values(PALETTE)
    expect(new Set(values).size).toBe(values.length)
  })
})
