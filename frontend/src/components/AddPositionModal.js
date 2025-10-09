/**
 * AddPositionModal
 * Modal for adding positions (from signals or manually)
 */

import React, { useState, useEffect } from 'react';
import {
  Modal,
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  Alert,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../theme/ThemeContext';
import { Card, Button } from './index';
import { api } from '../api/client';

export default function AddPositionModal({
  visible,
  onClose,
  mode = 'manual', // 'manual' or 'from-signal'
  signalData = null // pre-filled data from signal
}) {
  const { theme } = useTheme();

  // Form state
  const [ticker, setTicker] = useState('');
  const [entryPrice, setEntryPrice] = useState('');
  const [shares, setShares] = useState('');
  const [stopLoss, setStopLoss] = useState('');
  const [target1, setTarget1] = useState('');
  const [target2, setTarget2] = useState('');
  const [target3, setTarget3] = useState('');
  const [loading, setLoading] = useState(false);

  // Search state for manual mode
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);

  // Reset form function
  const resetForm = () => {
    setTicker('');
    setSearchQuery('');
    setEntryPrice('');
    setShares('');
    setStopLoss('');
    setTarget1('');
    setTarget2('');
    setTarget3('');
    setSearchResults([]);
  };

  // Pre-fill form when signal data is provided
  useEffect(() => {
    if (mode === 'from-signal' && signalData) {
      setTicker(signalData.ticker || '');
      setEntryPrice(signalData.trade_setup?.entry?.toString() || signalData.price?.toString() || '');
      setStopLoss(signalData.trade_setup?.stop_loss?.toString() || '');
      setTarget1(signalData.trade_setup?.target_1?.toString() || '');
      setTarget2(signalData.trade_setup?.target_2?.toString() || '');
      setTarget3(signalData.trade_setup?.target_3?.toString() || '');
    }
  }, [mode, signalData]);

  // Reset form when modal opens in manual mode
  useEffect(() => {
    if (visible && mode === 'manual') {
      resetForm();
    }
  }, [visible, mode]);

  // Search stocks (for manual mode)
  useEffect(() => {
    if (mode === 'manual' && searchQuery.trim().length >= 2) {
      setIsSearching(true);
      const timer = setTimeout(async () => {
        try {
          const response = await api.searchStocks(searchQuery.trim(), 10);
          setSearchResults(response.data.results || []);
        } catch (error) {
          console.error('Search error:', error);
          setSearchResults([]);
        } finally {
          setIsSearching(false);
        }
      }, 300);
      return () => clearTimeout(timer);
    } else {
      setSearchResults([]);
    }
  }, [searchQuery, mode]);

  const selectStock = async (stock) => {
    setTicker(stock.ticker);
    setSearchQuery('');
    setSearchResults([]);

    // Fetch current price and set as entry price
    try {
      const response = await api.getStockPrice(stock.ticker, 'SE');
      const price = response.data.price;
      setEntryPrice(price.toString());

      // Suggest stop loss (2% below entry)
      const suggestedStop = (price * 0.98).toFixed(2);
      setStopLoss(suggestedStop);

      // Suggest targets (4%, 8%, 15% above entry)
      setTarget1((price * 1.04).toFixed(2));
      setTarget2((price * 1.08).toFixed(2));
      setTarget3((price * 1.15).toFixed(2));
    } catch (error) {
      console.error('Error fetching price:', error);
      setEntryPrice('');
    }
  };

  const validateForm = () => {
    if (!ticker.trim()) {
      Alert.alert('Fel', 'Ange ticker');
      return false;
    }
    if (!entryPrice || isNaN(parseFloat(entryPrice))) {
      Alert.alert('Fel', 'Ange giltig entry price');
      return false;
    }
    if (!shares || isNaN(parseInt(shares)) || parseInt(shares) <= 0) {
      Alert.alert('Fel', 'Ange giltigt antal aktier');
      return false;
    }
    if (!stopLoss || isNaN(parseFloat(stopLoss))) {
      Alert.alert('Fel', 'Ange giltig stop loss');
      return false;
    }
    if (!target1 || isNaN(parseFloat(target1))) {
      Alert.alert('Fel', 'Ange minst Target 1');
      return false;
    }
    return true;
  };

  const handleSubmit = async () => {
    if (!validateForm()) return;

    setLoading(true);
    try {
      const targets = {
        target_1: {
          price: parseFloat(target1),
          gain_percent: ((parseFloat(target1) - parseFloat(entryPrice)) / parseFloat(entryPrice) * 100)
        },
        target_2: target2 ? {
          price: parseFloat(target2),
          gain_percent: ((parseFloat(target2) - parseFloat(entryPrice)) / parseFloat(entryPrice) * 100)
        } : { price: parseFloat(target1) * 1.05, gain_percent: 5 },
        target_3: target3 ? {
          price: parseFloat(target3),
          gain_percent: ((parseFloat(target3) - parseFloat(entryPrice)) / parseFloat(entryPrice) * 100)
        } : { price: parseFloat(target1) * 1.1, gain_percent: 10 },
      };

      const positionData = {
        ticker: ticker.trim().toUpperCase(),
        entry_price: parseFloat(entryPrice),
        shares: parseInt(shares),
        stop_loss: parseFloat(stopLoss),
        targets: targets,
        market: 'SE'
      };

      await api.addPosition(positionData);

      Alert.alert('Framgång!', `Position tillagd för ${ticker}`);
      resetForm();
      onClose();
    } catch (error) {
      console.error('Error adding position:', error);
      Alert.alert('Fel', 'Kunde inte lägga till position');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    resetForm();
    onClose();
  };

  return (
    <Modal
      visible={visible}
      animationType="slide"
      transparent={true}
      onRequestClose={handleClose}
    >
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.modalOverlay}
      >
        <View style={[styles.modalContent, { backgroundColor: theme.colors.background.primary }]}>
          {/* Header */}
          <View style={[styles.header, { borderBottomColor: theme.colors.border.primary }]}>
            <Text style={[styles.title, { color: theme.colors.text.primary }]}>
              {mode === 'from-signal' ? 'Lägg till från Signal' : 'Ny Position'}
            </Text>
            <TouchableOpacity onPress={handleClose}>
              <Ionicons name="close" size={28} color={theme.colors.text.primary} />
            </TouchableOpacity>
          </View>

          <ScrollView
            style={styles.scrollView}
            contentContainerStyle={{ paddingBottom: 20 }}
            keyboardShouldPersistTaps="handled"
          >
            {/* Manual Mode: Stock Search */}
            {mode === 'manual' && (
              <View style={{ marginBottom: theme.spacing.md }}>
                <Text style={[styles.label, { color: theme.colors.text.secondary }]}>
                  Sök Aktie *
                </Text>
                <TextInput
                  style={[styles.input, {
                    backgroundColor: theme.colors.background.secondary,
                    borderColor: theme.colors.border.primary,
                    color: theme.colors.text.primary
                  }]}
                  placeholder="Sök företag eller ticker..."
                  placeholderTextColor={theme.colors.text.tertiary}
                  value={searchQuery}
                  onChangeText={setSearchQuery}
                  autoCapitalize="characters"
                />

                {/* Search Results */}
                {searchResults.length > 0 && (
                  <View style={[styles.searchResults, {
                    backgroundColor: theme.colors.background.secondary,
                    borderColor: theme.colors.primary
                  }]}>
                    {searchResults.map((stock, index) => (
                      <TouchableOpacity
                        key={`${stock.ticker}-${index}`}
                        style={[styles.searchResultItem, {
                          borderBottomColor: theme.colors.border.primary,
                          borderBottomWidth: index < searchResults.length - 1 ? 1 : 0
                        }]}
                        onPress={() => selectStock(stock)}
                      >
                        <Text style={[styles.resultTicker, { color: theme.colors.text.primary }]}>
                          {stock.ticker}
                        </Text>
                        <Text style={[styles.resultName, { color: theme.colors.text.secondary }]} numberOfLines={1}>
                          {stock.name}
                        </Text>
                      </TouchableOpacity>
                    ))}
                  </View>
                )}
              </View>
            )}

            {/* From Signal Mode: Show Ticker */}
            {mode === 'from-signal' && (
              <View style={{ marginBottom: theme.spacing.md }}>
                <Text style={[styles.label, { color: theme.colors.text.secondary }]}>
                  Aktie
                </Text>
                <View style={[styles.readOnlyInput, {
                  backgroundColor: theme.colors.alpha(theme.colors.primary, 0.1),
                  borderColor: theme.colors.primary
                }]}>
                  <Text style={[styles.readOnlyText, { color: theme.colors.text.primary }]}>
                    {ticker}
                  </Text>
                </View>
              </View>
            )}

            {/* Entry Price */}
            <View style={{ marginBottom: theme.spacing.md }}>
              <Text style={[styles.label, { color: theme.colors.text.secondary }]}>
                Entry Price (kr) *
              </Text>
              <TextInput
                style={[styles.input, {
                  backgroundColor: theme.colors.background.secondary,
                  borderColor: theme.colors.border.primary,
                  color: theme.colors.text.primary
                }]}
                placeholder="0.00"
                placeholderTextColor={theme.colors.text.tertiary}
                value={entryPrice}
                onChangeText={setEntryPrice}
                keyboardType="decimal-pad"
              />
            </View>

            {/* Shares */}
            <View style={{ marginBottom: theme.spacing.md }}>
              <Text style={[styles.label, { color: theme.colors.text.secondary }]}>
                Antal Aktier *
              </Text>
              <TextInput
                style={[styles.input, {
                  backgroundColor: theme.colors.background.secondary,
                  borderColor: theme.colors.border.primary,
                  color: theme.colors.text.primary
                }]}
                placeholder="0"
                placeholderTextColor={theme.colors.text.tertiary}
                value={shares}
                onChangeText={setShares}
                keyboardType="number-pad"
              />
            </View>

            {/* Stop Loss */}
            <View style={{ marginBottom: theme.spacing.md }}>
              <Text style={[styles.label, { color: theme.colors.text.secondary }]}>
                Stop Loss (kr) *
              </Text>
              <TextInput
                style={[styles.input, {
                  backgroundColor: theme.colors.background.secondary,
                  borderColor: theme.colors.border.primary,
                  color: theme.colors.text.primary
                }]}
                placeholder="0.00"
                placeholderTextColor={theme.colors.text.tertiary}
                value={stopLoss}
                onChangeText={setStopLoss}
                keyboardType="decimal-pad"
              />
            </View>

            {/* Targets */}
            <Card variant="elevated" style={{ padding: theme.spacing.md, marginBottom: theme.spacing.md }}>
              <Text style={[styles.sectionTitle, { color: theme.colors.text.primary }]}>
                Price Targets
              </Text>

              <View style={{ marginTop: theme.spacing.sm }}>
                <Text style={[styles.label, { color: theme.colors.text.secondary }]}>
                  Target 1 (kr) *
                </Text>
                <TextInput
                  style={[styles.input, {
                    backgroundColor: theme.colors.background.secondary,
                    borderColor: theme.colors.border.primary,
                    color: theme.colors.text.primary
                  }]}
                  placeholder="0.00"
                  placeholderTextColor={theme.colors.text.tertiary}
                  value={target1}
                  onChangeText={setTarget1}
                  keyboardType="decimal-pad"
                />
              </View>

              <View style={{ marginTop: theme.spacing.sm }}>
                <Text style={[styles.label, { color: theme.colors.text.secondary }]}>
                  Target 2 (kr)
                </Text>
                <TextInput
                  style={[styles.input, {
                    backgroundColor: theme.colors.background.secondary,
                    borderColor: theme.colors.border.primary,
                    color: theme.colors.text.primary
                  }]}
                  placeholder="0.00 (optional)"
                  placeholderTextColor={theme.colors.text.tertiary}
                  value={target2}
                  onChangeText={setTarget2}
                  keyboardType="decimal-pad"
                />
              </View>

              <View style={{ marginTop: theme.spacing.sm }}>
                <Text style={[styles.label, { color: theme.colors.text.secondary }]}>
                  Target 3 (kr)
                </Text>
                <TextInput
                  style={[styles.input, {
                    backgroundColor: theme.colors.background.secondary,
                    borderColor: theme.colors.border.primary,
                    color: theme.colors.text.primary
                  }]}
                  placeholder="0.00 (optional)"
                  placeholderTextColor={theme.colors.text.tertiary}
                  value={target3}
                  onChangeText={setTarget3}
                  keyboardType="decimal-pad"
                />
              </View>
            </Card>
          </ScrollView>

          {/* Footer Buttons */}
          <View style={[styles.footer, { borderTopColor: theme.colors.border.primary }]}>
            <TouchableOpacity
              style={[styles.cancelButton, {
                borderColor: theme.colors.border.primary,
                backgroundColor: theme.colors.background.secondary
              }]}
              onPress={handleClose}
            >
              <Text style={[styles.cancelButtonText, { color: theme.colors.text.primary }]}>
                Avbryt
              </Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={[styles.submitButton, { backgroundColor: theme.colors.primary }]}
              onPress={handleSubmit}
              disabled={loading}
            >
              <Text style={styles.submitButtonText}>
                {loading ? 'Sparar...' : 'Lägg till Position'}
              </Text>
            </TouchableOpacity>
          </View>
        </View>
      </KeyboardAvoidingView>
    </Modal>
  );
}

const styles = StyleSheet.create({
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    height: '90%',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: -2 },
    shadowOpacity: 0.25,
    shadowRadius: 10,
    elevation: 10,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    borderBottomWidth: 1,
  },
  title: {
    fontSize: 20,
    fontWeight: '700',
  },
  scrollView: {
    flex: 1,
    padding: 20,
  },
  label: {
    fontSize: 13,
    fontWeight: '600',
    marginBottom: 8,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  input: {
    borderWidth: 1,
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
  },
  readOnlyInput: {
    borderWidth: 1.5,
    borderRadius: 8,
    padding: 12,
  },
  readOnlyText: {
    fontSize: 16,
    fontWeight: '600',
  },
  searchResults: {
    marginTop: 8,
    borderWidth: 2,
    borderRadius: 8,
    maxHeight: 200,
  },
  searchResultItem: {
    padding: 12,
  },
  resultTicker: {
    fontSize: 16,
    fontWeight: '700',
    marginBottom: 4,
  },
  resultName: {
    fontSize: 13,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '700',
    marginBottom: 8,
  },
  footer: {
    flexDirection: 'row',
    padding: 20,
    gap: 12,
    borderTopWidth: 1,
  },
  cancelButton: {
    flex: 1,
    paddingVertical: 14,
    borderRadius: 10,
    borderWidth: 1.5,
    alignItems: 'center',
  },
  cancelButtonText: {
    fontSize: 16,
    fontWeight: '600',
  },
  submitButton: {
    flex: 2,
    paddingVertical: 14,
    borderRadius: 10,
    alignItems: 'center',
  },
  submitButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '700',
  },
});
