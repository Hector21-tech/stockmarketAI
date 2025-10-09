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
  TouchableOpacity,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../theme/ThemeContext';
import { Card, PriceText, AddPositionModal } from '../components';
import { api } from '../api/client';

export default function SignalsScreen() {
  const { theme } = useTheme();
  const [signals, setSignals] = useState([]);
  const [loading, setLoading] = useState(false);
  const [signalMode, setSignalMode] = useState('conservative');
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
  const [modalVisible, setModalVisible] = useState(false);
  const [selectedSignal, setSelectedSignal] = useState(null);

  useEffect(() => {
    loadSignalMode();
    fetchSignals();
  }, []);

  const loadSignalMode = async () => {
    try {
      const response = await api.getCurrentSignalMode();
      setSignalMode(response.data.mode);
    } catch (error) {
      console.error('Error loading signal mode:', error);
    }
  };

  const fetchSignals = async () => {
    setLoading(true);
    try {
      // Hämta aktuell signal mode först
      const modeResponse = await api.getCurrentSignalMode();
      const currentMode = modeResponse.data.mode;
      setSignalMode(currentMode);

      // Använd mode för att hämta signaler
      const response = await api.getBuySignals(watchlist, 'SE', currentMode);
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

  const getConfidenceColor = (confidence) => {
    if (confidence >= 80) return theme.colors.bullish;  // Strong green
    if (confidence >= 65) return theme.colors.bullish;  // Green
    if (confidence >= 50) return '#FFA500';  // Orange
    if (confidence >= 35) return '#FF6347';  // Red-orange
    return theme.colors.bearish;  // Red
  };

  const getConfidenceIcon = (confidence) => {
    if (confidence >= 80) return '🟢';
    if (confidence >= 65) return '🟢';
    if (confidence >= 50) return '🟡';
    if (confidence >= 35) return '🟠';
    return '🔴';
  };

  const renderSignalItem = ({ item }) => {
    const { ticker, name, signal, trade_setup, analysis } = item;
    const signalColor = getSignalColor(signal.strength);
    const confidence = signal.confidence || 0;
    const confidenceColor = getConfidenceColor(confidence);
    const confidenceIcon = getConfidenceIcon(confidence);
    const riskFactors = signal.risk_factors || [];
    const recommendedSize = signal.recommended_size || 'full';

    return (
      <Card variant="elevated" style={{ marginBottom: theme.spacing.md }}>
        {/* Header */}
        <View style={styles.header}>
          <View>
            <Text style={[styles.ticker, { color: theme.colors.text.primary, ...theme.typography.styles.h5 }]}>
              {ticker}
            </Text>
            <Text style={[styles.subtitle, { color: theme.colors.text.secondary }]} numberOfLines={1}>
              {name || ticker}
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

        {/* Confidence & Score Badge */}
        <View style={{ marginTop: theme.spacing.md, flexDirection: 'row', alignItems: 'center', gap: theme.spacing.md }}>
          <View style={[styles.scoreBadge, { backgroundColor: theme.colors.alpha(confidenceColor, 0.2), flex: 1 }]}>
            <Text style={[styles.scoreLabel, { color: theme.colors.text.secondary }]}>
              {confidenceIcon} CONFIDENCE
            </Text>
            <Text style={[styles.scoreValue, { color: confidenceColor }]}>
              {confidence.toFixed(0)}%
            </Text>
          </View>

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
        </View>

        {/* Risk Factors Warning */}
        {riskFactors.length > 0 && (
          <View style={[styles.riskWarning, {
            backgroundColor: theme.colors.alpha(theme.colors.bearish, 0.1),
            marginTop: theme.spacing.sm,
            borderLeftColor: theme.colors.bearish,
          }]}>
            <Text style={[styles.riskTitle, { color: theme.colors.bearish }]}>
              ⚠️ Risk Factors
            </Text>
            {riskFactors.map((risk, index) => (
              <Text key={index} style={[styles.riskText, { color: theme.colors.text.secondary }]}>
                • {risk}
              </Text>
            ))}
            <Text style={[styles.riskSize, { color: theme.colors.text.tertiary, marginTop: 4 }]}>
              → Recommended: {recommendedSize === 'full' ? 'Full' : recommendedSize === 'half' ? 'Half (50%)' : recommendedSize === 'quarter' ? 'Quarter (25%)' : 'No'} position
            </Text>
          </View>
        )}

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

        {/* Add to Portfolio Button */}
        <TouchableOpacity
          onPress={() => {
            setSelectedSignal(item);
            setModalVisible(true);
          }}
          style={[styles.addButton, {
            backgroundColor: theme.colors.alpha(theme.colors.primary, 0.1),
            borderColor: theme.colors.primary,
            marginTop: theme.spacing.md,
          }]}
          activeOpacity={0.7}
        >
          <Ionicons name="briefcase-outline" size={20} color={theme.colors.primary} />
          <Text style={[styles.addButtonText, { color: theme.colors.primary }]}>
            Add to Portfolio
          </Text>
        </TouchableOpacity>
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

  const getModeConfig = () => {
    if (signalMode === 'aggressive') {
      return {
        icon: '⚡',
        name: 'Aggressive',
        color: theme.colors.warning || '#FF9800',
        description: 'Tidigt inträde för leverage-produkter',
      };
    }
    return {
      icon: '🛡️',
      name: 'Conservative',
      color: theme.colors.primary,
      description: 'Bekräftade signaler för aktieköp',
    };
  };

  const modeConfig = getModeConfig();

  return (
    <View style={[styles.container, { backgroundColor: theme.colors.background.primary }]}>
      {/* Mode Badge Header */}
      <View style={[styles.modeHeader, { backgroundColor: theme.colors.background.secondary, borderBottomColor: theme.colors.border }]}>
        <View style={{ flexDirection: 'row', alignItems: 'center' }}>
          <Text style={{ fontSize: 18, marginRight: 8 }}>{modeConfig.icon}</Text>
          <View>
            <Text style={[styles.modeName, { color: theme.colors.text.primary }]}>
              Signal Mode: {modeConfig.name}
            </Text>
            <Text style={[styles.modeDescription, { color: theme.colors.text.secondary }]}>
              {modeConfig.description}
            </Text>
          </View>
        </View>
        <View style={[styles.modeBadge, { backgroundColor: modeConfig.color + '20', borderColor: modeConfig.color }]}>
          <Text style={[styles.modeBadgeText, { color: modeConfig.color }]}>
            {signalMode.toUpperCase()}
          </Text>
        </View>
      </View>

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

      {/* Add Position Modal */}
      <AddPositionModal
        visible={modalVisible}
        onClose={() => {
          setModalVisible(false);
          setSelectedSignal(null);
        }}
        mode="from-signal"
        signalData={selectedSignal}
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
  modeHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
  },
  modeName: {
    fontSize: 13,
    fontWeight: '700',
  },
  modeDescription: {
    fontSize: 11,
    marginTop: 2,
  },
  modeBadge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 6,
    borderWidth: 1,
  },
  modeBadgeText: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 0.5,
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
  addButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 10,
    borderWidth: 1.5,
    gap: 8,
  },
  addButtonText: {
    fontSize: 15,
    fontWeight: '700',
  },
  riskWarning: {
    padding: 12,
    borderRadius: 8,
    borderLeftWidth: 3,
  },
  riskTitle: {
    fontSize: 12,
    fontWeight: '700',
    marginBottom: 8,
    letterSpacing: 0.5,
  },
  riskText: {
    fontSize: 12,
    lineHeight: 18,
    marginVertical: 2,
  },
  riskSize: {
    fontSize: 11,
    fontStyle: 'italic',
  },
});
