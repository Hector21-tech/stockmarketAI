/**
 * MarketsAI Typography System
 * Professional font hierarchy for financial data
 */

export const Typography = {
  // Font Families
  fontFamily: {
    primary: 'System',      // System default for best compatibility
    mono: 'Courier',        // Monospace for numbers/prices
    display: 'System',      // Display font for headers
  },

  // Font Sizes
  fontSize: {
    xs: 10,
    sm: 12,
    base: 14,
    md: 16,
    lg: 18,
    xl: 20,
    '2xl': 24,
    '3xl': 28,
    '4xl': 32,
    '5xl': 40,
  },

  // Font Weights
  fontWeight: {
    light: '300',
    normal: '400',
    medium: '500',
    semibold: '600',
    bold: '700',
    extrabold: '800',
  },

  // Line Heights
  lineHeight: {
    tight: 1.2,
    normal: 1.5,
    relaxed: 1.75,
    loose: 2,
  },

  // Letter Spacing
  letterSpacing: {
    tight: -0.5,
    normal: 0,
    wide: 0.5,
    wider: 1,
  },

  // Text Styles (predefined combinations)
  styles: {
    // Headers
    h1: {
      fontSize: 32,
      fontWeight: '700',
      lineHeight: 1.2,
      letterSpacing: -0.5,
    },
    h2: {
      fontSize: 28,
      fontWeight: '700',
      lineHeight: 1.2,
      letterSpacing: -0.5,
    },
    h3: {
      fontSize: 24,
      fontWeight: '600',
      lineHeight: 1.3,
    },
    h4: {
      fontSize: 20,
      fontWeight: '600',
      lineHeight: 1.4,
    },
    h5: {
      fontSize: 18,
      fontWeight: '600',
      lineHeight: 1.4,
    },
    h6: {
      fontSize: 16,
      fontWeight: '600',
      lineHeight: 1.4,
    },

    // Body
    body: {
      fontSize: 14,
      fontWeight: '400',
      lineHeight: 1.5,
    },
    bodyLarge: {
      fontSize: 16,
      fontWeight: '400',
      lineHeight: 1.5,
    },
    bodySmall: {
      fontSize: 12,
      fontWeight: '400',
      lineHeight: 1.5,
    },

    // Special
    caption: {
      fontSize: 12,
      fontWeight: '400',
      lineHeight: 1.4,
      letterSpacing: 0.5,
    },
    overline: {
      fontSize: 10,
      fontWeight: '500',
      lineHeight: 1.4,
      letterSpacing: 1,
      textTransform: 'uppercase',
    },

    // Price/Numbers (monospace)
    price: {
      fontSize: 20,
      fontWeight: '600',
      fontFamily: 'Courier',
      lineHeight: 1.2,
    },
    priceLarge: {
      fontSize: 28,
      fontWeight: '700',
      fontFamily: 'Courier',
      lineHeight: 1.2,
    },
    priceSmall: {
      fontSize: 14,
      fontWeight: '500',
      fontFamily: 'Courier',
      lineHeight: 1.2,
    },

    // Percentage change
    percentChange: {
      fontSize: 14,
      fontWeight: '600',
      fontFamily: 'Courier',
    },

    // Button text
    button: {
      fontSize: 14,
      fontWeight: '600',
      lineHeight: 1.2,
      letterSpacing: 0.5,
    },
    buttonLarge: {
      fontSize: 16,
      fontWeight: '600',
      lineHeight: 1.2,
      letterSpacing: 0.5,
    },

    // Tab text
    tab: {
      fontSize: 12,
      fontWeight: '500',
      lineHeight: 1.2,
    },

    // Input text
    input: {
      fontSize: 14,
      fontWeight: '400',
      lineHeight: 1.4,
    },
  },
};

export default Typography;
