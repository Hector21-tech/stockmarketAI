/**
 * Positions Screen
 * Track open positions with 1/3-exit rule management
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  FlatList,
  StyleSheet,
  RefreshControl,
  Alert,
  ScrollView,
  TouchableOpacity,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../theme/ThemeContext';
import { Card, PriceText, AddPositionModal } from '../components';
import { api } from '../api/client';

export default function PositionsScreen({ navigation }) {
  const { theme } = useTheme();
  const [positions, setPositions] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [lastChecked, setLastChecked] = useState(null);

  useEffect(() => {
    fetchPositions();
    checkPositions();
  }, []);

  const fetchPositions = async () => {
    setLoading(true);
    try {
      const response = await api.getPositions();
      setPositions(response.data.positions || []);
    } catch (error) {
      console.error('Error fetching positions:', error);
    } finally {
      setLoading(false);
    }
  };

  const checkPositions = async () => {
    try {
      const response = await api.checkPositions();
      const newNotifications = response.data.notifications || [];
      const lastCheck = response.data.last_checked || {};

      setLastChecked(lastCheck);

      if (newNotifications.length > 0) {
        setNotifications(newNotifications);
        // Show first notification
        const notif = newNotifications[0];
        Alert.alert(
          `${notif.type}: ${notif.ticker}`,
          notif.action,
          [{ text: 'OK' }]
        );
      }
    } catch (error) {
      console.error('Error checking positions:', error);
    }
  };

  const refresh = () => {
    fetchPositions();
    checkPositions();
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'OPEN':
        return theme.colors.bullish;
      case 'PARTIAL':
        return theme.colors.warning || '#FF9800';
      case 'CLOSED':
        return theme.colors.text.tertiary;
      default:
        return theme.colors.text.tertiary;
    }
  };

  const getTimeAgo = (isoString) => {
    if (!isoString) return 'Aldrig';
    const date = new Date(isoString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);

    if (diffMins < 1) return 'Just nu';
    if (diffMins === 1) return '1 min sedan';
    if (diffMins < 60) return `${diffMins} min sedan`;

    const diffHours = Math.floor(diffMins / 60);
    if (diffHours === 1) return '1 timme sedan';
    if (diffHours < 24) return `${diffHours} timmar sedan';

    const diffDays = Math.floor(diffHours / 24);
    if (diffDays === 1) return '1 dag sedan';
    return `${diffDays} dagar sedan`;
  };

  const renderPositionItem = ({ item }) => {
    const statusColor = getStatusColor(item.status);

    return (
      <Card variant="elevated" style={{ marginBottom: theme.spacing.md }}>
        {/* Header */}
        <View style={styles.header}>
          <View>
            <Text style={[styles.ticker, { color: theme.colors.text.primary, ...theme.typography.styles.h5 }]}>
              {item.ticker}
            </Text>
            <Text style={[styles.subtitle, { color: theme.colors.text.secondary }]}>
              {item.current_shares} aktier
            </Text>
          </View>
          <View style={[styles.statusBadge, { backgroundColor: theme.colors.alpha(statusColor, 0.2) }]}>
            <Text style={[styles.statusText, { color: statusColor }]}>
              {item.status}
            </Text>
          </View>
        </View>

        {/* Prices */}
        <View style={[styles.pricesRow, { marginTop: theme.spacing.md }]}>
          <View style={{ flex: 1 }}>
            <Text style={[styles.priceLabel, { color: theme.colors.text.secondary }]}>
              Entry Price
            </Text>
            <PriceText value={item.entry_price} size="md" suffix=" SEK" />
          </View>

          {item.current_price && (
            <View style={{ flex: 1 }}>
              <Text style={[styles.priceLabel, { color: theme.colors.text.secondary }]}>
                Current Price
              </Text>
              <PriceText value={item.current_price} size="md" suffix=" SEK" />
            </View>
          )}
        </View>

        {/* P/L */}
        {item.current_price && (
          <View style={[styles.plSection, {
            backgroundColor: theme.colors.alpha(
              item.unrealized_percent > 0 ? theme.colors.bullish : theme.colors.bearish,
              0.1
            ),
            marginTop: theme.spacing.md,
          }]}>
            <View style={{ flex: 1 }}>
              <Text style={[styles.plLabel, { color: theme.colors.text.secondary }]}>
                UNREALIZED P/L
              </Text>
              <View style={{ flexDirection: 'row', alignItems: 'baseline', gap: theme.spacing.xs }}>
                <PriceText
                  value={item.unrealized_profit}
                  size="lg"
                  showChange
                  colorize
                  suffix=" SEK"
                />
                <PriceText
                  value={item.unrealized_percent}
                  size="md"
                  showChange
                  colorize
                  suffix="%"
                  style={{ marginLeft: theme.spacing.sm }}
                />
              </View>
            </View>
          </View>
        )}

        {/* Stop Loss */}
        <View style={[styles.row, { marginTop: theme.spacing.md }]}>
          <Text style={[styles.label, { color: theme.colors.text.secondary }]}>
            Stop Loss
          </Text>
          <PriceText value={item.stop_loss} size="sm" suffix=" SEK" />
        </View>

        {/* Targets */}
        {item.targets && (
          <View style={[styles.targetsSection, {
            backgroundColor: theme.colors.alpha(theme.colors.bullish, 0.1),
            borderLeftColor: theme.colors.bullish,
            marginTop: theme.spacing.md,
          }]}>
            <Text style={[styles.targetsTitle, { color: theme.colors.bullish }]}>
              PRICE TARGETS (1/3 exits)
            </Text>

            <View style={styles.targetsGrid}>
              <View style={styles.targetItem}>
                <Text style={[styles.targetLabel, { color: theme.colors.text.secondary }]}>
                  Target 1
                </Text>
                <PriceText value={item.targets.target_1.price} size="sm" suffix=" SEK" />
                <Text style={[styles.gainText, { color: theme.colors.bullish }]}>
                  +{item.targets.target_1.gain_percent.toFixed(1)}%
                </Text>
              </View>

              <View style={styles.targetItem}>
                <Text style={[styles.targetLabel, { color: theme.colors.text.secondary }]}>
                  Target 2
                </Text>
                <PriceText value={item.targets.target_2.price} size="sm" suffix=" SEK" />
                <Text style={[styles.gainText, { color: theme.colors.bullish }]}>
                  +{item.targets.target_2.gain_percent.toFixed(1)}%
                </Text>
              </View>

              <View style={styles.targetItem}>
                <Text style={[styles.targetLabel, { color: theme.colors.text.secondary }]}>
                  Target 3
                </Text>
                <PriceText value={item.targets.target_3.price} size="sm" suffix=" SEK" />
                <Text style={[styles.gainText, { color: theme.colors.bullish }]}>
                  +{item.targets.target_3.gain_percent.toFixed(1)}%
                </Text>
              </View>
            </View>
          </View>
        )}

        {/* Exits */}
        {item.exits && item.exits.length > 0 && (
          <View style={[styles.exitsSection, {
            borderTopColor: theme.colors.border.primary,
            marginTop: theme.spacing.md,
            paddingTop: theme.spacing.md,
          }]}>
            <Text style={[styles.exitsTitle, { color: theme.colors.text.secondary }]}>
              EXIT HISTORY
            </Text>
            {item.exits.map((exit, index) => (
              <View key={index} style={[styles.exitRow, { marginTop: theme.spacing.xs }]}>
                <View style={{ flex: 1 }}>
                  <Text style={[styles.exitText, { color: theme.colors.text.primary }]}>
                    {exit.shares} shares @ {exit.price} SEK
                  </Text>
                  <Text style={[styles.exitType, { color: theme.colors.text.tertiary }]}>
                    {exit.type}
                  </Text>
                </View>
                <PriceText
                  value={exit.profit_percent}
                  size="sm"
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

  const renderNotificationItem = ({ item }) => (
    <Card
      variant="elevated"
      style={[styles.notificationCard, {
        borderLeftColor: theme.colors.warning || '#FF9800',
      }]}
    >
      <View style={styles.notifHeader}>
        <Text style={[styles.notifType, { color: theme.colors.warning || '#FF9800' }]}>
          {item.type}
        </Text>
        <Text style={[styles.notifTicker, { color: theme.colors.text.primary }]}>
          {item.ticker}
        </Text>
      </View>
      <Text style={[styles.notifAction, { color: theme.colors.text.primary }]}>
        {item.action}
      </Text>
      {item.instruction && (
        <Text style={[styles.notifInstruction, { color: theme.colors.text.secondary }]}>
          {item.instruction}
        </Text>
      )}
    </Card>
  );

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.colors.background.primary }]} edges={['top']}>
      {/* Header with Analytics Button (samma stil som Watchlist) */}
      <View style={{
        flexDirection: 'row',
        paddingHorizontal: theme.spacing.base,
        paddingVertical: theme.spacing.md,
        backgroundColor: theme.colors.background.secondary,
        borderBottomWidth: 1,
        borderBottomColor: theme.colors.border.primary,
        gap: theme.spacing.sm,
      }}>
        <View
          style={{
            flex: 2,
            paddingVertical: 12,
            paddingHorizontal: 16,
            borderRadius: 8,
            backgroundColor: theme.colors.background.tertiary,
            borderWidth: 1.5,
            borderColor: theme.colors.border.primary,
            justifyContent: 'center',
          }}
        >
          <Text style={{
            color: theme.colors.text.primary,
            fontSize: 15,
            fontWeight: '700',
            textAlign: 'center',
          }}>
            Positioner
          </Text>
        </View>

        <TouchableOpacity
          onPress={() => navigation.navigate('Analytics')}
          style={{
            flex: 1,
            paddingVertical: 12,
            paddingHorizontal: 16,
            borderRadius: 8,
            backgroundColor: theme.colors.alpha(theme.colors.primary, 0.1),
            borderWidth: 1.5,
            borderColor: theme.colors.primary,
          }}
          activeOpacity={0.7}
        >
          <Text style={{
            color: theme.colors.primary,
            fontSize: 15,
            fontWeight: '700',
            textAlign: 'center',
          }}>
            Analytics
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          onPress={checkPositions}
          style={{
            paddingVertical: 12,
            paddingHorizontal: 16,
            borderRadius: 8,
            backgroundColor: theme.colors.alpha(theme.colors.primary, 0.1),
            borderWidth: 1.5,
            borderColor: theme.colors.primary,
            justifyContent: 'center',
            alignItems: 'center',
          }}
          activeOpacity={0.7}
        >
          <Ionicons name="refresh" size={20} color={theme.colors.primary} />
        </TouchableOpacity>

        <TouchableOpacity
          onPress={() => setModalVisible(true)}
          style={{
            paddingVertical: 12,
            paddingHorizontal: 16,
            borderRadius: 8,
            backgroundColor: theme.colors.bullish,
            borderWidth: 1.5,
            borderColor: theme.colors.bullish,
            justifyContent: 'center',
            alignItems: 'center',
          }}
          activeOpacity={0.7}
        >
          <Ionicons name="add" size={24} color="#FFFFFF" />
        </TouchableOpacity>
      </View>

      {/* Last Checked Indicator */}
      {lastChecked && (lastChecked.SE || lastChecked.US) && (
        <View style={{
          paddingHorizontal: theme.spacing.base,
          paddingVertical: theme.spacing.xs,
          backgroundColor: theme.colors.background.secondary,
        }}>
          <Text style={{
            fontSize: 11,
            color: theme.colors.text.tertiary,
            textAlign: 'center',
          }}>
            Senast kollad: {lastChecked.SE ? `SE ${getTimeAgo(lastChecked.SE)}` : ''}{lastChecked.SE && lastChecked.US ? ' • ' : ''}{lastChecked.US ? `US ${getTimeAgo(lastChecked.US)}` : ''}
          </Text>
        </View>
      )}

      {/* Alerts Section */}
      {notifications.length > 0 && (
        <View style={[styles.notificationsSection, {
          backgroundColor: theme.colors.alpha(theme.colors.warning || '#FF9800', 0.1),
          borderBottomColor: theme.colors.warning || '#FF9800',
          paddingHorizontal: theme.spacing.base,
          paddingVertical: theme.spacing.md,
        }]}>
          <Text style={[styles.sectionTitle, { color: theme.colors.warning || '#FF9800' }]}>
            ALERTS
          </Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false}>
            {notifications.map((item, index) => (
              <View key={`${item.ticker}-${index}`} style={{ marginRight: theme.spacing.sm }}>
                {renderNotificationItem({ item })}
              </View>
            ))}
          </ScrollView>
        </View>
      )}

      {/* Positions List */}
      <FlatList
        data={positions}
        renderItem={renderPositionItem}
        keyExtractor={(item) => item.ticker}
        contentContainerStyle={{
          padding: theme.spacing.base,
          paddingBottom: theme.spacing.xl,
        }}
        refreshControl={
          <RefreshControl
            refreshing={loading}
            onRefresh={refresh}
            tintColor={theme.colors.primary}
          />
        }
        ListEmptyComponent={
          <Card variant="default" style={{ marginTop: theme.spacing.xl, alignItems: 'center', padding: theme.spacing.xl }}>
            <Text style={[styles.emptyText, { color: theme.colors.text.secondary }]}>
              Inga öppna positioner
            </Text>
            <Text style={[styles.emptySubtext, { color: theme.colors.text.tertiary }]}>
              Lägg till positioner från Signaler-fliken
            </Text>
          </Card>
        }
      />

      {/* Add Position Modal */}
      <AddPositionModal
        visible={modalVisible}
        onClose={() => {
          setModalVisible(false);
          fetchPositions(); // Refresh positions after adding
        }}
        mode="manual"
        signalData={null}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  notificationsSection: {
    borderBottomWidth: 2,
  },
  sectionTitle: {
    fontSize: 12,
    fontWeight: '700',
    letterSpacing: 0.5,
    marginBottom: 8,
  },
  notificationCard: {
    minWidth: 250,
    borderLeftWidth: 4,
  },
  notifHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  notifType: {
    fontSize: 11,
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  notifTicker: {
    fontSize: 14,
    fontWeight: '700',
  },
  notifAction: {
    fontSize: 13,
    marginBottom: 4,
  },
  notifInstruction: {
    fontSize: 12,
    fontStyle: 'italic',
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
  statusBadge: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
  },
  statusText: {
    fontWeight: '700',
    fontSize: 12,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  pricesRow: {
    flexDirection: 'row',
    gap: 16,
  },
  priceLabel: {
    fontSize: 11,
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 4,
  },
  plSection: {
    padding: 12,
    borderRadius: 8,
  },
  plLabel: {
    fontSize: 11,
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 4,
  },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  label: {
    fontSize: 12,
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  exitsSection: {
    borderTopWidth: 1,
  },
  exitsTitle: {
    fontSize: 11,
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 8,
  },
  exitRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  exitText: {
    fontSize: 13,
  },
  exitType: {
    fontSize: 11,
    marginTop: 2,
  },
  targetsSection: {
    padding: 12,
    borderRadius: 8,
    borderLeftWidth: 3,
  },
  targetsTitle: {
    fontSize: 12,
    fontWeight: '700',
    letterSpacing: 0.5,
    marginBottom: 12,
  },
  targetsGrid: {
    flexDirection: 'row',
    gap: 12,
  },
  targetItem: {
    flex: 1,
  },
  targetLabel: {
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
  emptyText: {
    fontSize: 16,
    marginBottom: 8,
  },
  emptySubtext: {
    fontSize: 14,
    textAlign: 'center',
  },
});
