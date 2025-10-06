import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  RefreshControl,
  Alert,
} from 'react-native';
import { api } from '../api/client';

export default function PositionsScreen() {
  const [positions, setPositions] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(false);

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

      if (newNotifications.length > 0) {
        setNotifications(newNotifications);
        // Visa forsta notifikationen
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

  const renderPositionItem = ({ item }) => {
    const profitColor =
      item.status === 'CLOSED'
        ? '#666'
        : item.unrealized_percent > 0
        ? '#4CAF50'
        : '#F44336';

    return (
      <View style={styles.positionCard}>
        <View style={styles.header}>
          <Text style={styles.ticker}>{item.ticker}</Text>
          <View
            style={[
              styles.statusBadge,
              {
                backgroundColor:
                  item.status === 'OPEN'
                    ? '#4CAF50'
                    : item.status === 'PARTIAL'
                    ? '#FF9800'
                    : '#9E9E9E',
              },
            ]}
          >
            <Text style={styles.statusText}>{item.status}</Text>
          </View>
        </View>

        <View style={styles.row}>
          <Text style={styles.label}>Aktier:</Text>
          <Text style={styles.value}>{item.current_shares}</Text>
        </View>

        <View style={styles.row}>
          <Text style={styles.label}>Entry:</Text>
          <Text style={styles.value}>{item.entry_price} SEK</Text>
        </View>

        {item.current_price && (
          <>
            <View style={styles.row}>
              <Text style={styles.label}>Nuvarande:</Text>
              <Text style={styles.value}>{item.current_price} SEK</Text>
            </View>

            <View style={styles.row}>
              <Text style={styles.label}>P/L:</Text>
              <Text style={[styles.value, { color: profitColor }]}>
                {item.unrealized_profit > 0 ? '+' : ''}
                {item.unrealized_profit} SEK (
                {item.unrealized_percent > 0 ? '+' : ''}
                {item.unrealized_percent.toFixed(2)}%)
              </Text>
            </View>
          </>
        )}

        <View style={styles.row}>
          <Text style={styles.label}>Stop Loss:</Text>
          <Text style={styles.value}>{item.stop_loss} SEK</Text>
        </View>

        {item.exits && item.exits.length > 0 && (
          <View style={styles.exitsSection}>
            <Text style={styles.exitsTitle}>Exits:</Text>
            {item.exits.map((exit, index) => (
              <Text key={index} style={styles.exitText}>
                • {exit.shares} st @ {exit.price} SEK (
                {exit.profit_percent > 0 ? '+' : ''}
                {exit.profit_percent}%) - {exit.type}
              </Text>
            ))}
          </View>
        )}
      </View>
    );
  };

  const renderNotificationItem = ({ item }) => (
    <View style={styles.notificationCard}>
      <View style={styles.notifHeader}>
        <Text style={styles.notifType}>{item.type}</Text>
        <Text style={styles.notifTicker}>{item.ticker}</Text>
      </View>
      <Text style={styles.notifAction}>{item.action}</Text>
      {item.instruction && (
        <Text style={styles.notifInstruction}>{item.instruction}</Text>
      )}
    </View>
  );

  return (
    <View style={styles.container}>
      {notifications.length > 0 && (
        <View style={styles.notificationsSection}>
          <Text style={styles.sectionTitle}>ALERTS</Text>
          <FlatList
            data={notifications}
            renderItem={renderNotificationItem}
            keyExtractor={(item, index) => `${item.ticker}-${index}`}
            horizontal
            showsHorizontalScrollIndicator={false}
          />
        </View>
      )}

      <FlatList
        data={positions}
        renderItem={renderPositionItem}
        keyExtractor={(item) => item.ticker}
        refreshControl={
          <RefreshControl refreshing={loading} onRefresh={refresh} />
        }
        ListEmptyComponent={
          <View style={styles.emptyContainer}>
            <Text style={styles.emptyText}>Inga oppna positioner</Text>
            <Text style={styles.emptySubtext}>
              Lagg till positioner fran Signaler-fliken
            </Text>
          </View>
        }
        contentContainerStyle={
          positions.length === 0 && styles.emptyList
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  notificationsSection: {
    backgroundColor: '#FFF3E0',
    padding: 12,
    borderBottomWidth: 2,
    borderBottomColor: '#FF9800',
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#E65100',
    marginBottom: 8,
  },
  notificationCard: {
    backgroundColor: '#fff',
    padding: 12,
    marginRight: 12,
    borderRadius: 8,
    minWidth: 250,
    borderLeftWidth: 4,
    borderLeftColor: '#FF9800',
  },
  notifHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  notifType: {
    fontSize: 12,
    fontWeight: 'bold',
    color: '#E65100',
  },
  notifTicker: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#333',
  },
  notifAction: {
    fontSize: 14,
    color: '#333',
    marginBottom: 4,
  },
  notifInstruction: {
    fontSize: 12,
    color: '#666',
    fontStyle: 'italic',
  },
  positionCard: {
    backgroundColor: '#fff',
    margin: 16,
    marginBottom: 8,
    borderRadius: 12,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  ticker: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#333',
  },
  statusBadge: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
  },
  statusText: {
    color: '#fff',
    fontWeight: 'bold',
    fontSize: 12,
  },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginVertical: 4,
  },
  label: {
    fontSize: 14,
    color: '#666',
  },
  value: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#333',
  },
  exitsSection: {
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#e0e0e0',
  },
  exitsTitle: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#666',
    marginBottom: 4,
  },
  exitText: {
    fontSize: 12,
    color: '#555',
    marginVertical: 2,
  },
  emptyList: {
    flex: 1,
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingTop: 100,
  },
  emptyText: {
    fontSize: 18,
    color: '#999',
    marginBottom: 8,
  },
  emptySubtext: {
    fontSize: 14,
    color: '#bbb',
    textAlign: 'center',
    paddingHorizontal: 40,
  },
});
