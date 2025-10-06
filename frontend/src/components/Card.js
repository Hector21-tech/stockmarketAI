/**
 * Custom Card Component
 * Container for grouping related information
 */

import React from 'react';
import { View, StyleSheet } from 'react-native';
import { useTheme } from '../theme/ThemeContext';

const Card = ({
  children,
  variant = 'default', // default, elevated, outlined
  padding = 'base',
  style,
  ...props
}) => {
  const { theme } = useTheme();

  const cardStyles = [
    styles.base,
    {
      backgroundColor: getBackgroundColor(variant, theme),
      padding: getPadding(padding, theme),
      borderWidth: variant === 'outlined' ? theme.spacing.borderWidth.thin : 0,
      borderColor: variant === 'outlined' ? theme.colors.border.primary : 'transparent',
      borderRadius: theme.spacing.borderRadius.md,
    },
    variant === 'elevated' && theme.shadows.md,
    style,
  ];

  return (
    <View style={cardStyles} {...props}>
      {children}
    </View>
  );
};

// Helper functions
const getBackgroundColor = (variant, theme) => {
  switch (variant) {
    case 'elevated':
      return theme.colors.background.elevated;
    case 'outlined':
    case 'default':
    default:
      return theme.colors.background.tertiary;
  }
};

const getPadding = (padding, theme) => {
  if (typeof padding === 'number') {
    return padding;
  }

  switch (padding) {
    case 'none':
      return 0;
    case 'sm':
      return theme.spacing.sm;
    case 'md':
      return theme.spacing.md;
    case 'base':
      return theme.spacing.base;
    case 'lg':
      return theme.spacing.lg;
    default:
      return theme.spacing.base;
  }
};

const styles = StyleSheet.create({
  base: {
    overflow: 'hidden',
  },
});

export default Card;
