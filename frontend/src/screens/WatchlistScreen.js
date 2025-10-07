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
import { SafeAreaView } from 'react-native-safe-area-context';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useTheme } from '../theme/ThemeContext';
import { Card, PriceText, Button } from '../components';
import { api } from '../api/client';
import WebSocketService from '../services/WebSocketService';

export default function WatchlistScreen({ navigation }) {
  const { theme } = useTheme();
  const [watchlist, setWatchlist] = useState([]);
  const [stocks, setStocks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [newTicker, setNewTicker] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [wsConnected, setWsConnected] = useState(false);
  const [lastUpdate, setLastUpdate] = useState(null);

  useEffect(() => {
    loadWatchlist();
  }, []);

  useEffect(() => {
    const unsubscribe = navigation.addListener('focus', () => {
      loadWatchlist();
    });
    return unsubscribe;
  }, [navigation]);

  useEffect(() => {
    if (watchlist.length > 0) {
      fetchWatchlistData();
    }
  }, [watchlist]);

  // Debounced search effect
  useEffect(() => {
    if (newTicker.trim().length >= 2) {
      const timer = setTimeout(() => {
        searchStocks(newTicker.trim());
      }, 300); // 300ms debounce
      return () => clearTimeout(timer);
    } else {
      setSearchResults([]);
    }
  }, [newTicker]);

  // WebSocket setup
  useEffect(() => {
    console.log('Setting up WebSocket...');

    // Connect to WebSocket
    WebSocketService.connect();

    // Setup price update listener
    WebSocketService.onPriceUpdate((data) => {
      console.log('Real-time price update:', data);
      setLastUpdate(new Date());

      // Update stocks with new quotes (price + change)
      setStocks((prevStocks) => {
        return prevStocks.map((stock) => {
          const newQuote = data.quotes?.[stock.ticker];
          if (newQuote) {
            return {
              ...stock,
              price: newQuote.price,
              change: newQuote.change,
              changePercent: newQuote.changePercent,
            };
          }
          return stock;
        });
      });
    });

    // Setup connection status listener
    WebSocketService.onConnectionChange((connected) => {
      console.log('WebSocket connection changed:', connected);
      setWsConnected(connected);
    });

    // Cleanup on unmount
    return () => {
      console.log('Cleaning up WebSocket...');
      WebSocketService.unsubscribeFromWatchlist();
      WebSocketService.disconnect();
    };
  }, []);

  // Subscribe to watchlist updates when watchlist changes
  useEffect(() => {
    if (watchlist.length > 0 && WebSocketService.isConnected()) {
      console.log('Subscribing to watchlist:', watchlist);
      WebSocketService.subscribeToWatchlist(watchlist, 'SE');
    }
  }, [watchlist, wsConnected]);

  const searchStocks = async (query) => {
    setIsSearching(true);
    try {
      const response = await api.searchStocks(query, 10);
      console.log('Search response:', response.data);
      console.log('Results:', response.data.results);
      setSearchResults(response.data.results || []);
    } catch (error) {
      console.error('Error searching stocks:', error);
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  const loadWatchlist = async () => {
    try {
      const watchlistJson = await AsyncStorage.getItem('watchlist');
      if (watchlistJson) {
        setWatchlist(JSON.parse(watchlistJson));
      } else {
        // Default watchlist
        const defaultWatchlist = ['VOLVO-B', 'HM-B', 'ERIC-B', 'ABB', 'AZN'];
        setWatchlist(defaultWatchlist);
        await AsyncStorage.setItem('watchlist', JSON.stringify(defaultWatchlist));
      }
    } catch (error) {
      console.error('Error loading watchlist:', error);
    }
  };

  const fetchWatchlistData = async () => {
    setLoading(true);
    try {
      const response = await api.getMultipleQuotes(watchlist, 'SE');
      const quotesData = response.data.quotes;

      // Fetch stock info (name) for each ticker
      const stocksData = await Promise.all(
        Object.keys(quotesData).map(async (ticker) => {
          try {
            const infoResponse = await api.getStockInfo(ticker, 'SE');
            const quote = quotesData[ticker];
            return {
              ticker,
              name: infoResponse.data.name || ticker,
              price: quote.price,
              change: quote.change,
              changePercent: quote.changePercent,
            };
          } catch (error) {
            console.error(`Error fetching info for ${ticker}:`, error);
            const quote = quotesData[ticker];
            return {
              ticker,
              name: ticker,
              price: quote.price,
              change: quote.change,
              changePercent: quote.changePercent,
            };
          }
        })
      );

      setStocks(stocksData);
    } catch (error) {
      console.error('Error fetching watchlist:', error);
      Alert.alert('Fel', 'Kunde inte hämta aktiekurser');
    } finally {
      setLoading(false);
    }
  };

  const selectStock = async (stock) => {
    const ticker = stock.ticker;

    if (watchlist.includes(ticker)) {
      Alert.alert('Finns redan', `${stock.name} finns redan i watchlist`);
      return;
    }

    if (watchlist.length >= 30) {
      Alert.alert('Fel', 'Max 30 aktier i watchlist');
      return;
    }

    try {
      setLoading(true);
      // Add to watchlist
      const newWatchlist = [...watchlist, ticker];
      setWatchlist(newWatchlist);
      await AsyncStorage.setItem('watchlist', JSON.stringify(newWatchlist));
      setNewTicker('');
      setSearchResults([]);
      Alert.alert('Tillagd!', `${stock.name} har lagts till i watchlist`);
    } catch (error) {
      console.error('Error adding stock:', error);
      Alert.alert('Fel', 'Kunde inte lägga till aktie');
    } finally {
      setLoading(false);
    }
  };

  const addToWatchlist = async () => {
    if (!newTicker.trim()) {
      Alert.alert('Fel', 'Ange en aktie att söka efter');
      return;
    }

    // If there are search results, select the first one
    if (searchResults.length > 0) {
      selectStock(searchResults[0]);
    } else {
      Alert.alert('Ingen aktie hittades', 'Prova att söka efter ett annat företag eller ticker');
    }
  };

  const removeFromWatchlist = (ticker) => {
    Alert.alert(
      'Ta bort',
      `Vill du ta bort ${ticker} från watchlist?`,
      [
        { text: 'Avbryt', style: 'cancel' },
        {
          text: 'Ta bort',
          onPress: async () => {
            const newWatchlist = watchlist.filter((t) => t !== ticker);
            setWatchlist(newWatchlist);
            await AsyncStorage.setItem('watchlist', JSON.stringify(newWatchlist));
          },
          style: 'destructive',
        },
      ]
    );
  };

  const renderStockItem = ({ item }) => (
    <TouchableOpacity
      onPress={() => navigation.navigate('StockDetail', { ticker: item.ticker, market: 'SE' })}
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
            <Text style={[styles.stockName, { color: theme.colors.text.tertiary }]} numberOfLines={1}>
              {item.name || 'Loading...'}
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
    <SafeAreaView style={[styles.container, { backgroundColor: theme.colors.background.primary }]} edges={['top']}>
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
            fontSize: 16,
          }]}
          placeholder="Sök företag eller ticker (t.ex. Investor, AAPL)"
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

      {/* Search Results Dropdown */}
      {searchResults.length > 0 && newTicker.trim().length >= 2 && (
        <View style={[styles.searchDropdown, {
          backgroundColor: '#FFFFFF',
          borderColor: theme.colors.primary,
          borderWidth: 2,
          shadowColor: '#000',
          shadowOffset: { width: 0, height: 4 },
          shadowOpacity: 0.3,
          shadowRadius: 5,
          elevation: 8,
          zIndex: 9999,
          position: 'relative',
        }]}>
          <View style={{ backgroundColor: theme.colors.primary, padding: 8 }}>
            <Text style={{ color: '#FFFFFF', fontSize: 12, fontWeight: 'bold' }}>
              {searchResults.length} resultat funna
            </Text>
          </View>
          {searchResults.map((stock, index) => {
            console.log('Rendering stock:', stock);
            return (
              <TouchableOpacity
                key={`${stock.ticker}-${index}`}
                style={[styles.searchResultItem, {
                  borderBottomColor: '#E0E0E0',
                  borderBottomWidth: index < searchResults.length - 1 ? 1 : 0,
                  backgroundColor: index % 2 === 0 ? '#FFFFFF' : '#F5F5F5',
                }]}
                onPress={() => {
                  console.log('Selected stock:', stock);
                  selectStock(stock);
                }}
                activeOpacity={0.7}
              >
                <View style={{ flex: 1 }}>
                  <Text style={{
                    fontSize: 16,
                    fontWeight: '700',
                    color: theme.colors.primary,
                    marginBottom: 4,
                  }}>
                    {stock.ticker || 'NO TICKER'}
                  </Text>
                  <Text style={{
                    fontSize: 14,
                    fontWeight: '500',
                    color: '#000000',
                    marginBottom: 4,
                  }} numberOfLines={1}>
                    {stock.name || 'NO NAME'}
                  </Text>
                  <Text style={{
                    fontSize: 11,
                    color: '#666666',
                    textTransform: 'uppercase',
                  }}>
                    {stock.exchange} • {stock.market}
                  </Text>
                </View>
              </TouchableOpacity>
            );
          })}
        </View>
      )}

      {/* Loading indicator for search */}
      {isSearching && newTicker.trim().length >= 2 && (
        <View style={{ paddingHorizontal: theme.spacing.base, paddingVertical: theme.spacing.sm }}>
          <Text style={[styles.searchingText, { color: theme.colors.text.tertiary }]}>
            Söker...
          </Text>
        </View>
      )}

      {/* Stock Count & Connection Status */}
      <View style={{
        paddingHorizontal: theme.spacing.base,
        paddingVertical: theme.spacing.sm,
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
      }}>
        <Text style={[styles.count, { color: theme.colors.text.secondary }]}>
          {watchlist.length} / 30 aktier
        </Text>
        <View style={{
          flexDirection: 'row',
          alignItems: 'center',
          backgroundColor: wsConnected ? theme.colors.alpha(theme.colors.bullish, 0.15) : theme.colors.alpha(theme.colors.bearish, 0.15),
          paddingHorizontal: 10,
          paddingVertical: 5,
          borderRadius: 12,
        }}>
          <View style={{
            width: 8,
            height: 8,
            borderRadius: 4,
            backgroundColor: wsConnected ? theme.colors.bullish : theme.colors.bearish,
            marginRight: 6,
          }} />
          <Text style={{
            fontSize: 11,
            color: wsConnected ? theme.colors.bullish : theme.colors.bearish,
            fontWeight: '600',
            textTransform: 'uppercase',
          }}>
            {wsConnected ? 'Live' : 'Offline'}
          </Text>
          {lastUpdate && wsConnected && (
            <Text style={{
              fontSize: 9,
              color: theme.colors.text.tertiary,
              marginLeft: 6,
            }}>
              {lastUpdate.toLocaleTimeString('sv-SE', { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
            </Text>
          )}
        </View>
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
    </SafeAreaView>
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
    paddingVertical: 12,
    lineHeight: 20,
    includeFontPadding: false,
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
  searchDropdown: {
    marginHorizontal: 16,
    borderRadius: 8,
    borderWidth: 1,
    overflow: 'hidden',
    maxHeight: 300,
  },
  searchResultItem: {
    padding: 12,
  },
  searchResultTicker: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 2,
  },
  searchResultName: {
    fontSize: 14,
    marginBottom: 4,
  },
  searchResultExchange: {
    fontSize: 11,
    textTransform: 'uppercase',
  },
  searchingText: {
    fontSize: 12,
    fontStyle: 'italic',
  },
});
