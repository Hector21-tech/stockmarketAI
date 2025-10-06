/**
 * PriceText Component
 * Displays prices and percentage changes with color coding
 */

import React from 'react';
import { Text, StyleSheet } from 'react-native';
import { useTheme } from '../theme/ThemeContext';

const PriceText = ({
  value,
  prefix = '',
  suffix = '',
  size = 'md', // sm, md, lg
  showChange = false, // Show +/- prefix
  colorize = false, // Color based on positive/negative
  style,
  ...props
}) => {
  const { theme } = useTheme();

  // Determine if value is positive or negative
  const numValue = typeof value === 'string' ? parseFloat(value) : value;
  const isPositive = numValue > 0;
  const isNegative = numValue < 0;
  const isZero = numValue === 0;

  // Get color
  const getColor = () => {
    if (!colorize) {
      return theme.colors.text.primary;
    }

    if (isPositive) return theme.colors.bullish;
    if (isNegative) return theme.colors.bearish;
    return theme.colors.text.secondary;
  };

  // Get font size
  const getFontSize = () => {
    switch (size) {
      case 'sm':
        return theme.typography.styles.priceSmall.fontSize;
      case 'md':
        return theme.typography.styles.price.fontSize;
      case 'lg':
        return theme.typography.styles.priceLarge.fontSize;
      default:
        return theme.typography.styles.price.fontSize;
    }
  };

  // Format value
  const formatValue = () => {
    if (typeof value === 'undefined' || value === null) return '--';

    const absValue = Math.abs(numValue);
    const formatted = absValue.toFixed(2);

    // Add +/- prefix if requested
    if (showChange) {
      if (isPositive) return `+${formatted}`;
      if (isNegative) return `-${formatted}`;
    }

    return formatted;
  };

  const textStyles = [
    styles.base,
    {
      color: getColor(),
      fontSize: getFontSize(),
      fontWeight: theme.typography.fontWeight.semibold,
      fontFamily: theme.typography.fontFamily.mono,
    },
    style,
  ];

  return (
    <Text style={textStyles} {...props}>
      {prefix}{formatValue()}{suffix}
    </Text>
  );
};

const styles = StyleSheet.create({
  base: {
    letterSpacing: 0.5,
  },
});

export default PriceText;
