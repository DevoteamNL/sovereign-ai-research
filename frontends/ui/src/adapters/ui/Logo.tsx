// SPDX-FileCopyrightText: Copyright (c) 2025-2026, NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: Apache-2.0

/**
 * Logo Component Shim
 *
 * Renders the Red Hat logo as an inline SVG.
 * The fill color is Red Hat red (#EE0000).
 */

import { type FC } from 'react'

interface LogoProps {
  /** 'horizontal' renders a wider logo; 'logo-only' renders the hat mark */
  kind?: 'horizontal' | 'logo-only'
  size?: 'small' | 'medium' | 'large'
  className?: string
}

/** Dimensions when showing the full logo (wider aspect for horizontal layout) */
const fullSizeMap = {
  small: { width: 80, height: 44 },
  medium: { width: 120, height: 66 },
  large: { width: 160, height: 88 },
} as const

/** Dimensions when showing just the hat */
const eyeSizeMap = {
  small: { width: 28, height: 28 },
  medium: { width: 40, height: 40 },
  large: { width: 56, height: 56 },
} as const

/**
 * Renders the Red Hat fedora logo as an inline SVG.
 */
export const Logo: FC<LogoProps> = ({ kind = 'horizontal', size = 'medium', className }) => {
  const isHatOnly = kind === 'logo-only'
  const dims = isHatOnly ? eyeSizeMap[size] : fullSizeMap[size]

  return (
    <span
      className={className}
      style={{ display: 'inline-flex', alignItems: 'center', width: dims.width, height: dims.height }}
    >
      <svg
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 512 512"
        width={dims.width}
        height={dims.height}
        aria-label="Red Hat"
        role="img"
      >
        {/* Red Hat fedora icon */}
        <path
          d="M341.5 261.1c-1.1-3.6-3.2-7-6.2-9.7l-2.6-2.3c-5.8-5-13.3-7.7-21-7.7h-16.4c-1.4 0-2.7.3-3.9.8l-35.7 15.3c-3.1 1.3-5.1 4.3-5.1 7.7v7.9c0 3.3 2 6.3 5.1 7.6l11.5 4.9c3.1 1.3 5.1 4.3 5.1 7.6v18.6c0 4.6-3.7 8.3-8.3 8.3H196c-4.6 0-8.3 3.7-8.3 8.3v16.6c0 4.6 3.7 8.3 8.3 8.3h67.5c29.8 0 54-24.2 54-54v-9.8c0-2.5-1.1-4.9-3.1-6.5l-9.2-7.6c-1.9-1.6-3.1-3.9-3.1-6.5v-.5c0-2.8 1.4-5.3 3.7-6.8l4.5-2.9c2.3-1.5 3.7-4.1 3.7-6.8v-2.2c0-1.3-.2-2.7-.5-3.8z"
          fill="#EE0000"
        />
        <path
          d="M459.4 187.5c-25.7-3.3-50.9 2.8-71.4 17.3l-14 9.9c-8.5 6-18.5 9.2-28.8 9.2h-39.9c-6.3 0-12.3 1.5-17.8 4.3l-50.9 25.8c-9.2 4.7-15.1 14.1-15.1 24.5v14.1c0 9.4 4.8 18.2 12.7 23.3l23.7 15.2c2.6 1.7 4.2 4.6 4.2 7.7v30.4c0 15 12.2 27.2 27.2 27.2h30.1c44.7 0 81-36.3 81-81v-13.5c0-3.6-1.7-7-4.5-9.2l-14.6-11.3c-2.8-2.2-4.5-5.6-4.5-9.2v-4.2c0-4.1 2.1-7.9 5.6-10.1l14.7-9.4c5.5-3.5 8.8-9.5 8.8-16v-4.3c0-3.2-.6-6.3-1.8-9.2-2.1-5.2-3.5-10.8-3.8-16.5-.3-4.6 3.7-8.5 8.3-7.9 7.8 1.1 15.4 3.6 22.3 7.6 8.2 4.7 17.7 6.2 27 4.2l.6-.1c8-1.7 14.9-6.7 18.9-13.7 4-7 4.7-15.2 2-22.7-3.2-8.8-10.7-15.1-19.9-16.4z"
          fill="#EE0000"
        />
      </svg>
    </span>
  )
}
