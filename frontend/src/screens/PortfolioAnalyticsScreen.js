/**
 * Portfolio Analytics Screen
 * Track overall portfolio performance with P/L, win rate, and trade history
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  FlatList,
  StyleSheet,
  RefreshControl,
  ScrollView,
  TouchableOpacity,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../theme/ThemeContext';
import { Card, PriceText } from '../components';
import { api } from '../api/client';

export default function PortfolioAnalyticsScreen() {
  const { theme } = useTheme();
  const [analytics, setAnalytics] = useState(null);
  const [tradeHistory, setTradeHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [filter, setFilter] = useState('all'); // all, winners, losers

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [analyticsResponse, historyResponse] = await Promise.all([
        api.getPortfolioAnalytics(),
        api.getTradeHistory(),
      ]);
      setAnalytics(analyticsResponse.data);
      setTradeHistory(historyResponse.data.trades || []);
    } catch (error) {
      console.error('Error fetching portfolio analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  const getFilteredTrades = () => {
    if (filter === 'winners') {
      return tradeHistory.filter(trade => trade.total_pnl > 0);
    } else if (filter === 'losers') {
      return tradeHistory.filter(trade => trade.total_pnl < 0);
    }
    return tradeHistory;
  };

  const renderSummaryCard = (title, value, subtitle, icon, color) => (
    <Card variant="elevated" style={[styles.summaryCard, { backgroundColor: theme.colors.background.secondary }]}>
      <View style={styles.summaryHeader}>
        <Ionicons name={icon} size={24} color={color || theme.colors.primary} />
      </View>
      <Text style={[styles.summaryTitle, { color: theme.colors.text.secondary }]}>
        {title}
      </Text>
      <Text style={[styles.summaryValue, { color: theme.colors.text.primary, ...theme.typography.styles.h3 }]}>
        {value}
      </Text>
      {subtitle && (
        <Text style={[styles.summarySubtitle, { color: theme.colors.text.tertiary }]}>
          {subtitle}
        </Text>
      )}
    </Card>
  );

  const renderTradeItem = ({ item }) => {
    const isProfit = item.total_pnl > 0;
    const pnlColor = isProfit ? theme.colors.bullish : theme.colors.bearish;

    return (
      <Card variant="elevated" style={{ marginBottom: theme.spacing.md }}>
        {/* Header */}
        <View style={styles.tradeHeader}>
          <View style={{ flex: 1 }}>
            <Text style={[styles.tradeTicker, { color: theme.colors.text.primary, ...theme.typography.styles.h5 }]}>
              {item.ticker}
            </Text>
            <Text style={[styles.tradeDate, { color: theme.colors.text.tertiary }]}>
              {new Date(item.entry_date).toLocaleDateString('sv-SE')} → {new Date(item.exit_date).toLocaleDateString('sv-SE')}
            </Text>
          </View>
          <View style={[styles.pnlBadge, { backgroundColor: theme.colors.alpha(pnlColor, 0.1) }]}>
            <PriceText
              value={item.total_pnl}
              size="md"
              showChange
              colorize
              suffix=" kr"
            />
          </View>
        </View>

        {/* Details */}
        <View style={[styles.tradeDetails, { marginTop: theme.spacing.md }]}>
          <View style={styles.detailRow}>
            <Text style={[styles.detailLabel, { color: theme.colors.text.secondary }]}>
              Entry Price
            </Text>
            <PriceText value={item.entry_price} size="sm" suffix=" kr" />
          </View>
          <View style={styles.detailRow}>
            <Text style={[styles.detailLabel, { color: theme.colors.text.secondary }]}>
              Shares
            </Text>
            <Text style={[styles.detailValue, { color: theme.colors.text.primary }]}>
              {item.shares}
            </Text>
          </View>
          <View style={styles.detailRow}>
            <Text style={[styles.detailLabel, { color: theme.colors.text.secondary }]}>
              Return
            </Text>
            <PriceText
              value={item.total_pnl_percent}
              size="sm"
              showChange
              colorize
              suffix="%"
            />
          </View>
        </View>

        {/* Exits */}
        {item.exits && item.exits.length > 0 && (
          <View style={[styles.exitsSection, {
            borderTopColor: theme.colors.border.primary,
            marginTop: theme.spacing.md,
            paddingTop: theme.spacing.md,
          }]}>
            <Text style={[styles.exitsTitle, { color: theme.colors.text.secondary }]}>
              EXITS ({item.exits.length})
            </Text>
            {item.exits.map((exit, index) => (
              <View key={index} style={[styles.exitRow, { marginTop: theme.spacing.xs }]}>
                <Text style={[styles.exitText, { color: theme.colors.text.primary }]}>
                  {exit.shares} @ {exit.price} kr
                </Text>
                <PriceText
                  value={exit.profit_percent}
                  size="xs"
                  showChange
                  colorize
                  suffix="%"
                />
              </View>
            ))}
          </View>
        )}
      </Card>
    );
  };

  if (!analytics) {
    return (
      <View style={[styles.container, { backgroundColor: theme.colors.background.primary }]}>
        <View style={[styles.loadingContainer, { justifyContent: 'center', alignItems: 'center' }]}>
          <Text style={[styles.loadingText, { color: theme.colors.text.secondary }]}>
            Loading analytics...
          </Text>
        </View>
      </View>
    );
  }

  const { pnl, win_rate, metrics, open_positions } = analytics;
  const filteredTrades = getFilteredTrades();

  return (
    <View style={[styles.container, { backgroundColor: theme.colors.background.primary }]}>
      <ScrollView
        refreshControl={
          <RefreshControl
            refreshing={loading}
            onRefresh={fetchData}
            tintColor={theme.colors.primary}
          />
        }
      >
        {/* Summary Cards */}
        <View style={[styles.summarySection, { padding: theme.spacing.base }]}>
          <Text style={[styles.sectionTitle, { color: theme.colors.text.primary, ...theme.typography.styles.h4 }]}>
            Portfolio Overview
          </Text>

          <View style={[styles.summaryGrid, { marginTop: theme.spacing.md }]}>
            {renderSummaryCard(
              'Total P/L',
              `${pnl.total_pnl >= 0 ? '+' : ''}${pnl.total_pnl} kr`,
              `Realized: ${pnl.realized_pnl} kr`,
              'trending-up',
              pnl.total_pnl >= 0 ? theme.colors.bullish : theme.colors.bearish
            )}
            {renderSummaryCard(
              'Win Rate',
              `${win_rate.win_rate}%`,
              `${win_rate.winning_trades}/${win_rate.total_trades} trades`,
              'trophy',
              theme.colors.primary
            )}
          </View>

          <View style={[styles.summaryGrid, { marginTop: theme.spacing.md }]}>
            {renderSummaryCard(
              'Best Trade',
              `+${metrics.best_trade} kr`,
              null,
              'arrow-up-circle',
              theme.colors.bullish
            )}
            {renderSummaryCard(
              'Worst Trade',
              `${metrics.worst_trade} kr`,
              null,
              'arrow-down-circle',
              theme.colors.bearish
            )}
          </View>

          <View style={[styles.summaryGrid, { marginTop: theme.spacing.md }]}>
            {renderSummaryCard(
              'Avg Gain',
              `+${metrics.avg_gain} kr`,
              null,
              'trending-up',
              theme.colors.bullish
            )}
            {renderSummaryCard(
              'Avg Loss',
              `${metrics.avg_loss} kr`,
              null,
              'trending-down',
              theme.colors.bearish
            )}
          </View>
        </View>

        {/* Open Positions Summary */}
        {open_positions && open_positions.length > 0 && (
          <View style={[styles.openPositionsSection, {
            backgroundColor: theme.colors.alpha(theme.colors.primary, 0.05),
            padding: theme.spacing.base,
            marginTop: theme.spacing.md,
          }]}>
            <Text style={[styles.sectionTitle, { color: theme.colors.text.primary, ...theme.typography.styles.h5 }]}>
              Open Positions ({open_positions.length})
            </Text>
            <View style={[styles.openPositionsList, { marginTop: theme.spacing.sm }]}>
              {open_positions.map((position, index) => (
                <View key={index} style={[styles.openPositionItem, {
                  borderBottomColor: theme.colors.border.primary,
                  borderBottomWidth: index < open_positions.length - 1 ? 1 : 0,
                  paddingVertical: theme.spacing.sm,
                }]}>
                  <Text style={[styles.openPositionTicker, { color: theme.colors.text.primary }]}>
                    {position.ticker}
                  </Text>
                  <PriceText
                    value={position.unrealized_pnl_percent}
                    size="sm"
                    showChange
                    colorize
                    suffix="%"
                  />
                </View>
              ))}
            </View>
          </View>
        )}

        {/* Trade History */}
        <View style={[styles.historySection, { padding: theme.spacing.base, marginTop: theme.spacing.md }]}>
          <View style={styles.historyHeader}>
            <Text style={[styles.sectionTitle, { color: theme.colors.text.primary, ...theme.typography.styles.h5 }]}>
              Trade History
            </Text>
            <View style={styles.filterButtons}>
              {['all', 'winners', 'losers'].map((filterOption) => (
                <TouchableOpacity
                  key={filterOption}
                  onPress={() => setFilter(filterOption)}
                  style={[
                    styles.filterButton,
                    {
                      backgroundColor: filter === filterOption
                        ? theme.colors.primary
                        : theme.colors.alpha(theme.colors.primary, 0.1),
                      borderColor: theme.colors.primary,
                      borderWidth: 1,
                    },
                  ]}
                >
                  <Text
                    style={[
                      styles.filterButtonText,
                      {
                        color: filter === filterOption
                          ? '#fff'
                          : theme.colors.primary,
                      },
                    ]}
                  >
                    {filterOption === 'all' ? 'All' : filterOption === 'winners' ? 'Winners' : 'Losers'}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>

          {filteredTrades.length > 0 ? (
            <View style={{ marginTop: theme.spacing.md }}>
              {filteredTrades.map((trade, index) => (
                <View key={`${trade.ticker}-${trade.exit_date}-${index}`}>
                  {renderTradeItem({ item: trade })}
                </View>
              ))}
            </View>
          ) : (
            <Card variant="default" style={{ marginTop: theme.spacing.md, alignItems: 'center', padding: theme.spacing.xl }}>
              <Ionicons name="file-tray-outline" size={48} color={theme.colors.text.tertiary} />
              <Text style={[styles.emptyText, { color: theme.colors.text.secondary, marginTop: theme.spacing.md }]}>
                {filter === 'all' ? 'Ingen trade history än' : `Inga ${filter === 'winners' ? 'vinnande' : 'förlorande'} trades`}
              </Text>
            </Card>
          )}
        </View>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  loadingContainer: {
    flex: 1,
  },
  loadingText: {
    fontSize: 16,
  },
  summarySection: {},
  sectionTitle: {
    marginBottom: 8,
  },
  summaryGrid: {
    flexDirection: 'row',
    gap: 12,
  },
  summaryCard: {
    flex: 1,
    padding: 16,
    borderRadius: 12,
  },
  summaryHeader: {
    marginBottom: 8,
  },
  summaryTitle: {
    fontSize: 11,
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 4,
  },
  summaryValue: {
    marginBottom: 4,
  },
  summarySubtitle: {
    fontSize: 12,
  },
  openPositionsSection: {
    borderRadius: 8,
  },
  openPositionsList: {},
  openPositionItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  openPositionTicker: {
    fontSize: 14,
    fontWeight: '600',
  },
  historySection: {},
  historyHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  filterButtons: {
    flexDirection: 'row',
    gap: 8,
  },
  filterButton: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
  },
  filterButtonText: {
    fontSize: 12,
    fontWeight: '600',
  },
  tradeHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  tradeTicker: {
    marginBottom: 2,
  },
  tradeDate: {
    fontSize: 12,
  },
  pnlBadge: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
  },
  tradeDetails: {
    gap: 8,
  },
  detailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  detailLabel: {
    fontSize: 12,
    fontWeight: '600',
  },
  detailValue: {
    fontSize: 14,
  },
  exitsSection: {
    borderTopWidth: 1,
  },
  exitsTitle: {
    fontSize: 11,
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 4,
  },
  exitRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  exitText: {
    fontSize: 12,
  },
  emptyText: {
    fontSize: 16,
  },
});
