/**
 * Custom Button Component
 * Professional trading app button with variants
 */

import React from 'react';
import { TouchableOpacity, Text, StyleSheet, ActivityIndicator } from 'react-native';
import { useTheme } from '../theme/ThemeContext';

const Button = ({
  children,
  onPress,
  variant = 'primary', // primary, secondary, outline, ghost
  size = 'md', // sm, md, lg
  disabled = false,
  loading = false,
  style,
  textStyle,
  ...props
}) => {
  const { theme } = useTheme();

  const buttonStyles = [
    styles.base,
    {
      backgroundColor: getBackgroundColor(variant, theme, disabled),
      borderWidth: variant === 'outline' ? theme.spacing.borderWidth.base : 0,
      borderColor: variant === 'outline' ? theme.colors.primary : 'transparent',
      paddingVertical: getSizePadding(size, theme).vertical,
      paddingHorizontal: getSizePadding(size, theme).horizontal,
      opacity: disabled ? 0.5 : 1,
    },
    style,
  ];

  const textStyles = [
    {
      color: getTextColor(variant, theme, disabled),
      fontSize: getSizeFontSize(size, theme),
      fontWeight: theme.typography.fontWeight.semibold,
    },
    textStyle,
  ];

  return (
    <TouchableOpacity
      style={buttonStyles}
      onPress={onPress}
      disabled={disabled || loading}
      activeOpacity={0.7}
      {...props}
    >
      {loading ? (
        <ActivityIndicator color={getTextColor(variant, theme, disabled)} />
      ) : (
        <Text style={textStyles}>{children}</Text>
      )}
    </TouchableOpacity>
  );
};

// Helper functions
const getBackgroundColor = (variant, theme, disabled) => {
  if (disabled) {
    return theme.colors.background.tertiary;
  }

  switch (variant) {
    case 'primary':
      return theme.colors.primary;
    case 'secondary':
      return theme.colors.background.elevated;
    case 'outline':
    case 'ghost':
      return 'transparent';
    default:
      return theme.colors.primary;
  }
};

const getTextColor = (variant, theme, disabled) => {
  if (disabled) {
    return theme.colors.text.tertiary;
  }

  switch (variant) {
    case 'primary':
      return '#FFFFFF';
    case 'secondary':
    case 'outline':
    case 'ghost':
      return theme.colors.primary;
    default:
      return '#FFFFFF';
  }
};

const getSizePadding = (size, theme) => {
  switch (size) {
    case 'sm':
      return { vertical: theme.spacing.sm, horizontal: theme.spacing.md };
    case 'md':
      return { vertical: theme.spacing.md, horizontal: theme.spacing.lg };
    case 'lg':
      return { vertical: theme.spacing.base, horizontal: theme.spacing.xl };
    default:
      return { vertical: theme.spacing.md, horizontal: theme.spacing.lg };
  }
};

const getSizeFontSize = (size, theme) => {
  switch (size) {
    case 'sm':
      return theme.typography.fontSize.sm;
    case 'md':
      return theme.typography.fontSize.base;
    case 'lg':
      return theme.typography.fontSize.md;
    default:
      return theme.typography.fontSize.base;
  }
};

const styles = StyleSheet.create({
  base: {
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: 44, // Good touch target
  },
});

export default Button;
