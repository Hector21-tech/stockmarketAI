import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  RefreshControl,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { api } from '../api/client';

export default function SignalsScreen() {
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
      Alert.alert('Fel', 'Kunde inte hamta signaler');
    } finally {
      setLoading(false);
    }
  };

  const getSignalColor = (strength) => {
    switch (strength) {
      case 'STRONG':
        return '#4CAF50';
      case 'MODERATE':
        return '#FF9800';
      default:
        return '#9E9E9E';
    }
  };

  const renderSignalItem = ({ item }) => {
    const { ticker, signal, trade_setup, analysis } = item;

    return (
      <View style={styles.signalCard}>
        <View style={styles.header}>
          <Text style={styles.ticker}>{ticker}</Text>
          <View
            style={[
              styles.signalBadge,
              { backgroundColor: getSignalColor(signal.strength) },
            ]}
          >
            <Text style={styles.signalText}>{signal.action}</Text>
          </View>
        </View>

        <Text style={styles.price}>
          Pris: {analysis.price.toFixed(2)} SEK
        </Text>

        <View style={styles.infoRow}>
          <Text style={styles.label}>RSI:</Text>
          <Text style={styles.value}>{analysis.rsi.toFixed(1)}</Text>
          <Text style={styles.label}>Score:</Text>
          <Text style={styles.value}>{signal.score}</Text>
        </View>

        <Text style={styles.summary}>{signal.summary}</Text>

        {trade_setup.entry && (
          <View style={styles.tradeSetup}>
            <Text style={styles.setupTitle}>TRADE SETUP:</Text>
            <View style={styles.setupRow}>
              <Text style={styles.setupLabel}>Entry:</Text>
              <Text style={styles.setupValue}>
                {trade_setup.entry} SEK
              </Text>
            </View>
            <View style={styles.setupRow}>
              <Text style={styles.setupLabel}>Stop:</Text>
              <Text style={styles.setupValue}>
                {trade_setup.stop_loss} SEK
              </Text>
            </View>
            <View style={styles.setupRow}>
              <Text style={styles.setupLabel}>Target 1:</Text>
              <Text style={styles.setupValue}>
                {trade_setup.targets.target_1.price} SEK (+
                {trade_setup.targets.target_1.gain_percent}%)
              </Text>
            </View>
            <View style={styles.setupRow}>
              <Text style={styles.setupLabel}>Target 2:</Text>
              <Text style={styles.setupValue}>
                {trade_setup.targets.target_2.price} SEK (+
                {trade_setup.targets.target_2.gain_percent}%)
              </Text>
            </View>
          </View>
        )}

        <View style={styles.reasons}>
          {signal.reasons.map((reason, index) => (
            <Text key={index} style={styles.reason}>
              • {reason}
            </Text>
          ))}
        </View>
      </View>
    );
  };

  if (loading && signals.length === 0) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#2196F3" />
        <Text style={styles.loadingText}>Skannar watchlist...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <FlatList
        data={signals}
        renderItem={renderSignalItem}
        keyExtractor={(item) => item.ticker}
        refreshControl={
          <RefreshControl refreshing={loading} onRefresh={fetchSignals} />
        }
        ListEmptyComponent={
          <View style={styles.emptyContainer}>
            <Text style={styles.emptyText}>Inga kopsignaler just nu</Text>
            <Text style={styles.emptySubtext}>
              Dra ner for att uppdatera
            </Text>
          </View>
        }
        contentContainerStyle={signals.length === 0 && styles.emptyList}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f5f5f5',
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
    color: '#666',
  },
  signalCard: {
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
  signalBadge: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
  },
  signalText: {
    color: '#fff',
    fontWeight: 'bold',
    fontSize: 14,
  },
  price: {
    fontSize: 18,
    color: '#666',
    marginBottom: 8,
  },
  infoRow: {
    flexDirection: 'row',
    marginBottom: 12,
  },
  label: {
    fontSize: 14,
    color: '#666',
    marginRight: 8,
  },
  value: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#333',
    marginRight: 16,
  },
  summary: {
    fontSize: 15,
    color: '#333',
    marginBottom: 12,
    fontStyle: 'italic',
  },
  tradeSetup: {
    backgroundColor: '#E3F2FD',
    padding: 12,
    borderRadius: 8,
    marginVertical: 12,
  },
  setupTitle: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#1976D2',
    marginBottom: 8,
  },
  setupRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginVertical: 2,
  },
  setupLabel: {
    fontSize: 14,
    color: '#555',
  },
  setupValue: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#333',
  },
  reasons: {
    marginTop: 8,
  },
  reason: {
    fontSize: 13,
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
  },
});
