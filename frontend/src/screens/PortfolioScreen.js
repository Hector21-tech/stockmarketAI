/**
 * Portfolio Analytics Screen
 * Visar portfolio performance, trade history och metrics
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  RefreshControl,
  ActivityIndicator,
} from 'react-native';
import { useTheme } from '../theme/ThemeContext';
import { Card, PriceText } from '../components';
import { api } from '../api/client';

export default function PortfolioScreen() {
  const { theme } = useTheme();
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [analytics, setAnalytics] = useState(null);
  const [tradeHistory, setTradeHistory] = useState([]);

  useEffect(() => {
    loadPortfolioData();
  }, []);

  const loadPortfolioData = async () => {
    try {
      setLoading(true);

      // Load analytics
      const analyticsRes = await api.getPortfolioAnalytics();
      setAnalytics(analyticsRes.data);

      // Load trade history
      const historyRes = await api.getTradeHistory();
      setTradeHistory(historyRes.data.trades || []);

      console.log('📊 Portfolio data loaded');
    } catch (error) {
      console.error('Error loading portfolio data:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const onRefresh = () => {
    setRefreshing(true);
    loadPortfolioData();
  };

  if (loading) {
    return (
      <View style={[styles.loadingContainer, { backgroundColor: theme.colors.background.primary }]}>
        <ActivityIndicator size="large" color={theme.colors.primary} />
        <Text style={[styles.loadingText, { color: theme.colors.text.secondary }]}>
          Loading portfolio data...
        </Text>
      </View>
    );
  }

  return (
    <ScrollView
      style={[styles.container, { backgroundColor: theme.colors.background.primary }]}
      refreshControl={
        <RefreshControl
          refreshing={refreshing}
          onRefresh={onRefresh}
          tintColor={theme.colors.primary}
        />
      }
    >
      {/* Header */}
      <View style={[styles.header, { paddingHorizontal: theme.spacing.base }]}>
        <Text style={[styles.title, { color: theme.colors.text.primary }]}>
          Portfolio Analytics
        </Text>
        <Text style={[styles.subtitle, { color: theme.colors.text.secondary }]}>
          Track your trading performance
        </Text>
      </View>

      {/* Summary Cards */}
      {analytics && (
        <>
          {/* Total P/L Card */}
          <Card style={{ margin: theme.spacing.base }}>
            <Text style={[styles.cardTitle, { color: theme.colors.text.secondary }]}>
              Total Profit/Loss
            </Text>
            <PriceText
              value={analytics.total_pl}
              size="xl"
              suffix=" SEK"
              style={{ marginTop: theme.spacing.xs }}
            />
            <View style={[styles.row, { marginTop: theme.spacing.sm }]}>
              <View style={{ flex: 1 }}>
                <Text style={[styles.label, { color: theme.colors.text.tertiary }]}>
                  Realized
                </Text>
                <PriceText value={analytics.realized_pl} size="md" suffix=" SEK" />
              </View>
              <View style={{ flex: 1, alignItems: 'flex-end' }}>
                <Text style={[styles.label, { color: theme.colors.text.tertiary }]}>
                  Unrealized
                </Text>
                <PriceText value={analytics.unrealized_pl} size="md" suffix=" SEK" />
              </View>
            </View>
          </Card>

          {/* Trading Stats */}
          <View style={[styles.row, { paddingHorizontal: theme.spacing.base, gap: theme.spacing.base }]}>
            <Card style={{ flex: 1 }}>
              <Text style={[styles.cardTitle, { color: theme.colors.text.secondary }]}>
                Win Rate
              </Text>
              <Text style={[styles.bigNumber, { color: theme.colors.bullish, marginTop: theme.spacing.xs }]}>
                {analytics.win_rate}%
              </Text>
              <Text style={[styles.label, { color: theme.colors.text.tertiary, marginTop: theme.spacing.xs }]}>
                {analytics.winning_trades}W / {analytics.losing_trades}L
              </Text>
            </Card>

            <Card style={{ flex: 1 }}>
              <Text style={[styles.cardTitle, { color: theme.colors.text.secondary }]}>
                Total Trades
              </Text>
              <Text style={[styles.bigNumber, { color: theme.colors.text.primary, marginTop: theme.spacing.xs }]}>
                {analytics.total_trades}
              </Text>
              <Text style={[styles.label, { color: theme.colors.text.tertiary, marginTop: theme.spacing.xs }]}>
                {analytics.open_positions_count} open
              </Text>
            </Card>
          </View>

          {/* Performance Metrics */}
          <Card style={{ margin: theme.spacing.base }}>
            <Text style={[styles.cardTitle, { color: theme.colors.text.secondary, marginBottom: theme.spacing.md }]}>
              Performance Metrics
            </Text>

            <View style={[styles.metricRow, { paddingBottom: theme.spacing.sm, borderBottomWidth: 1, borderBottomColor: theme.colors.border.primary }]}>
              <Text style={[styles.metricLabel, { color: theme.colors.text.secondary }]}>
                Average Gain
              </Text>
              <Text style={[styles.metricValue, { color: theme.colors.bullish }]}>
                +{analytics.avg_gain.toFixed(2)}%
              </Text>
            </View>

            <View style={[styles.metricRow, { paddingVertical: theme.spacing.sm, borderBottomWidth: 1, borderBottomColor: theme.colors.border.primary }]}>
              <Text style={[styles.metricLabel, { color: theme.colors.text.secondary }]}>
                Average Loss
              </Text>
              <Text style={[styles.metricValue, { color: theme.colors.bearish }]}>
                {analytics.avg_loss.toFixed(2)}%
              </Text>
            </View>

            <View style={[styles.metricRow, { paddingVertical: theme.spacing.sm, borderBottomWidth: 1, borderBottomColor: theme.colors.border.primary }]}>
              <Text style={[styles.metricLabel, { color: theme.colors.text.secondary }]}>
                Average Trade
              </Text>
              <PriceText
                value={analytics.avg_trade}
                suffix="%"
                style={styles.metricValue}
              />
            </View>

            <View style={[styles.metricRow, { paddingTop: theme.spacing.sm }]}>
              <Text style={[styles.metricLabel, { color: theme.colors.text.secondary }]}>
                Profit Factor
              </Text>
              <Text style={[styles.metricValue, { color: analytics.profit_factor >= 2 ? theme.colors.bullish : theme.colors.text.primary }]}>
                {analytics.profit_factor.toFixed(2)}x
              </Text>
            </View>
          </Card>
        </>
      )}

      {/* Trade History */}
      {tradeHistory.length > 0 && (
        <View style={{ margin: theme.spacing.base }}>
          <Text style={[styles.sectionTitle, { color: theme.colors.text.primary, marginBottom: theme.spacing.sm }]}>
            Trade History
          </Text>
          {tradeHistory.slice(0, 20).map((trade, index) => (
            <Card key={index} style={{ marginBottom: theme.spacing.sm }}>
              <View style={styles.tradeRow}>
                <View style={{ flex: 1 }}>
                  <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
                    <Text style={[styles.tradeTicker, { color: theme.colors.text.primary }]}>
                      {trade.ticker}
                    </Text>
                    <View style={[
                      styles.typeTag,
                      { backgroundColor: trade.type === 'ENTRY' ? theme.colors.alpha(theme.colors.primary, 0.2) : theme.colors.alpha(theme.colors.bearish, 0.2) }
                    ]}>
                      <Text style={[
                        styles.typeTagText,
                        { color: trade.type === 'ENTRY' ? theme.colors.primary : theme.colors.bearish }
                      ]}>
                        {trade.type}
                      </Text>
                    </View>
                  </View>
                  <Text style={[styles.tradeDate, { color: theme.colors.text.tertiary, marginTop: 4 }]}>
                    {new Date(trade.date).toLocaleDateString('sv-SE')}
                  </Text>
                </View>
                <View style={{ alignItems: 'flex-end' }}>
                  <Text style={[styles.tradePrice, { color: theme.colors.text.primary }]}>
                    {trade.shares} @ {trade.price.toFixed(2)} SEK
                  </Text>
                  {trade.pl !== undefined && (
                    <PriceText
                      value={trade.pl}
                      size="sm"
                      suffix={` SEK (${trade.pl_percent.toFixed(2)}%)`}
                      style={{ marginTop: 4 }}
                    />
                  )}
                </View>
              </View>
            </Card>
          ))}
        </View>
      )}

      {/* Empty State */}
      {!analytics || (analytics.total_trades === 0 && tradeHistory.length === 0) && (
        <View style={{ padding: theme.spacing.xl, alignItems: 'center' }}>
          <Text style={[styles.emptyText, { color: theme.colors.text.secondary }]}>
            No trading data yet
          </Text>
          <Text style={[styles.emptySubtext, { color: theme.colors.text.tertiary, marginTop: theme.spacing.xs }]}>
            Start trading to see your portfolio analytics
          </Text>
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 16,
    fontSize: 14,
  },
  header: {
    paddingTop: 16,
    paddingBottom: 8,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
  },
  subtitle: {
    fontSize: 14,
    marginTop: 4,
  },
  cardTitle: {
    fontSize: 12,
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  row: {
    flexDirection: 'row',
  },
  label: {
    fontSize: 12,
  },
  bigNumber: {
    fontSize: 32,
    fontWeight: 'bold',
  },
  metricRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  metricLabel: {
    fontSize: 14,
  },
  metricValue: {
    fontSize: 16,
    fontWeight: '600',
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
  },
  tradeRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  tradeTicker: {
    fontSize: 16,
    fontWeight: '600',
  },
  typeTag: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  typeTagText: {
    fontSize: 10,
    fontWeight: '700',
  },
  tradeDate: {
    fontSize: 12,
  },
  tradePrice: {
    fontSize: 14,
    fontWeight: '500',
  },
  emptyText: {
    fontSize: 16,
    fontWeight: '600',
  },
  emptySubtext: {
    fontSize: 14,
  },
});
