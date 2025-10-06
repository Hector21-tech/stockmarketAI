/**
 * MarketsAI Theme System
 * Central export for all theme tokens
 */

import { Colors } from './colors';
import { Typography } from './typography';
import { Spacing } from './spacing';

/**
 * Get theme based on mode (dark/light)
 * @param {string} mode - 'dark' or 'light'
 * @returns {object} Complete theme object
 */
export const getTheme = (mode = 'dark') => {
  const isDark = mode === 'dark';

  return {
    mode,
    isDark,

    // Colors based on mode
    colors: {
      // Brand colors (same for both modes)
      primary: Colors.primary,
      secondary: Colors.secondary,
      accent: Colors.accent,

      // Market colors
      bullish: Colors.bullish,
      bearish: Colors.bearish,
      neutral: Colors.neutral,

      // Status colors
      success: Colors.success,
      warning: Colors.warning,
      error: Colors.error,
      info: Colors.info,

      // Mode-specific colors
      background: isDark ? Colors.dark.background : Colors.light.background,
      text: isDark ? Colors.dark.text : Colors.light.text,
      border: isDark ? Colors.dark.border : Colors.light.border,
      chart: isDark ? Colors.dark.chart : Colors.light.chart,

      // Chart indicators (same for both)
      indicators: Colors.indicators,

      // Gradients
      gradients: Colors.gradients,

      // Helper function
      alpha: Colors.alpha,
    },

    // Typography (same for both modes)
    typography: Typography,

    // Spacing (same for both modes)
    spacing: Spacing,

    // Shadows (mode-specific)
    shadows: isDark
      ? {
          sm: {
            shadowColor: '#000',
            shadowOffset: { width: 0, height: 1 },
            shadowOpacity: 0.3,
            shadowRadius: 2,
            elevation: 2,
          },
          md: {
            shadowColor: '#000',
            shadowOffset: { width: 0, height: 2 },
            shadowOpacity: 0.4,
            shadowRadius: 4,
            elevation: 4,
          },
          lg: {
            shadowColor: '#000',
            shadowOffset: { width: 0, height: 4 },
            shadowOpacity: 0.5,
            shadowRadius: 8,
            elevation: 8,
          },
        }
      : {
          sm: {
            shadowColor: '#000',
            shadowOffset: { width: 0, height: 1 },
            shadowOpacity: 0.1,
            shadowRadius: 2,
            elevation: 2,
          },
          md: {
            shadowColor: '#000',
            shadowOffset: { width: 0, height: 2 },
            shadowOpacity: 0.15,
            shadowRadius: 4,
            elevation: 4,
          },
          lg: {
            shadowColor: '#000',
            shadowOffset: { width: 0, height: 4 },
            shadowOpacity: 0.2,
            shadowRadius: 8,
            elevation: 8,
          },
        },
  };
};

// Export individual modules
export { Colors, Typography, Spacing };

// Default export (dark theme)
export default getTheme('dark');
