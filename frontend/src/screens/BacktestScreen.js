import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TextInput,
  TouchableOpacity,
  ActivityIndicator,
  Alert
} from 'react-native';
import { useTheme } from '../context/ThemeContext';
import { Card, Button } from '../components';
import { apiClient } from '../api/client';
import { Ionicons } from '@expo/vector-icons';

export default function BacktestScreen() {
  const { theme } = useTheme();
  const [ticker, setTicker] = useState('VOLVO-B');
  const [market, setMarket] = useState('SE');
  const [startDate, setStartDate] = useState('2024-01-01');
  const [endDate, setEndDate] = useState('2025-01-01');
  const [initialCapital, setInitialCapital] = useState('100000');
  const [mode, setMode] = useState('conservative');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);

  const modes = [
    { id: 'conservative', name: 'Conservative', icon: '🛡️', color: '#3b82f6' },
    { id: 'aggressive', name: 'Aggressive', icon: '⚡', color: '#f97316' },
    { id: 'ai-hybrid', name: 'AI-Hybrid', icon: '🤖', color: '#10b981' }
  ];

  const runBacktest = async () => {
    if (!ticker) {
      Alert.alert('Error', 'Please enter a ticker symbol');
      return;
    }

    setLoading(true);
    setResults(null);

    try {
      const response = await apiClient.post('/backtest', {
        ticker,
        market,
        start_date: startDate,
        end_date: endDate,
        initial_capital: parseInt(initialCapital),
        mode
      });

      if (response.data.error) {
        Alert.alert('Backtest Error', response.data.error);
      } else {
        setResults(response.data);
      }
    } catch (error) {
      console.error('Backtest error:', error);
      Alert.alert('Error', 'Failed to run backtest');
    } finally {
      setLoading(false);
    }
  };

  const renderMetric = (label, value, suffix = '', color = null) => (
    <View style={styles.metricContainer}>
      <Text style={[styles.metricLabel, { color: theme.colors.text.secondary }]}>
        {label}
      </Text>
      <Text style={[
        styles.metricValue,
        { color: color || theme.colors.text.primary }
      ]}>
        {value}{suffix}
      </Text>
    </View>
  );

  const renderTradeRow = (trade, index) => {
    const isProfit = trade.pnl > 0;
    const pnlColor = isProfit ? theme.colors.bullish : theme.colors.bearish;

    return (
      <View
        key={index}
        style={[styles.tradeRow, { borderBottomColor: theme.colors.border }]}
      >
        <View style={styles.tradeDate}>
          <Text style={[styles.tradeText, { color: theme.colors.text.secondary }]}>
            {new Date(trade.entry_date).toLocaleDateString('sv-SE')}
          </Text>
          <Text style={[styles.tradeText, { color: theme.colors.text.secondary }]}>
            →
          </Text>
          <Text style={[styles.tradeText, { color: theme.colors.text.secondary }]}>
            {new Date(trade.exit_date).toLocaleDateString('sv-SE')}
          </Text>
        </View>
        <Text style={[styles.tradeText, { color: theme.colors.text.primary }]}>
          {trade.shares} shares
        </Text>
        <Text style={[styles.tradeText, { color: theme.colors.text.secondary }]}>
          {trade.entry_price.toFixed(2)} SEK
        </Text>
        <Text style={[styles.tradePnL, { color: pnlColor }]}>
          {isProfit ? '+' : ''}{trade.pnl.toFixed(0)} SEK
        </Text>
        <Text style={[styles.tradePnL, { color: pnlColor }]}>
          {isProfit ? '+' : ''}{trade.pnl_percent.toFixed(1)}%
        </Text>
        <Text style={[styles.tradeText, { color: theme.colors.text.secondary, fontSize: 11 }]}>
          {trade.exit_reason}
        </Text>
      </View>
    );
  };

  return (
    <ScrollView
      style={[styles.container, { backgroundColor: theme.colors.background }]}
      contentContainerStyle={styles.content}
    >
      {/* Header */}
      <View style={styles.header}>
        <Ionicons name="analytics" size={32} color={theme.colors.primary} />
        <Text style={[styles.title, { color: theme.colors.text.primary }]}>
          Strategy Backtester
        </Text>
        <Text style={[styles.subtitle, { color: theme.colors.text.secondary }]}>
          Test your signal mode historically
        </Text>
      </View>

      {/* Input Form */}
      <Card variant="elevated" style={{ marginBottom: theme.spacing.lg }}>
        <Text style={[styles.sectionTitle, { color: theme.colors.text.primary }]}>
          Backtest Configuration
        </Text>

        {/* Ticker */}
        <Text style={[styles.label, { color: theme.colors.text.secondary }]}>Ticker</Text>
        <TextInput
          style={[styles.input, {
            backgroundColor: theme.colors.surface,
            color: theme.colors.text.primary,
            borderColor: theme.colors.border
          }]}
          value={ticker}
          onChangeText={setTicker}
          placeholder="VOLVO-B"
          placeholderTextColor={theme.colors.text.secondary}
          autoCapitalize="characters"
        />

        {/* Market */}
        <Text style={[styles.label, { color: theme.colors.text.secondary }]}>Market</Text>
        <View style={styles.marketButtons}>
          <TouchableOpacity
            style={[
              styles.marketButton,
              {
                backgroundColor: market === 'SE' ? theme.colors.primary : theme.colors.surface,
                borderColor: theme.colors.border
              }
            ]}
            onPress={() => setMarket('SE')}
          >
            <Text style={[styles.marketButtonText, {
              color: market === 'SE' ? '#fff' : theme.colors.text.primary
            }]}>
              SE
            </Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[
              styles.marketButton,
              {
                backgroundColor: market === 'US' ? theme.colors.primary : theme.colors.surface,
                borderColor: theme.colors.border
              }
            ]}
            onPress={() => setMarket('US')}
          >
            <Text style={[styles.marketButtonText, {
              color: market === 'US' ? '#fff' : theme.colors.text.primary
            }]}>
              US
            </Text>
          </TouchableOpacity>
        </View>

        {/* Dates */}
        <Text style={[styles.label, { color: theme.colors.text.secondary }]}>Start Date</Text>
        <TextInput
          style={[styles.input, {
            backgroundColor: theme.colors.surface,
            color: theme.colors.text.primary,
            borderColor: theme.colors.border
          }]}
          value={startDate}
          onChangeText={setStartDate}
          placeholder="YYYY-MM-DD"
          placeholderTextColor={theme.colors.text.secondary}
        />

        <Text style={[styles.label, { color: theme.colors.text.secondary }]}>End Date</Text>
        <TextInput
          style={[styles.input, {
            backgroundColor: theme.colors.surface,
            color: theme.colors.text.primary,
            borderColor: theme.colors.border
          }]}
          value={endDate}
          onChangeText={setEndDate}
          placeholder="YYYY-MM-DD"
          placeholderTextColor={theme.colors.text.secondary}
        />

        {/* Initial Capital */}
        <Text style={[styles.label, { color: theme.colors.text.secondary }]}>Initial Capital (SEK)</Text>
        <TextInput
          style={[styles.input, {
            backgroundColor: theme.colors.surface,
            color: theme.colors.text.primary,
            borderColor: theme.colors.border
          }]}
          value={initialCapital}
          onChangeText={setInitialCapital}
          placeholder="100000"
          placeholderTextColor={theme.colors.text.secondary}
          keyboardType="numeric"
        />

        {/* Mode Selection */}
        <Text style={[styles.label, { color: theme.colors.text.secondary }]}>Signal Mode</Text>
        <View style={styles.modeSelector}>
          {modes.map((m) => (
            <TouchableOpacity
              key={m.id}
              style={[
                styles.modeButton,
                {
                  backgroundColor: mode === m.id ? m.color : theme.colors.surface,
                  borderColor: mode === m.id ? m.color : theme.colors.border
                }
              ]}
              onPress={() => setMode(m.id)}
            >
              <Text style={{ fontSize: 20, marginBottom: 4 }}>{m.icon}</Text>
              <Text style={[styles.modeButtonText, {
                color: mode === m.id ? '#fff' : theme.colors.text.primary
              }]}>
                {m.name}
              </Text>
            </TouchableOpacity>
          ))}
        </View>

        {/* Run Button */}
        <Button
          title={loading ? "Running Backtest..." : "Run Backtest"}
          onPress={runBacktest}
          disabled={loading}
          style={{ marginTop: theme.spacing.lg }}
        />
      </Card>

      {/* Loading */}
      {loading && (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={theme.colors.primary} />
          <Text style={[styles.loadingText, { color: theme.colors.text.secondary }]}>
            Analyzing historical data...
          </Text>
        </View>
      )}

      {/* Results */}
      {results && results.metrics && (
        <>
          {/* Metrics Overview */}
          <Card variant="elevated" style={{ marginBottom: theme.spacing.lg }}>
            <Text style={[styles.sectionTitle, { color: theme.colors.text.primary }]}>
              Performance Metrics
            </Text>

            <View style={styles.metricsGrid}>
              {renderMetric(
                'Total Return',
                results.metrics.total_return.toFixed(1),
                '%',
                results.metrics.total_return > 0 ? theme.colors.bullish : theme.colors.bearish
              )}
              {renderMetric(
                'CAGR',
                results.metrics.cagr.toFixed(1),
                '%',
                results.metrics.cagr > 0 ? theme.colors.bullish : theme.colors.bearish
              )}
              {renderMetric(
                'Win Rate',
                results.metrics.win_rate.toFixed(1),
                '%'
              )}
              {renderMetric(
                'Sharpe Ratio',
                results.metrics.sharpe_ratio.toFixed(2)
              )}
              {renderMetric(
                'Max Drawdown',
                results.metrics.max_drawdown.toFixed(1),
                '%',
                theme.colors.bearish
              )}
              {renderMetric(
                'Profit Factor',
                results.metrics.profit_factor.toFixed(2)
              )}
            </View>

            <View style={[styles.divider, { backgroundColor: theme.colors.border }]} />

            <View style={styles.metricsRow}>
              {renderMetric('Initial Capital', results.metrics.initial_capital.toLocaleString(), ' SEK')}
              {renderMetric(
                'Final Value',
                results.metrics.final_value.toLocaleString(),
                ' SEK',
                results.metrics.final_value > results.metrics.initial_capital
                  ? theme.colors.bullish
                  : theme.colors.bearish
              )}
            </View>

            <View style={styles.metricsRow}>
              {renderMetric('Total Trades', results.metrics.total_trades)}
              {renderMetric('Winning Trades', results.metrics.winning_trades, '', theme.colors.bullish)}
              {renderMetric('Losing Trades', results.metrics.losing_trades, '', theme.colors.bearish)}
            </View>

            <View style={styles.metricsRow}>
              {renderMetric('Avg Gain', results.metrics.avg_gain.toFixed(1), '%', theme.colors.bullish)}
              {renderMetric('Avg Loss', results.metrics.avg_loss.toFixed(1), '%', theme.colors.bearish)}
            </View>
          </Card>

          {/* Trade Log */}
          <Card variant="elevated">
            <Text style={[styles.sectionTitle, { color: theme.colors.text.primary }]}>
              Trade Log ({results.trades.length} trades)
            </Text>

            <View style={styles.tradeLogHeader}>
              <Text style={[styles.tradeHeaderText, { color: theme.colors.text.secondary }]}>
                Date
              </Text>
              <Text style={[styles.tradeHeaderText, { color: theme.colors.text.secondary }]}>
                Shares
              </Text>
              <Text style={[styles.tradeHeaderText, { color: theme.colors.text.secondary }]}>
                Entry
              </Text>
              <Text style={[styles.tradeHeaderText, { color: theme.colors.text.secondary }]}>
                P/L
              </Text>
              <Text style={[styles.tradeHeaderText, { color: theme.colors.text.secondary }]}>
                %
              </Text>
              <Text style={[styles.tradeHeaderText, { color: theme.colors.text.secondary }]}>
                Reason
              </Text>
            </View>

            {results.trades.map((trade, index) => renderTradeRow(trade, index))}
          </Card>
        </>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  content: {
    padding: 16,
  },
  header: {
    alignItems: 'center',
    marginBottom: 24,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    marginTop: 8,
  },
  subtitle: {
    fontSize: 14,
    marginTop: 4,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 16,
  },
  label: {
    fontSize: 14,
    fontWeight: '500',
    marginTop: 12,
    marginBottom: 6,
  },
  input: {
    borderWidth: 1,
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
  },
  marketButtons: {
    flexDirection: 'row',
    gap: 12,
  },
  marketButton: {
    flex: 1,
    paddingVertical: 12,
    borderRadius: 8,
    borderWidth: 1,
    alignItems: 'center',
  },
  marketButtonText: {
    fontSize: 16,
    fontWeight: '600',
  },
  modeSelector: {
    flexDirection: 'row',
    gap: 8,
  },
  modeButton: {
    flex: 1,
    paddingVertical: 12,
    borderRadius: 8,
    borderWidth: 1,
    alignItems: 'center',
  },
  modeButtonText: {
    fontSize: 12,
    fontWeight: '600',
  },
  loadingContainer: {
    alignItems: 'center',
    paddingVertical: 40,
  },
  loadingText: {
    marginTop: 12,
    fontSize: 14,
  },
  metricsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  metricsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 12,
  },
  metricContainer: {
    width: '48%',
    marginBottom: 16,
  },
  metricLabel: {
    fontSize: 12,
    marginBottom: 4,
  },
  metricValue: {
    fontSize: 20,
    fontWeight: '700',
  },
  divider: {
    height: 1,
    marginVertical: 16,
  },
  tradeLogHeader: {
    flexDirection: 'row',
    paddingVertical: 8,
    borderBottomWidth: 2,
    borderBottomColor: '#e5e7eb',
    marginBottom: 8,
  },
  tradeHeaderText: {
    flex: 1,
    fontSize: 11,
    fontWeight: '600',
    textAlign: 'center',
  },
  tradeRow: {
    flexDirection: 'row',
    paddingVertical: 12,
    borderBottomWidth: 1,
    alignItems: 'center',
  },
  tradeDate: {
    flex: 1.5,
    flexDirection: 'row',
    gap: 4,
    justifyContent: 'center',
  },
  tradeText: {
    flex: 1,
    fontSize: 12,
    textAlign: 'center',
  },
  tradePnL: {
    flex: 1,
    fontSize: 12,
    fontWeight: '600',
    textAlign: 'center',
  },
});
