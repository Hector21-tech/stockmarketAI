/**
 * MarketsAI Spacing System
 * Consistent spacing scale (8pt grid system)
 */

export const Spacing = {
  // Base spacing scale (multiples of 4)
  xs: 4,
  sm: 8,
  md: 12,
  base: 16,
  lg: 20,
  xl: 24,
  '2xl': 32,
  '3xl': 40,
  '4xl': 48,
  '5xl': 64,

  // Padding
  padding: {
    xs: 4,
    sm: 8,
    md: 12,
    base: 16,
    lg: 20,
    xl: 24,
    '2xl': 32,
  },

  // Margin
  margin: {
    xs: 4,
    sm: 8,
    md: 12,
    base: 16,
    lg: 20,
    xl: 24,
    '2xl': 32,
  },

  // Gap (for flex/grid)
  gap: {
    xs: 4,
    sm: 8,
    md: 12,
    base: 16,
    lg: 20,
    xl: 24,
  },

  // Border Radius
  borderRadius: {
    none: 0,
    sm: 4,
    md: 8,
    lg: 12,
    xl: 16,
    '2xl': 20,
    full: 9999,
  },

  // Border Width
  borderWidth: {
    none: 0,
    thin: 1,
    base: 2,
    thick: 3,
  },

  // Screen padding (safe areas)
  screen: {
    horizontal: 16,
    vertical: 16,
    top: 20,      // Extra top padding for status bar
    bottom: 20,   // Extra bottom padding for tab bar
  },

  // Component specific
  card: {
    padding: 16,
    gap: 12,
  },
  button: {
    paddingVertical: 12,
    paddingHorizontal: 20,
  },
  input: {
    paddingVertical: 12,
    paddingHorizontal: 16,
  },
  list: {
    itemGap: 8,
    padding: 16,
  },
};

export default Spacing;
