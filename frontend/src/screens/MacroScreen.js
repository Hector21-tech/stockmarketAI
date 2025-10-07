/**
 * Macro Dashboard Screen
 * Displays key macro indicators: M2, Fed Funds, DXY, VIX, Treasury Yields
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  RefreshControl,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { useTheme } from '../theme/ThemeContext';
import { Card, PriceText } from '../components';
import { api } from '../api/client';

export default function MacroScreen() {
  const { theme } = useTheme();
  const [loading, setLoading] = useState(false);
  const [macroData, setMacroData] = useState({
    m2: null,
    fedFunds: null,
    dxy: null,
    vix: null,
    treasury10y: null,
    regime: 'loading',
    sentiment: null,
    correlations: null,
    seasonality: null,
  });

  useEffect(() => {
    fetchMacroData();
  }, []);

  const fetchMacroData = async () => {
    setLoading(true);
    try {
      const response = await api.getMacroData();

      if (response.data.success) {
        const data = response.data.data;
        setMacroData({
          m2: data.m2,
          fedFunds: data.fedFunds,
          dxy: data.dxy,
          vix: data.vix,
          treasury10y: data.treasury10y,
          regime: data.regime,
          sentiment: data.sentiment,
          correlations: data.correlations,
          seasonality: data.seasonality,
        });
      }
    } catch (error) {
      console.error('Error fetching macro data:', error);
      Alert.alert('Fel', 'Kunde inte hämta makrodata');
    } finally {
      setLoading(false);
    }
  };

  const getRegimeInfo = (regime) => {
    switch (regime) {
      case 'bullish':
        return {
          label: 'Bull Market',
          color: theme.colors.success,
          description: 'Favorable conditions for risk assets',
          icon: '📈',
        };
      case 'bearish':
        return {
          label: 'Bear Market',
          color: theme.colors.danger,
          description: 'Defensive positioning recommended',
          icon: '📉',
        };
      case 'transition':
        return {
          label: 'Transition',
          color: theme.colors.warning,
          description: 'Market regime unclear - caution advised',
          icon: '⚠️',
        };
      default:
        return {
          label: 'Loading',
          color: theme.colors.text.tertiary,
          description: 'Analyzing market conditions...',
          icon: '⏳',
        };
    }
  };

  const getCorrelationColor = (correlation) => {
    if (correlation === null || correlation === undefined) return theme.colors.text.tertiary;

    // Strong positive: green
    if (correlation > 0.7) return '#16a34a';
    // Moderate positive: light green
    if (correlation > 0.3) return '#22c55e';
    // Weak/neutral: gray
    if (correlation > -0.3) return '#94a3b8';
    // Moderate negative: orange
    if (correlation > -0.7) return '#f59e0b';
    // Strong negative: red
    return '#ef4444';
  };

  const getCorrelationLabel = (correlation) => {
    if (correlation === null || correlation === undefined) return 'N/A';

    if (correlation > 0.7) return 'Strong +';
    if (correlation > 0.3) return 'Moderate +';
    if (correlation > -0.3) return 'Weak';
    if (correlation > -0.7) return 'Moderate -';
    return 'Strong -';
  };

  const renderMacroCard = (data) => {
    if (!data) return null;

    return (
      <Card variant="default" style={{ marginBottom: theme.spacing.md }}>
        <Text
          style={[
            styles.cardLabel,
            {
              color: theme.colors.text.secondary,
              fontSize: theme.typography.fontSize.sm,
            },
          ]}
        >
          {data.label}
        </Text>
        <View style={styles.cardContent}>
          <View style={{ flexDirection: 'row', alignItems: 'baseline' }}>
            <Text
              style={[
                styles.cardValue,
                {
                  color: theme.colors.text.primary,
                  ...theme.typography.styles.h4,
                },
              ]}
            >
              {data.value.toFixed(2)}
            </Text>
            {data.unit && (
              <Text
                style={[
                  styles.cardUnit,
                  {
                    color: theme.colors.text.secondary,
                    fontSize: theme.typography.fontSize.md,
                    marginLeft: theme.spacing.xs,
                  },
                ]}
              >
                {data.unit}
              </Text>
            )}
          </View>
          <View style={{ flexDirection: 'row', alignItems: 'center', marginTop: theme.spacing.xs }}>
            <PriceText
              value={data.change}
              size="sm"
              showChange
              colorize
              style={{ marginRight: theme.spacing.xs }}
            />
            <PriceText
              value={data.changePercent}
              size="sm"
              showChange
              colorize
              suffix="%"
            />
          </View>
        </View>
      </Card>
    );
  };

  const regimeInfo = getRegimeInfo(macroData.regime);

  return (
    <View style={[styles.container, { backgroundColor: theme.colors.background.primary }]}>
      <ScrollView
        contentContainerStyle={{
          padding: theme.spacing.base,
        }}
        refreshControl={
          <RefreshControl
            refreshing={loading}
            onRefresh={fetchMacroData}
            tintColor={theme.colors.primary}
          />
        }
      >
        {/* Header */}
        <View style={{ marginBottom: theme.spacing.xl }}>
          <Text
            style={[
              styles.title,
              {
                color: theme.colors.text.primary,
                ...theme.typography.styles.h5,
                marginBottom: theme.spacing.xs,
              },
            ]}
          >
            Macro Dashboard
          </Text>
          <Text
            style={[
              styles.subtitle,
              {
                color: theme.colors.text.secondary,
                fontSize: theme.typography.fontSize.sm,
              },
            ]}
          >
            Key economic indicators and market regime
          </Text>
        </View>

        {/* Market Regime Card */}
        <Card
          variant="default"
          style={{
            marginBottom: theme.spacing.xl,
            backgroundColor: `${regimeInfo.color}15`,
            borderColor: regimeInfo.color,
            borderWidth: 1,
          }}
        >
          <View style={styles.regimeCard}>
            <Text style={{ fontSize: 40, marginBottom: theme.spacing.sm }}>{regimeInfo.icon}</Text>
            <Text
              style={[
                styles.regimeLabel,
                {
                  color: regimeInfo.color,
                  ...theme.typography.styles.h5,
                  marginBottom: theme.spacing.xs,
                },
              ]}
            >
              {regimeInfo.label}
            </Text>
            <Text
              style={[
                styles.regimeDescription,
                {
                  color: theme.colors.text.secondary,
                  fontSize: theme.typography.fontSize.sm,
                  textAlign: 'center',
                },
              ]}
            >
              {regimeInfo.description}
            </Text>
          </View>
        </Card>

        {/* Macro Indicators Grid */}
        <Text
          style={[
            styles.sectionTitle,
            {
              color: theme.colors.text.primary,
              ...theme.typography.styles.h6,
              marginBottom: theme.spacing.md,
            },
          ]}
        >
          Economic Indicators
        </Text>

        {renderMacroCard(macroData.m2)}
        {renderMacroCard(macroData.fedFunds)}
        {renderMacroCard(macroData.dxy)}
        {renderMacroCard(macroData.vix)}
        {renderMacroCard(macroData.treasury10y)}

        {/* Sentiment Section */}
        {macroData.sentiment && (
          <>
            <Text
              style={[
                styles.sectionTitle,
                {
                  color: theme.colors.text.primary,
                  ...theme.typography.styles.h6,
                  marginTop: theme.spacing.xl,
                  marginBottom: theme.spacing.md,
                },
              ]}
            >
              Market Sentiment
            </Text>

            {/* Fear & Greed Gauge */}
            <Card variant="default" style={{ marginBottom: theme.spacing.md }}>
              <Text
                style={[
                  styles.cardLabel,
                  {
                    color: theme.colors.text.secondary,
                    fontSize: theme.typography.fontSize.sm,
                  },
                ]}
              >
                CNN FEAR & GREED INDEX
              </Text>
              <View style={{ alignItems: 'center', paddingVertical: theme.spacing.md }}>
                <Text style={{ fontSize: 64, marginBottom: theme.spacing.sm }}>
                  {macroData.sentiment.fearGreed?.emoji || '😐'}
                </Text>
                <Text
                  style={[
                    {
                      fontSize: theme.typography.fontSize.xxl,
                      fontWeight: theme.typography.fontWeight.bold,
                      color: macroData.sentiment.fearGreed?.color || theme.colors.text.primary,
                      marginBottom: theme.spacing.xs,
                    },
                  ]}
                >
                  {macroData.sentiment.fearGreed?.value || '--'}
                </Text>
                <Text
                  style={[
                    {
                      fontSize: theme.typography.fontSize.lg,
                      fontWeight: theme.typography.fontWeight.semibold,
                      color: macroData.sentiment.fearGreed?.color || theme.colors.text.secondary,
                    },
                  ]}
                >
                  {macroData.sentiment.fearGreed?.label || 'Loading...'}
                </Text>
              </View>
            </Card>

            {/* Put/Call Ratio */}
            {macroData.sentiment.putCallRatio && (
              <Card variant="default" style={{ marginBottom: theme.spacing.md }}>
                <Text
                  style={[
                    styles.cardLabel,
                    {
                      color: theme.colors.text.secondary,
                      fontSize: theme.typography.fontSize.sm,
                    },
                  ]}
                >
                  PUT/CALL RATIO
                </Text>
                <View style={styles.cardContent}>
                  <View style={{ flexDirection: 'row', alignItems: 'baseline' }}>
                    <Text
                      style={[
                        styles.cardValue,
                        {
                          color: theme.colors.text.primary,
                          ...theme.typography.styles.h4,
                        },
                      ]}
                    >
                      {macroData.sentiment.putCallRatio.value.toFixed(2)}
                    </Text>
                  </View>
                  <Text
                    style={[
                      {
                        color: theme.colors.text.tertiary,
                        fontSize: theme.typography.fontSize.sm,
                        marginTop: theme.spacing.xs,
                      },
                    ]}
                  >
                    {macroData.sentiment.putCallRatio.interpretation}
                  </Text>
                </View>
              </Card>
            )}
          </>
        )}

        {/* Correlations Section */}
        {macroData.correlations && macroData.correlations.matrix && (
          <>
            <Text
              style={[
                styles.sectionTitle,
                {
                  color: theme.colors.text.primary,
                  ...theme.typography.styles.h6,
                  marginTop: theme.spacing.xl,
                  marginBottom: theme.spacing.md,
                },
              ]}
            >
              Intermarket Correlations
            </Text>

            <Card variant="default" style={{ marginBottom: theme.spacing.md }}>
              <Text
                style={[
                  styles.cardLabel,
                  {
                    color: theme.colors.text.secondary,
                    fontSize: theme.typography.fontSize.sm,
                    marginBottom: theme.spacing.md,
                  },
                ]}
              >
                CORRELATION MATRIX (3 MONTHS)
              </Text>

              {/* Correlation Heatmap */}
              <View style={{ gap: theme.spacing.sm }}>
                {Object.entries(macroData.correlations.matrix).map(([asset1, correlations]) => (
                  <View key={asset1}>
                    <Text
                      style={[
                        {
                          color: theme.colors.text.secondary,
                          fontSize: theme.typography.fontSize.xs,
                          fontWeight: theme.typography.fontWeight.semibold,
                          marginBottom: theme.spacing.xs,
                          textTransform: 'uppercase',
                        },
                      ]}
                    >
                      {macroData.correlations.labels[asset1]}
                    </Text>
                    <View style={{ flexDirection: 'row', gap: theme.spacing.xs, flexWrap: 'wrap' }}>
                      {Object.entries(correlations).map(([asset2, corr]) => {
                        if (asset1 === asset2) return null; // Skip self-correlation

                        return (
                          <View
                            key={`${asset1}-${asset2}`}
                            style={{
                              backgroundColor: getCorrelationColor(corr) + '20',
                              borderColor: getCorrelationColor(corr),
                              borderWidth: 1,
                              borderRadius: 6,
                              paddingHorizontal: theme.spacing.sm,
                              paddingVertical: theme.spacing.xs,
                              minWidth: 80,
                            }}
                          >
                            <Text
                              style={{
                                fontSize: theme.typography.fontSize.xs,
                                color: theme.colors.text.tertiary,
                              }}
                            >
                              {macroData.correlations.labels[asset2]}
                            </Text>
                            <Text
                              style={{
                                fontSize: theme.typography.fontSize.sm,
                                fontWeight: theme.typography.fontWeight.bold,
                                color: getCorrelationColor(corr),
                              }}
                            >
                              {corr !== null ? corr.toFixed(2) : 'N/A'}
                            </Text>
                            <Text
                              style={{
                                fontSize: theme.typography.fontSize.xs,
                                color: getCorrelationColor(corr),
                              }}
                            >
                              {getCorrelationLabel(corr)}
                            </Text>
                          </View>
                        );
                      })}
                    </View>
                  </View>
                ))}
              </View>

              <Text
                style={[
                  {
                    color: theme.colors.text.tertiary,
                    fontSize: theme.typography.fontSize.xs,
                    marginTop: theme.spacing.md,
                    fontStyle: 'italic',
                  },
                ]}
              >
                Correlation: +1 = perfect positive, 0 = no relationship, -1 = perfect negative
              </Text>
            </Card>
          </>
        )}

        {/* Seasonality Section */}
        {macroData.seasonality && macroData.seasonality.current_month && (
          <>
            <Text
              style={[
                styles.sectionTitle,
                {
                  color: theme.colors.text.primary,
                  ...theme.typography.styles.h6,
                  marginTop: theme.spacing.xl,
                  marginBottom: theme.spacing.md,
                },
              ]}
            >
              Seasonality (S&P 500)
            </Text>

            {/* Current Month Card */}
            <Card variant="default" style={{ marginBottom: theme.spacing.md }}>
              <Text
                style={[
                  styles.cardLabel,
                  {
                    color: theme.colors.text.secondary,
                    fontSize: theme.typography.fontSize.sm,
                    marginBottom: theme.spacing.sm,
                  },
                ]}
              >
                CURRENT MONTH: {macroData.seasonality.current_month.name.toUpperCase()}
              </Text>

              <View style={{ alignItems: 'center', paddingVertical: theme.spacing.md }}>
                <Text
                  style={{
                    fontSize: theme.typography.fontSize.xxl,
                    fontWeight: theme.typography.fontWeight.bold,
                    color: macroData.seasonality.current_month.avg_return > 0 ? theme.colors.success : theme.colors.danger,
                  }}
                >
                  {macroData.seasonality.current_month.avg_return > 0 ? '+' : ''}
                  {macroData.seasonality.current_month.avg_return.toFixed(2)}%
                </Text>
                <Text
                  style={{
                    fontSize: theme.typography.fontSize.sm,
                    color: theme.colors.text.secondary,
                    marginTop: theme.spacing.xs,
                  }}
                >
                  Historical Average Return
                </Text>
                <Text
                  style={{
                    fontSize: theme.typography.fontSize.md,
                    color: theme.colors.text.tertiary,
                    marginTop: theme.spacing.sm,
                  }}
                >
                  Win Rate: {macroData.seasonality.current_month.win_rate.toFixed(0)}%
                </Text>
              </View>
            </Card>

            {/* Best/Worst Months */}
            <View style={{ flexDirection: 'row', gap: theme.spacing.sm, marginBottom: theme.spacing.md }}>
              <Card variant="default" style={{ flex: 1 }}>
                <Text
                  style={[
                    styles.cardLabel,
                    {
                      color: theme.colors.text.secondary,
                      fontSize: theme.typography.fontSize.xs,
                    },
                  ]}
                >
                  BEST MONTH
                </Text>
                <Text
                  style={{
                    fontSize: theme.typography.fontSize.lg,
                    fontWeight: theme.typography.fontWeight.bold,
                    color: theme.colors.text.primary,
                    marginTop: theme.spacing.xs,
                  }}
                >
                  {macroData.seasonality.best_month.name}
                </Text>
                <Text
                  style={{
                    fontSize: theme.typography.fontSize.md,
                    fontWeight: theme.typography.fontWeight.semibold,
                    color: theme.colors.success,
                    marginTop: theme.spacing.xs,
                  }}
                >
                  +{macroData.seasonality.best_month.avg_return.toFixed(2)}%
                </Text>
              </Card>

              <Card variant="default" style={{ flex: 1 }}>
                <Text
                  style={[
                    styles.cardLabel,
                    {
                      color: theme.colors.text.secondary,
                      fontSize: theme.typography.fontSize.xs,
                    },
                  ]}
                >
                  WORST MONTH
                </Text>
                <Text
                  style={{
                    fontSize: theme.typography.fontSize.lg,
                    fontWeight: theme.typography.fontWeight.bold,
                    color: theme.colors.text.primary,
                    marginTop: theme.spacing.xs,
                  }}
                >
                  {macroData.seasonality.worst_month.name}
                </Text>
                <Text
                  style={{
                    fontSize: theme.typography.fontSize.md,
                    fontWeight: theme.typography.fontWeight.semibold,
                    color: theme.colors.danger,
                    marginTop: theme.spacing.xs,
                  }}
                >
                  {macroData.seasonality.worst_month.avg_return.toFixed(2)}%
                </Text>
              </Card>
            </View>

            <Text
              style={[
                {
                  color: theme.colors.text.tertiary,
                  fontSize: theme.typography.fontSize.xs,
                  textAlign: 'center',
                  fontStyle: 'italic',
                },
              ]}
            >
              Based on 5-year historical performance
            </Text>
          </>
        )}

        {/* Info Footer */}
        <Card variant="ghost" style={{ marginTop: theme.spacing.md }}>
          <Text
            style={[
              styles.infoText,
              {
                color: theme.colors.text.tertiary,
                fontSize: theme.typography.fontSize.xs,
                textAlign: 'center',
              },
            ]}
          >
            Data updated daily from Federal Reserve Economic Data (FRED)
          </Text>
        </Card>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  title: {
    fontWeight: 'bold',
  },
  subtitle: {
    lineHeight: 20,
  },
  regimeCard: {
    alignItems: 'center',
    paddingVertical: 10,
  },
  regimeLabel: {
    fontWeight: 'bold',
  },
  regimeDescription: {
    lineHeight: 20,
  },
  sectionTitle: {
    fontWeight: 'bold',
  },
  cardLabel: {
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 8,
  },
  cardContent: {
    flexDirection: 'column',
  },
  cardValue: {
    fontWeight: 'bold',
  },
  cardUnit: {
    fontWeight: '500',
  },
  infoText: {
    lineHeight: 16,
  },
});
