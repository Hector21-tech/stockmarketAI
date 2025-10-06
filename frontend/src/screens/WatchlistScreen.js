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
import { api } from '../api/client';

export default function WatchlistScreen({ navigation }) {
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
      }));

      setStocks(stocksData);
    } catch (error) {
      console.error('Error fetching watchlist:', error);
      Alert.alert('Fel', 'Kunde inte hamta aktiekurser');
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
      `Vill du ta bort ${ticker} fran watchlist?`,
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

  const analyzeStock = async (ticker) => {
    try {
      navigation.navigate('StockAnalysis', { ticker });
    } catch (error) {
      console.error('Error:', error);
    }
  };

  const renderStockItem = ({ item }) => (
    <TouchableOpacity
      style={styles.stockItem}
      onPress={() => analyzeStock(item.ticker)}
      onLongPress={() => removeFromWatchlist(item.ticker)}
    >
      <View style={styles.stockInfo}>
        <Text style={styles.ticker}>{item.ticker}</Text>
        <Text style={styles.price}>{item.price?.toFixed(2)} SEK</Text>
      </View>
      <Text style={styles.arrow}>→</Text>
    </TouchableOpacity>
  );

  return (
    <View style={styles.container}>
      <View style={styles.addSection}>
        <TextInput
          style={styles.input}
          placeholder="Lagg till aktie (t.ex. VOLVO-B)"
          value={newTicker}
          onChangeText={setNewTicker}
          autoCapitalize="characters"
          onSubmitEditing={addToWatchlist}
        />
        <TouchableOpacity style={styles.addButton} onPress={addToWatchlist}>
          <Text style={styles.addButtonText}>+</Text>
        </TouchableOpacity>
      </View>

      <Text style={styles.count}>
        {watchlist.length} / 30 aktier
      </Text>

      <FlatList
        data={stocks}
        renderItem={renderStockItem}
        keyExtractor={(item) => item.ticker}
        refreshControl={
          <RefreshControl
            refreshing={loading}
            onRefresh={fetchWatchlistData}
          />
        }
        ListEmptyComponent={
          <Text style={styles.emptyText}>
            Inga aktier i watchlist. Lagg till aktier ovan.
          </Text>
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
  addSection: {
    flexDirection: 'row',
    padding: 16,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  input: {
    flex: 1,
    height: 45,
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    paddingHorizontal: 12,
    marginRight: 8,
    fontSize: 16,
  },
  addButton: {
    width: 45,
    height: 45,
    backgroundColor: '#2196F3',
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
  },
  addButtonText: {
    color: '#fff',
    fontSize: 24,
    fontWeight: 'bold',
  },
  count: {
    padding: 12,
    paddingLeft: 16,
    color: '#666',
    fontSize: 14,
  },
  stockItem: {
    backgroundColor: '#fff',
    padding: 16,
    marginHorizontal: 16,
    marginVertical: 6,
    borderRadius: 8,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  stockInfo: {
    flex: 1,
  },
  ticker: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
  },
  price: {
    fontSize: 16,
    color: '#666',
    marginTop: 4,
  },
  arrow: {
    fontSize: 24,
    color: '#2196F3',
  },
  emptyText: {
    textAlign: 'center',
    marginTop: 50,
    color: '#999',
    fontSize: 16,
  },
});
