/**
 * MarketsAI Color System
 * Professional trading app colors inspired by Bloomberg & TradingView
 */

export const Colors = {
  // Brand Colors
  primary: '#2196F3',      // Blue
  secondary: '#1976D2',    // Dark Blue
  accent: '#00BCD4',       // Cyan

  // Market Colors
  bullish: '#26A69A',      // Teal Green (gains)
  bearish: '#EF5350',      // Red (losses)
  neutral: '#9E9E9E',      // Gray

  // Dark Theme
  dark: {
    background: {
      primary: '#0A0E27',    // Deep navy (main background)
      secondary: '#131722',  // Slightly lighter navy
      tertiary: '#1E222D',   // Cards/containers
      elevated: '#2A2E39',   // Elevated elements
    },
    text: {
      primary: '#E0E3EB',    // Main text
      secondary: '#9598A1',  // Secondary text
      tertiary: '#6B7280',   // Disabled/hint text
      inverse: '#0A0E27',    // Text on light backgrounds
    },
    border: {
      primary: '#2A2E39',
      secondary: '#1E222D',
      focus: '#2196F3',
    },
    chart: {
      grid: '#1E222D',
      axis: '#6B7280',
      crosshair: '#9598A1',
    },
  },

  // Light Theme
  light: {
    background: {
      primary: '#FFFFFF',
      secondary: '#F5F5F5',
      tertiary: '#FAFAFA',
      elevated: '#FFFFFF',
    },
    text: {
      primary: '#1F2937',
      secondary: '#6B7280',
      tertiary: '#9CA3AF',
      inverse: '#FFFFFF',
    },
    border: {
      primary: '#E5E7EB',
      secondary: '#F3F4F6',
      focus: '#2196F3',
    },
    chart: {
      grid: '#F3F4F6',
      axis: '#9CA3AF',
      crosshair: '#6B7280',
    },
  },

  // Status Colors
  success: '#10B981',      // Green
  warning: '#F59E0B',      // Orange
  error: '#EF4444',        // Red
  info: '#3B82F6',         // Blue

  // Chart Colors (Technical Indicators)
  indicators: {
    rsi: '#9C27B0',        // Purple
    macd: '#FF9800',       // Orange
    macdSignal: '#2196F3', // Blue
    stochastic: '#4CAF50', // Green
    ema20: '#FF5722',      // Deep Orange
    sma50: '#2196F3',      // Blue
    bollinger: '#9E9E9E',  // Gray
    volume: '#78909C',     // Blue Gray
  },

  // Gradient overlays
  gradients: {
    bullish: ['#26A69A', '#66BB6A'],
    bearish: ['#EF5350', '#F44336'],
    primary: ['#2196F3', '#1976D2'],
    dark: ['rgba(10, 14, 39, 0.9)', 'rgba(19, 23, 34, 0.95)'],
  },

  // Opacity helpers
  alpha: (color, opacity) => {
    // Convert hex to rgba
    const hex = color.replace('#', '');
    const r = parseInt(hex.substring(0, 2), 16);
    const g = parseInt(hex.substring(2, 4), 16);
    const b = parseInt(hex.substring(4, 6), 16);
    return `rgba(${r}, ${g}, ${b}, ${opacity})`;
  },
};

export default Colors;
