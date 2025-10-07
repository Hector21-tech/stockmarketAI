/**
 * Dashboard Screen
 * Professional trading dashboard with market overview
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  RefreshControl,
  TouchableOpacity,
} from 'react-native';
import { useTheme } from '../theme/ThemeContext';
import { Card, PriceText, Button } from '../components';
import { api } from '../api/client';

export default function DashboardScreen({ navigation }) {
  const { theme } = useTheme();
  const [loading, setLoading] = useState(false);
  const [marketData, setMarketData] = useState(null);
  const [signals, setSignals] = useState([]);
  const [positions, setPositions] = useState([]);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    setLoading(true);
    try {
      // Load market overview
      await loadMarketOverview();

      // Load recent signals
      await loadRecentSignals();

      // Load positions
      await loadPositions();
    } catch (error) {
      console.error('Error loading dashboard:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadMarketOverview = async () => {
    try {
      const tickers = ['VOLVO-B', 'HM-B', 'ERIC-B'];
      const response = await api.getMultipleQuotes(tickers, 'SE');
      const quotesData = response.data.quotes;

      // Fetch stock info (name) for each ticker
      const marketDataWithNames = {};
      for (const ticker of tickers) {
        try {
          const infoResponse = await api.getStockInfo(ticker, 'SE');
          const quote = quotesData[ticker];
          marketDataWithNames[ticker] = {
            price: quote.price,
            change: quote.change,
            changePercent: quote.changePercent,
            name: infoResponse.data.name || ticker,
          };
        } catch (error) {
          const quote = quotesData[ticker];
          marketDataWithNames[ticker] = {
            price: quote.price,
            change: quote.change,
            changePercent: quote.changePercent,
            name: ticker,
          };
        }
      }

      setMarketData(marketDataWithNames);
    } catch (error) {
      console.error('Error loading market data:', error);
    }
  };

  const loadRecentSignals = async () => {
    try {
      const response = await api.getBuySignals(['VOLVO-B', 'HM-B', 'ERIC-B', 'ABB', 'AZN'], 'SE');
      setSignals(response.data.signals.slice(0, 3)); // Top 3
    } catch (error) {
      console.error('Error loading signals:', error);
    }
  };

  const loadPositions = async () => {
    try {
      const response = await api.getPositions();
      setPositions(response.data.positions);
    } catch (error) {
      console.error('Error loading positions:', error);
    }
  };

  const calculatePortfolioStats = () => {
    if (positions.length === 0) {
      return { totalValue: 0, totalPL: 0, totalPLPercent: 0 };
    }

    // Mock calculation - would need current prices for real calculation
    const totalValue = positions.reduce((sum, pos) => sum + (pos.entry_price * pos.current_shares), 0);
    const totalPL = 0; // Would calculate with current prices
    const totalPLPercent = 0;

    return { totalValue, totalPL, totalPLPercent };
  };

  const portfolioStats = calculatePortfolioStats();

  return (
    <ScrollView
      style={[styles.container, { backgroundColor: theme.colors.background.primary }]}
      refreshControl={
        <RefreshControl refreshing={loading} onRefresh={loadDashboardData} />
      }
    >
      {/* Header */}
      <View style={[styles.header, { paddingHorizontal: theme.spacing.base }]}>
        <Text style={[styles.greeting, { color: theme.colors.text.primary, ...theme.typography.styles.h2 }]}>
          Welcome Back
        </Text>
        <Text style={[styles.subtitle, { color: theme.colors.text.secondary, ...theme.typography.styles.body }]}>
          Here's your market overview
        </Text>
      </View>

      {/* Portfolio Summary */}
      <View style={{ paddingHorizontal: theme.spacing.base, marginTop: theme.spacing.base }}>
        <Card variant="elevated">
          <Text style={[styles.cardTitle, { color: theme.colors.text.secondary, ...theme.typography.styles.overline }]}>
            PORTFOLIO VALUE
          </Text>
          <PriceText
            value={portfolioStats.totalValue}
            size="lg"
            prefix="SEK "
            style={{ marginTop: theme.spacing.sm }}
          />
          <View style={{ flexDirection: 'row', marginTop: theme.spacing.sm, alignItems: 'center' }}>
            <PriceText
              value={portfolioStats.totalPL}
              size="sm"
              showChange
              colorize
              prefix="SEK "
            />
            <Text style={{ color: theme.colors.text.tertiary, marginLeft: theme.spacing.xs }}>
              •
            </Text>
            <PriceText
              value={portfolioStats.totalPLPercent}
              size="sm"
              showChange
              colorize
              suffix="%"
              style={{ marginLeft: theme.spacing.xs }}
            />
          </View>
        </Card>
      </View>

      {/* Quick Stats */}
      <View style={[styles.statsGrid, { paddingHorizontal: theme.spacing.base, marginTop: theme.spacing.base }]}>
        <Card variant="elevated" style={styles.statCard}>
          <Text style={[styles.statLabel, { color: theme.colors.text.secondary }]}>
            Active Positions
          </Text>
          <Text style={[styles.statValue, { color: theme.colors.primary, ...theme.typography.styles.h3 }]}>
            {positions.length}
          </Text>
        </Card>

        <Card variant="elevated" style={styles.statCard}>
          <Text style={[styles.statLabel, { color: theme.colors.text.secondary }]}>
            Buy Signals
          </Text>
          <Text style={[styles.statValue, { color: theme.colors.bullish, ...theme.typography.styles.h3 }]}>
            {signals.length}
          </Text>
        </Card>
      </View>

      {/* Market Overview */}
      <View style={{ paddingHorizontal: theme.spacing.base, marginTop: theme.spacing.xl }}>
        <View style={styles.sectionHeader}>
          <Text style={[styles.sectionTitle, { color: theme.colors.text.primary, ...theme.typography.styles.h4 }]}>
            Market Overview
          </Text>
          <TouchableOpacity onPress={() => navigation.navigate('Watchlist')}>
            <Text style={[styles.seeAll, { color: theme.colors.primary }]}>
              See All
            </Text>
          </TouchableOpacity>
        </View>

        {marketData && Object.keys(marketData).map((ticker) => (
          <TouchableOpacity
            key={ticker}
            onPress={() => navigation.navigate('Watchlist')}
          >
            <Card variant="default" style={{ marginTop: theme.spacing.sm }}>
              <View style={styles.stockRow}>
                <View style={{ flex: 1 }}>
                  <Text style={[styles.ticker, { color: theme.colors.text.primary, ...theme.typography.styles.h6 }]}>
                    {ticker}
                  </Text>
                  <Text style={[styles.stockName, { color: theme.colors.text.tertiary }]} numberOfLines={1}>
                    {marketData[ticker]?.name || ticker}
                  </Text>
                </View>
                <View style={{ alignItems: 'flex-end' }}>
                  <PriceText value={marketData[ticker]?.price || marketData[ticker]} size="md" suffix=" SEK" />
                  <PriceText
                    value={marketData[ticker]?.changePercent || 0}
                    size="sm"
                    showChange
                    colorize
                    suffix="%"
                    style={{ marginTop: theme.spacing.xs }}
                  />
                </View>
              </View>
            </Card>
          </TouchableOpacity>
        ))}
      </View>

      {/* Recent Signals */}
      <View style={{ paddingHorizontal: theme.spacing.base, marginTop: theme.spacing.xl }}>
        <View style={styles.sectionHeader}>
          <Text style={[styles.sectionTitle, { color: theme.colors.text.primary, ...theme.typography.styles.h4 }]}>
            Recent Signals
          </Text>
          <TouchableOpacity onPress={() => navigation.navigate('Signals')}>
            <Text style={[styles.seeAll, { color: theme.colors.primary }]}>
              See All
            </Text>
          </TouchableOpacity>
        </View>

        {signals.length > 0 ? (
          signals.map((signal, index) => (
            <Card key={index} variant="default" style={{ marginTop: theme.spacing.sm }}>
              <View style={styles.signalRow}>
                <View style={{ flex: 1 }}>
                  <Text style={[styles.ticker, { color: theme.colors.text.primary, ...theme.typography.styles.h6 }]}>
                    {signal.ticker}
                  </Text>
                  <Text style={[styles.signalType, { color: theme.colors.bullish }]}>
                    {signal.signal.action} • {signal.signal.strength}
                  </Text>
                </View>
                <View style={[styles.scoreBadge, { backgroundColor: theme.colors.alpha(theme.colors.bullish, 0.2) }]}>
                  <Text style={[styles.scoreText, { color: theme.colors.bullish }]}>
                    {signal.signal.score}
                  </Text>
                </View>
              </View>
            </Card>
          ))
        ) : (
          <Card variant="default" style={{ marginTop: theme.spacing.sm }}>
            <Text style={[styles.emptyText, { color: theme.colors.text.tertiary }]}>
              No buy signals at the moment
            </Text>
          </Card>
        )}
      </View>

      {/* Quick Actions */}
      <View style={{ paddingHorizontal: theme.spacing.base, marginTop: theme.spacing.xl, marginBottom: theme.spacing.xl }}>
        <Text style={[styles.sectionTitle, { color: theme.colors.text.primary, ...theme.typography.styles.h4, marginBottom: theme.spacing.md }]}>
          Quick Actions
        </Text>
        <View style={styles.actionsGrid}>
          <Button onPress={() => navigation.navigate('Signals')} style={styles.actionButton}>
            View Signals
          </Button>
          <Button
            variant="outline"
            onPress={() => navigation.navigate('Positions')}
            style={styles.actionButton}
          >
            Positions
          </Button>
        </View>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    paddingTop: 20,
    paddingBottom: 16,
  },
  greeting: {
    marginBottom: 4,
  },
  subtitle: {

  },
  cardTitle: {

  },
  statsGrid: {
    flexDirection: 'row',
    gap: 12,
  },
  statCard: {
    flex: 1,
  },
  statLabel: {
    fontSize: 12,
    marginBottom: 8,
  },
  statValue: {

  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  sectionTitle: {

  },
  seeAll: {
    fontSize: 14,
    fontWeight: '600',
  },
  stockRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  ticker: {

  },
  stockName: {
    fontSize: 12,
    marginTop: 2,
  },
  signalRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  signalType: {
    fontSize: 12,
    marginTop: 4,
    fontWeight: '600',
  },
  scoreBadge: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
  },
  scoreText: {
    fontSize: 16,
    fontWeight: '700',
  },
  emptyText: {
    textAlign: 'center',
    padding: 20,
  },
  actionsGrid: {
    flexDirection: 'row',
    gap: 12,
  },
  actionButton: {
    flex: 1,
  },
});
