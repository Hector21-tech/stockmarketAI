/**
 * Stock Detail Screen
 * Full-screen chart with technical analysis
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  ActivityIndicator,
  Dimensions,
  TouchableOpacity,
} from 'react-native';
import { LineChart } from 'react-native-wagmi-charts';
import { useTheme } from '../theme/ThemeContext';
import { Card, PriceText, Button } from '../components';
import { api } from '../api/client';

const { width } = Dimensions.get('window');

export default function StockDetailScreen({ route, navigation }) {
  const { ticker, market = 'SE' } = route.params;
  const { theme } = useTheme();

  const [loading, setLoading] = useState(true);
  const [chartData, setChartData] = useState([]);
  const [stockInfo, setStockInfo] = useState(null);
  const [currentPrice, setCurrentPrice] = useState(null);
  const [period, setPeriod] = useState('3mo');

  const periods = [
    { label: '1M', value: '1mo' },
    { label: '3M', value: '3mo' },
    { label: '6M', value: '6mo' },
    { label: '1Y', value: '1y' },
    { label: 'MAX', value: 'max' },
  ];

  useEffect(() => {
    loadStockData();
  }, [ticker, period]);

  const loadStockData = async () => {
    setLoading(true);
    try {
      // Load historical data for chart
      const histResponse = await api.getHistoricalData(ticker, period, '1d', market);
      const data = histResponse.data.data || [];

      // Transform data for wagmi charts
      const chartData = data.map(item => ({
        timestamp: item.timestamp,
        value: item.close,
      }));

      setChartData(chartData);

      // Get current price (last close)
      if (data.length > 0) {
        setCurrentPrice(data[data.length - 1].close);
      }

      // Load stock info
      const infoResponse = await api.getStockInfo(ticker, market);
      setStockInfo(infoResponse.data);
    } catch (error) {
      console.error('Error loading stock data:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (value) => {
    return `${value?.toFixed(2)} SEK`;
  };

  if (loading) {
    return (
      <View style={[styles.loadingContainer, { backgroundColor: theme.colors.background.primary }]}>
        <ActivityIndicator size="large" color={theme.colors.primary} />
        <Text style={[styles.loadingText, { color: theme.colors.text.secondary }]}>
          Loading chart data...
        </Text>
      </View>
    );
  }

  return (
    <ScrollView style={[styles.container, { backgroundColor: theme.colors.background.primary }]}>
      {/* Header */}
      <View style={[styles.header, { paddingHorizontal: theme.spacing.base, paddingTop: theme.spacing.md }]}>
        <Text style={[styles.ticker, { color: theme.colors.text.primary, ...theme.typography.styles.h3 }]}>
          {ticker}
        </Text>
        {currentPrice && (
          <PriceText
            value={currentPrice}
            size="lg"
            suffix=" SEK"
            style={{ marginTop: theme.spacing.xs }}
          />
        )}
      </View>

      {/* Period Selector */}
      <View style={[styles.periodSelector, { paddingHorizontal: theme.spacing.base, marginTop: theme.spacing.md }]}>
        {periods.map((p) => (
          <TouchableOpacity
            key={p.value}
            onPress={() => setPeriod(p.value)}
            style={[
              styles.periodButton,
              {
                backgroundColor:
                  period === p.value
                    ? theme.colors.alpha(theme.colors.primary, 0.2)
                    : 'transparent',
                borderColor:
                  period === p.value
                    ? theme.colors.primary
                    : theme.colors.border.primary,
              },
            ]}
          >
            <Text
              style={[
                styles.periodText,
                {
                  color:
                    period === p.value
                      ? theme.colors.primary
                      : theme.colors.text.secondary,
                  fontWeight: period === p.value ? '700' : '400',
                },
              ]}
            >
              {p.label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Chart */}
      <View style={[styles.chartContainer, { marginTop: theme.spacing.md }]}>
        {chartData.length > 0 ? (
          <LineChart.Provider data={chartData}>
            <LineChart width={width} height={300}>
              <LineChart.Path color={theme.colors.primary} />
              <LineChart.CursorCrosshair>
                <LineChart.Tooltip />
              </LineChart.CursorCrosshair>
            </LineChart>
          </LineChart.Provider>
        ) : (
          <View style={styles.emptyChart}>
            <Text style={[styles.emptyText, { color: theme.colors.text.tertiary }]}>
              No chart data available
            </Text>
          </View>
        )}
      </View>

      {/* Stock Info */}
      {stockInfo && (
        <Card variant="elevated" style={{ margin: theme.spacing.base }}>
          <Text style={[styles.sectionTitle, { color: theme.colors.text.secondary }]}>
            STOCK INFORMATION
          </Text>

          {stockInfo.longName && (
            <View style={[styles.infoRow, { marginTop: theme.spacing.sm }]}>
              <Text style={[styles.infoLabel, { color: theme.colors.text.secondary }]}>
                Company
              </Text>
              <Text style={[styles.infoValue, { color: theme.colors.text.primary }]}>
                {stockInfo.longName}
              </Text>
            </View>
          )}

          {stockInfo.sector && (
            <View style={styles.infoRow}>
              <Text style={[styles.infoLabel, { color: theme.colors.text.secondary }]}>
                Sector
              </Text>
              <Text style={[styles.infoValue, { color: theme.colors.text.primary }]}>
                {stockInfo.sector}
              </Text>
            </View>
          )}

          {stockInfo.industry && (
            <View style={styles.infoRow}>
              <Text style={[styles.infoLabel, { color: theme.colors.text.secondary }]}>
                Industry
              </Text>
              <Text style={[styles.infoValue, { color: theme.colors.text.primary }]}>
                {stockInfo.industry}
              </Text>
            </View>
          )}

          {stockInfo.marketCap && (
            <View style={styles.infoRow}>
              <Text style={[styles.infoLabel, { color: theme.colors.text.secondary }]}>
                Market Cap
              </Text>
              <Text style={[styles.infoValue, { color: theme.colors.text.primary }]}>
                {(stockInfo.marketCap / 1e9).toFixed(2)}B SEK
              </Text>
            </View>
          )}
        </Card>
      )}

      {/* Action Buttons */}
      <View style={{ paddingHorizontal: theme.spacing.base, paddingBottom: theme.spacing.xl }}>
        <Button onPress={() => navigation.goBack()} variant="outline">
          Back to Watchlist
        </Button>
      </View>
    </ScrollView>
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
    paddingBottom: 16,
  },
  ticker: {
    marginBottom: 4,
  },
  periodSelector: {
    flexDirection: 'row',
    gap: 8,
  },
  periodButton: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
    borderWidth: 1,
  },
  periodText: {
    fontSize: 12,
    letterSpacing: 0.5,
  },
  chartContainer: {
    alignItems: 'center',
  },
  emptyChart: {
    width: width,
    height: 300,
    justifyContent: 'center',
    alignItems: 'center',
  },
  emptyText: {
    fontSize: 14,
  },
  sectionTitle: {
    fontSize: 11,
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 8,
  },
  infoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255,255,255,0.05)',
  },
  infoLabel: {
    fontSize: 14,
  },
  infoValue: {
    fontSize: 14,
    fontWeight: '600',
    flex: 1,
    textAlign: 'right',
  },
});
