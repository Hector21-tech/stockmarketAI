/**
 * Watchlist Screen
 * Professional watchlist with real-time prices and search
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  RefreshControl,
  TextInput,
  Alert,
} from 'react-native';
import { useTheme } from '../theme/ThemeContext';
import { Card, PriceText, Button } from '../components';
import { api } from '../api/client';

export default function WatchlistScreen({ navigation }) {
  const { theme } = useTheme();
  const [watchlist, setWatchlist] = useState([
    'VOLVO-B',
    'HM-B',
    'ERIC-B',
    'ABB',
    'AZN',
  ]);
  const [stocks, setStocks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [newTicker, setNewTicker] = useState('');

  useEffect(() => {
    fetchWatchlistData();
  }, [watchlist]);

  const fetchWatchlistData = async () => {
    setLoading(true);
    try {
      const response = await api.getMultiplePrices(watchlist, 'SE');
      const pricesData = response.data.prices;

      const stocksData = Object.keys(pricesData).map((ticker) => ({
        ticker,
        price: pricesData[ticker],
        // Mock change data - would come from real API
        change: (Math.random() * 10 - 5).toFixed(2),
        changePercent: (Math.random() * 5 - 2.5).toFixed(2),
      }));

      setStocks(stocksData);
    } catch (error) {
      console.error('Error fetching watchlist:', error);
      Alert.alert('Fel', 'Kunde inte hämta aktiekurser');
    } finally {
      setLoading(false);
    }
  };

  const addToWatchlist = () => {
    if (!newTicker.trim()) {
      Alert.alert('Fel', 'Ange en ticker');
      return;
    }

    const ticker = newTicker.trim().toUpperCase();

    if (watchlist.includes(ticker)) {
      Alert.alert('Fel', 'Aktien finns redan i watchlist');
      return;
    }

    if (watchlist.length >= 30) {
      Alert.alert('Fel', 'Max 30 aktier i watchlist');
      return;
    }

    setWatchlist([...watchlist, ticker]);
    setNewTicker('');
  };

  const removeFromWatchlist = (ticker) => {
    Alert.alert(
      'Ta bort',
      `Vill du ta bort ${ticker} från watchlist?`,
      [
        { text: 'Avbryt', style: 'cancel' },
        {
          text: 'Ta bort',
          onPress: () => {
            setWatchlist(watchlist.filter((t) => t !== ticker));
          },
          style: 'destructive',
        },
      ]
    );
  };

  const renderStockItem = ({ item }) => (
    <TouchableOpacity
      onLongPress={() => removeFromWatchlist(item.ticker)}
      activeOpacity={0.7}
    >
      <Card variant="default" style={{ marginBottom: theme.spacing.sm }}>
        <View style={styles.stockRow}>
          {/* Left side - Ticker and name */}
          <View style={{ flex: 1 }}>
            <Text style={[styles.ticker, { color: theme.colors.text.primary, ...theme.typography.styles.h6 }]}>
              {item.ticker}
            </Text>
            <Text style={[styles.stockName, { color: theme.colors.text.tertiary }]}>
              Swedish Stock
            </Text>
          </View>

          {/* Right side - Price and change */}
          <View style={{ alignItems: 'flex-end' }}>
            <PriceText
              value={item.price}
              size="md"
              suffix=" SEK"
            />
            <View style={{ flexDirection: 'row', alignItems: 'center', marginTop: theme.spacing.xs }}>
              <PriceText
                value={item.change}
                size="sm"
                showChange
                colorize
                style={{ marginRight: theme.spacing.xs }}
              />
              <PriceText
                value={item.changePercent}
                size="sm"
                showChange
                colorize
                suffix="%"
              />
            </View>
          </View>
        </View>
      </Card>
    </TouchableOpacity>
  );

  return (
    <View style={[styles.container, { backgroundColor: theme.colors.background.primary }]}>
      {/* Add Stock Section */}
      <View style={[styles.addSection, {
        backgroundColor: theme.colors.background.secondary,
        borderBottomColor: theme.colors.border.primary,
        paddingHorizontal: theme.spacing.base,
        paddingVertical: theme.spacing.md,
      }]}>
        <TextInput
          style={[styles.input, {
            backgroundColor: theme.colors.background.tertiary,
            borderColor: theme.colors.border.primary,
            color: theme.colors.text.primary,
            ...theme.typography.styles.body,
          }]}
          placeholder="Lägg till aktie (t.ex. VOLVO-B)"
          placeholderTextColor={theme.colors.text.tertiary}
          value={newTicker}
          onChangeText={setNewTicker}
          autoCapitalize="characters"
          onSubmitEditing={addToWatchlist}
        />
        <View style={{ width: theme.spacing.sm }} />
        <Button
          onPress={addToWatchlist}
          style={styles.addButton}
          textStyle={{ fontSize: 20 }}
        >
          +
        </Button>
      </View>

      {/* Stock Count */}
      <View style={{ paddingHorizontal: theme.spacing.base, paddingVertical: theme.spacing.sm }}>
        <Text style={[styles.count, { color: theme.colors.text.secondary }]}>
          {watchlist.length} / 30 aktier
        </Text>
      </View>

      {/* Stock List */}
      <FlatList
        data={stocks}
        renderItem={renderStockItem}
        keyExtractor={(item) => item.ticker}
        contentContainerStyle={{
          paddingHorizontal: theme.spacing.base,
          paddingBottom: theme.spacing.xl,
        }}
        refreshControl={
          <RefreshControl
            refreshing={loading}
            onRefresh={fetchWatchlistData}
            tintColor={theme.colors.primary}
          />
        }
        ListEmptyComponent={
          <Card variant="default" style={{ marginTop: theme.spacing.xl }}>
            <Text style={[styles.emptyText, { color: theme.colors.text.tertiary }]}>
              Inga aktier i watchlist. Lägg till aktier ovan.
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
  addSection: {
    flexDirection: 'row',
    borderBottomWidth: 1,
    alignItems: 'center',
  },
  input: {
    flex: 1,
    height: 44,
    borderWidth: 1,
    borderRadius: 8,
    paddingHorizontal: 12,
  },
  addButton: {
    width: 44,
    height: 44,
    paddingHorizontal: 0,
    paddingVertical: 0,
    minHeight: 44,
  },
  count: {
    fontSize: 12,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  stockRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  ticker: {
    marginBottom: 2,
  },
  stockName: {
    fontSize: 12,
  },
  emptyText: {
    textAlign: 'center',
    padding: 20,
  },
});
