/**
 * Signals Screen
 * Professional buy signal analysis with MarketMate strategy
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  FlatList,
  StyleSheet,
  RefreshControl,
  Alert,
  ActivityIndicator,
  ScrollView,
} from 'react-native';
import { useTheme } from '../theme/ThemeContext';
import { Card, PriceText } from '../components';
import { api } from '../api/client';

export default function SignalsScreen() {
  const { theme } = useTheme();
  const [signals, setSignals] = useState([]);
  const [loading, setLoading] = useState(false);
  const [watchlist] = useState([
    'VOLVO-B',
    'HM-B',
    'ERIC-B',
    'ABB',
    'AZN',
    'SINCH',
    'SKF-B',
    'TELIA',
  ]);

  useEffect(() => {
    fetchSignals();
  }, []);

  const fetchSignals = async () => {
    setLoading(true);
    try {
      const response = await api.getBuySignals(watchlist, 'SE');
      setSignals(response.data.signals || []);
    } catch (error) {
      console.error('Error fetching signals:', error);
      Alert.alert('Fel', 'Kunde inte hämta signaler');
    } finally {
      setLoading(false);
    }
  };

  const getSignalColor = (strength) => {
    switch (strength) {
      case 'STRONG':
        return theme.colors.bullish;
      case 'MODERATE':
        return theme.colors.warning || '#FF9800';
      default:
        return theme.colors.text.tertiary;
    }
  };

  const renderSignalItem = ({ item }) => {
    const { ticker, signal, trade_setup, analysis } = item;
    const signalColor = getSignalColor(signal.strength);

    return (
      <Card variant="elevated" style={{ marginBottom: theme.spacing.md }}>
        {/* Header */}
        <View style={styles.header}>
          <View>
            <Text style={[styles.ticker, { color: theme.colors.text.primary, ...theme.typography.styles.h5 }]}>
              {ticker}
            </Text>
            <Text style={[styles.subtitle, { color: theme.colors.text.secondary }]}>
              Swedish Stock
            </Text>
          </View>
          <View style={[styles.signalBadge, { backgroundColor: theme.colors.alpha(signalColor, 0.2) }]}>
            <Text style={[styles.signalText, { color: signalColor }]}>
              {signal.action}
            </Text>
          </View>
        </View>

        {/* Price */}
        <View style={{ marginTop: theme.spacing.sm }}>
          <PriceText
            value={analysis.price}
            size="lg"
            suffix=" SEK"
          />
        </View>

        {/* Score Badge */}
        <View style={{ marginTop: theme.spacing.md, flexDirection: 'row', alignItems: 'center', gap: theme.spacing.md }}>
          <View style={[styles.scoreBadge, { backgroundColor: theme.colors.alpha(signalColor, 0.2) }]}>
            <Text style={[styles.scoreLabel, { color: theme.colors.text.secondary }]}>
              SCORE
            </Text>
            <Text style={[styles.scoreValue, { color: signalColor }]}>
              {signal.score}
            </Text>
          </View>

          <View style={[styles.scoreBadge, { backgroundColor: theme.colors.alpha(theme.colors.primary, 0.1) }]}>
            <Text style={[styles.scoreLabel, { color: theme.colors.text.secondary }]}>
              RSI
            </Text>
            <Text style={[styles.scoreValue, { color: theme.colors.primary }]}>
              {analysis.rsi.toFixed(1)}
            </Text>
          </View>

          <View style={[styles.scoreBadge, { backgroundColor: theme.colors.alpha(signalColor, 0.2) }]}>
            <Text style={[styles.scoreLabel, { color: theme.colors.text.secondary }]}>
              STRENGTH
            </Text>
            <Text style={[styles.scoreValue, { color: signalColor, fontSize: 10 }]}>
              {signal.strength}
            </Text>
          </View>
        </View>

        {/* Summary */}
        <Text style={[styles.summary, { color: theme.colors.text.primary, marginTop: theme.spacing.md }]}>
          {signal.summary}
        </Text>

        {/* Trade Setup */}
        {trade_setup.entry && (
          <View style={[styles.tradeSetup, {
            backgroundColor: theme.colors.alpha(theme.colors.primary, 0.1),
            borderLeftColor: theme.colors.primary,
            marginTop: theme.spacing.md,
          }]}>
            <Text style={[styles.setupTitle, { color: theme.colors.primary }]}>
              TRADE SETUP
            </Text>

            <View style={styles.setupGrid}>
              <View style={styles.setupItem}>
                <Text style={[styles.setupLabel, { color: theme.colors.text.secondary }]}>
                  Entry
                </Text>
                <PriceText value={trade_setup.entry} size="sm" suffix=" SEK" />
              </View>

              <View style={styles.setupItem}>
                <Text style={[styles.setupLabel, { color: theme.colors.text.secondary }]}>
                  Stop Loss
                </Text>
                <PriceText value={trade_setup.stop_loss} size="sm" suffix=" SEK" colorize />
              </View>
            </View>

            <View style={[styles.setupGrid, { marginTop: theme.spacing.sm }]}>
              <View style={styles.setupItem}>
                <Text style={[styles.setupLabel, { color: theme.colors.text.secondary }]}>
                  Target 1
                </Text>
                <PriceText value={trade_setup.targets.target_1.price} size="sm" suffix=" SEK" />
                <Text style={[styles.gainText, { color: theme.colors.bullish }]}>
                  +{trade_setup.targets.target_1.gain_percent}%
                </Text>
              </View>

              <View style={styles.setupItem}>
                <Text style={[styles.setupLabel, { color: theme.colors.text.secondary }]}>
                  Target 2
                </Text>
                <PriceText value={trade_setup.targets.target_2.price} size="sm" suffix=" SEK" />
                <Text style={[styles.gainText, { color: theme.colors.bullish }]}>
                  +{trade_setup.targets.target_2.gain_percent}%
                </Text>
              </View>
            </View>
          </View>
        )}

        {/* Reasons */}
        <View style={{ marginTop: theme.spacing.md }}>
          <Text style={[styles.reasonsTitle, { color: theme.colors.text.secondary }]}>
            ANALYSIS REASONS
          </Text>
          {signal.reasons.map((reason, index) => (
            <View key={index} style={styles.reasonRow}>
              <Text style={[styles.bullet, { color: theme.colors.primary }]}>•</Text>
              <Text style={[styles.reason, { color: theme.colors.text.primary }]}>
                {reason}
              </Text>
            </View>
          ))}
        </View>
      </Card>
    );
  };

  if (loading && signals.length === 0) {
    return (
      <View style={[styles.loadingContainer, { backgroundColor: theme.colors.background.primary }]}>
        <ActivityIndicator size="large" color={theme.colors.primary} />
        <Text style={[styles.loadingText, { color: theme.colors.text.secondary }]}>
          Skannar watchlist...
        </Text>
      </View>
    );
  }

  return (
    <View style={[styles.container, { backgroundColor: theme.colors.background.primary }]}>
      <FlatList
        data={signals}
        renderItem={renderSignalItem}
        keyExtractor={(item) => item.ticker}
        contentContainerStyle={{
          padding: theme.spacing.base,
          paddingBottom: theme.spacing.xl,
        }}
        refreshControl={
          <RefreshControl
            refreshing={loading}
            onRefresh={fetchSignals}
            tintColor={theme.colors.primary}
          />
        }
        ListEmptyComponent={
          <Card variant="default" style={{ marginTop: theme.spacing.xl, alignItems: 'center', padding: theme.spacing.xl }}>
            <Text style={[styles.emptyText, { color: theme.colors.text.secondary }]}>
              Inga köpsignaler just nu
            </Text>
            <Text style={[styles.emptySubtext, { color: theme.colors.text.tertiary }]}>
              Dra ner för att uppdatera
            </Text>
          </Card>
        }
      />
    </View>
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
    fontSize: 16,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  ticker: {
    marginBottom: 2,
  },
  subtitle: {
    fontSize: 12,
  },
  signalBadge: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
  },
  signalText: {
    fontWeight: '700',
    fontSize: 12,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  scoreBadge: {
    flex: 1,
    padding: 8,
    borderRadius: 8,
    alignItems: 'center',
  },
  scoreLabel: {
    fontSize: 10,
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 4,
  },
  scoreValue: {
    fontSize: 16,
    fontWeight: '700',
  },
  summary: {
    fontSize: 14,
    lineHeight: 20,
    fontStyle: 'italic',
  },
  tradeSetup: {
    padding: 12,
    borderRadius: 8,
    borderLeftWidth: 3,
  },
  setupTitle: {
    fontSize: 12,
    fontWeight: '700',
    letterSpacing: 0.5,
    marginBottom: 12,
  },
  setupGrid: {
    flexDirection: 'row',
    gap: 12,
  },
  setupItem: {
    flex: 1,
  },
  setupLabel: {
    fontSize: 11,
    fontWeight: '600',
    marginBottom: 4,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  gainText: {
    fontSize: 11,
    fontWeight: '600',
    marginTop: 2,
  },
  reasonsTitle: {
    fontSize: 11,
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 8,
  },
  reasonRow: {
    flexDirection: 'row',
    marginVertical: 4,
  },
  bullet: {
    marginRight: 8,
    fontWeight: 'bold',
  },
  reason: {
    flex: 1,
    fontSize: 13,
    lineHeight: 18,
  },
  emptyText: {
    fontSize: 16,
    marginBottom: 8,
  },
  emptySubtext: {
    fontSize: 14,
  },
});
