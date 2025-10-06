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
import { LineChart, CandlestickChart } from 'react-native-wagmi-charts';
import { useTheme } from '../theme/ThemeContext';
import { Card, PriceText, Button } from '../components';
import { api } from '../api/client';

const { width } = Dimensions.get('window');

export default function StockDetailScreen({ route, navigation }) {
  const { ticker, market = 'SE' } = route.params;
  const { theme } = useTheme();

  const [loading, setLoading] = useState(true);
  const [chartData, setChartData] = useState([]);
  const [candleData, setCandleData] = useState([]);
  const [volumeData, setVolumeData] = useState([]);
  const [rsiData, setRsiData] = useState([]);
  const [macdData, setMacdData] = useState([]);
  const [ema20Data, setEma20Data] = useState([]);
  const [sma50Data, setSma50Data] = useState([]);
  const [stockInfo, setStockInfo] = useState(null);
  const [currentPrice, setCurrentPrice] = useState(null);
  const [period, setPeriod] = useState('3mo');
  const [chartType, setChartType] = useState('candle'); // 'line' or 'candle'
  const [showRSI, setShowRSI] = useState(true);
  const [showMACD, setShowMACD] = useState(false);
  const [showEMA20, setShowEMA20] = useState(true);
  const [showSMA50, setShowSMA50] = useState(true);

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

      // Transform data for line chart
      const lineData = data.map(item => ({
        timestamp: item.timestamp,
        value: item.close,
      }));
      setChartData(lineData);

      // Transform data for candlestick chart
      const candleData = data.map(item => ({
        timestamp: item.timestamp,
        open: item.open,
        high: item.high,
        low: item.low,
        close: item.close,
      }));
      setCandleData(candleData);

      // Transform data for volume bars
      const volData = data.map(item => ({
        timestamp: item.timestamp,
        value: item.volume,
      }));
      setVolumeData(volData);

      // Transform data for RSI
      const rsiData = data
        .filter(item => item.rsi !== undefined)
        .map(item => ({
          timestamp: item.timestamp,
          value: item.rsi,
        }));
      setRsiData(rsiData);

      // Transform data for MACD
      const macdData = data
        .filter(item => item.macd !== undefined)
        .map(item => ({
          timestamp: item.timestamp,
          macd: item.macd.macd,
          signal: item.macd.signal,
          histogram: item.macd.histogram,
        }));
      setMacdData(macdData);

      // Transform data for EMA20
      const ema20Data = data
        .filter(item => item.ema20 !== undefined)
        .map(item => ({
          timestamp: item.timestamp,
          value: item.ema20,
        }));
      setEma20Data(ema20Data);

      // Transform data for SMA50
      const sma50Data = data
        .filter(item => item.sma50 !== undefined)
        .map(item => ({
          timestamp: item.timestamp,
          value: item.sma50,
        }));
      setSma50Data(sma50Data);

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

      {/* Chart Type Selector */}
      <View style={[styles.chartTypeSelector, { paddingHorizontal: theme.spacing.base, marginTop: theme.spacing.md }]}>
        <TouchableOpacity
          onPress={() => setChartType('candle')}
          style={[
            styles.chartTypeButton,
            {
              backgroundColor:
                chartType === 'candle'
                  ? theme.colors.alpha(theme.colors.primary, 0.2)
                  : 'transparent',
              borderColor:
                chartType === 'candle'
                  ? theme.colors.primary
                  : theme.colors.border.primary,
            },
          ]}
        >
          <Text
            style={[
              styles.chartTypeText,
              {
                color:
                  chartType === 'candle'
                    ? theme.colors.primary
                    : theme.colors.text.secondary,
                fontWeight: chartType === 'candle' ? '700' : '400',
              },
            ]}
          >
            Candles
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          onPress={() => setChartType('line')}
          style={[
            styles.chartTypeButton,
            {
              backgroundColor:
                chartType === 'line'
                  ? theme.colors.alpha(theme.colors.primary, 0.2)
                  : 'transparent',
              borderColor:
                chartType === 'line'
                  ? theme.colors.primary
                  : theme.colors.border.primary,
            },
          ]}
        >
          <Text
            style={[
              styles.chartTypeText,
              {
                color:
                  chartType === 'line'
                    ? theme.colors.primary
                    : theme.colors.text.secondary,
                fontWeight: chartType === 'line' ? '700' : '400',
              },
            ]}
          >
            Line
          </Text>
        </TouchableOpacity>
      </View>

      {/* Period Selector */}
      <View style={[styles.periodSelector, { paddingHorizontal: theme.spacing.base, marginTop: theme.spacing.sm }]}>
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

      {/* Indicator Toggles */}
      <View style={[styles.indicatorToggles, { paddingHorizontal: theme.spacing.base, marginTop: theme.spacing.sm }]}>
        <Text style={[styles.indicatorLabel, { color: theme.colors.text.secondary }]}>
          Indicators:
        </Text>
        <TouchableOpacity
          onPress={() => setShowEMA20(!showEMA20)}
          style={[
            styles.indicatorToggle,
            {
              backgroundColor: showEMA20
                ? theme.colors.alpha(theme.colors.bullish, 0.2)
                : 'transparent',
              borderColor: showEMA20
                ? theme.colors.bullish
                : theme.colors.border.primary,
            },
          ]}
        >
          <Text
            style={[
              styles.indicatorToggleText,
              {
                color: showEMA20 ? theme.colors.bullish : theme.colors.text.secondary,
                fontWeight: showEMA20 ? '600' : '400',
              },
            ]}
          >
            EMA20
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          onPress={() => setShowSMA50(!showSMA50)}
          style={[
            styles.indicatorToggle,
            {
              backgroundColor: showSMA50
                ? theme.colors.alpha(theme.colors.warning, 0.2)
                : 'transparent',
              borderColor: showSMA50
                ? theme.colors.warning
                : theme.colors.border.primary,
            },
          ]}
        >
          <Text
            style={[
              styles.indicatorToggleText,
              {
                color: showSMA50 ? theme.colors.warning : theme.colors.text.secondary,
                fontWeight: showSMA50 ? '600' : '400',
              },
            ]}
          >
            SMA50
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          onPress={() => setShowRSI(!showRSI)}
          style={[
            styles.indicatorToggle,
            {
              backgroundColor: showRSI
                ? theme.colors.alpha(theme.colors.primary, 0.2)
                : 'transparent',
              borderColor: showRSI
                ? theme.colors.primary
                : theme.colors.border.primary,
            },
          ]}
        >
          <Text
            style={[
              styles.indicatorToggleText,
              {
                color: showRSI ? theme.colors.primary : theme.colors.text.secondary,
                fontWeight: showRSI ? '600' : '400',
              },
            ]}
          >
            RSI
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          onPress={() => setShowMACD(!showMACD)}
          style={[
            styles.indicatorToggle,
            {
              backgroundColor: showMACD
                ? theme.colors.alpha(theme.colors.primary, 0.2)
                : 'transparent',
              borderColor: showMACD
                ? theme.colors.primary
                : theme.colors.border.primary,
            },
          ]}
        >
          <Text
            style={[
              styles.indicatorToggleText,
              {
                color: showMACD ? theme.colors.primary : theme.colors.text.secondary,
                fontWeight: showMACD ? '600' : '400',
              },
            ]}
          >
            MACD
          </Text>
        </TouchableOpacity>
      </View>

      {/* Chart */}
      <View style={[styles.chartContainer, { marginTop: theme.spacing.md }]}>
        {/* MA Legend */}
        {(showEMA20 || showSMA50) && (
          <View style={[styles.maLegend, { paddingHorizontal: theme.spacing.base, marginBottom: theme.spacing.xs }]}>
            {showEMA20 && ema20Data.length > 0 && (
              <View style={styles.maLegendItem}>
                <View style={[styles.maLegendLine, { backgroundColor: theme.colors.bullish }]} />
                <Text style={[styles.maLegendText, { color: theme.colors.text.secondary }]}>
                  EMA20: {ema20Data[ema20Data.length - 1].value.toFixed(2)}
                </Text>
              </View>
            )}
            {showSMA50 && sma50Data.length > 0 && (
              <View style={styles.maLegendItem}>
                <View style={[styles.maLegendLine, { backgroundColor: theme.colors.warning }]} />
                <Text style={[styles.maLegendText, { color: theme.colors.text.secondary }]}>
                  SMA50: {sma50Data[sma50Data.length - 1].value.toFixed(2)}
                </Text>
              </View>
            )}
          </View>
        )}
        {chartType === 'candle' && candleData.length > 0 ? (
          <CandlestickChart.Provider data={candleData}>
            <CandlestickChart width={width} height={300}>
              <CandlestickChart.Candles
                positiveColor={theme.colors.bullish}
                negativeColor={theme.colors.bearish}
              />
              <CandlestickChart.Crosshair>
                <CandlestickChart.Tooltip />
              </CandlestickChart.Crosshair>
            </CandlestickChart>
          </CandlestickChart.Provider>
        ) : chartType === 'line' && chartData.length > 0 ? (
          <LineChart.Provider data={chartData}>
            <LineChart width={width} height={300}>
              <LineChart.Path color={theme.colors.primary} width={2} />
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

        {/* Moving Average Overlays */}
        {showEMA20 && ema20Data.length > 0 && (
          <View style={{ position: 'absolute', top: 0 }}>
            <LineChart.Provider data={ema20Data}>
              <LineChart width={width} height={300}>
                <LineChart.Path color={theme.colors.bullish} width={1.5} />
              </LineChart>
            </LineChart.Provider>
          </View>
        )}
        {showSMA50 && sma50Data.length > 0 && (
          <View style={{ position: 'absolute', top: 0 }}>
            <LineChart.Provider data={sma50Data}>
              <LineChart width={width} height={300}>
                <LineChart.Path color={theme.colors.warning} width={1.5} />
              </LineChart>
            </LineChart.Provider>
          </View>
        )}

        {/* Volume Chart */}
        {volumeData.length > 0 && (
          <View style={{ marginTop: theme.spacing.md }}>
            <Text style={[styles.volumeTitle, { color: theme.colors.text.secondary, paddingHorizontal: theme.spacing.base }]}>
              VOLUME
            </Text>
            <LineChart.Provider data={volumeData}>
              <LineChart width={width} height={100}>
                <LineChart.Path
                  color={theme.colors.alpha(theme.colors.primary, 0.6)}
                  width={1}
                >
                  <LineChart.Gradient color={theme.colors.primary} />
                </LineChart.Path>
              </LineChart>
            </LineChart.Provider>
          </View>
        )}

        {/* RSI Indicator */}
        {showRSI && rsiData.length > 0 && (
          <View style={{ marginTop: theme.spacing.md }}>
            <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingHorizontal: theme.spacing.base }}>
              <Text style={[styles.volumeTitle, { color: theme.colors.text.secondary, marginBottom: 0 }]}>
                RSI (14)
              </Text>
              {rsiData.length > 0 && (
                <Text style={[styles.indicatorValue, { color: theme.colors.text.primary }]}>
                  {rsiData[rsiData.length - 1].value.toFixed(2)}
                </Text>
              )}
            </View>
            <LineChart.Provider data={rsiData}>
              <LineChart width={width} height={120}>
                <LineChart.Path color={theme.colors.primary} width={2} />
                <LineChart.HorizontalLine at={{ index: 0, value: 70 }} />
                <LineChart.HorizontalLine at={{ index: 0, value: 30 }} />
              </LineChart>
            </LineChart.Provider>
          </View>
        )}

        {/* MACD Indicator */}
        {showMACD && macdData.length > 0 && (
          <View style={{ marginTop: theme.spacing.md }}>
            <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingHorizontal: theme.spacing.base }}>
              <Text style={[styles.volumeTitle, { color: theme.colors.text.secondary, marginBottom: 0 }]}>
                MACD (12, 26, 9)
              </Text>
              {macdData.length > 0 && (
                <View style={{ flexDirection: 'row', gap: 8 }}>
                  <Text style={[styles.indicatorValue, { color: theme.colors.bullish }]}>
                    {macdData[macdData.length - 1].macd?.toFixed(2) || 'N/A'}
                  </Text>
                  <Text style={[styles.indicatorValue, { color: theme.colors.bearish }]}>
                    {macdData[macdData.length - 1].signal?.toFixed(2) || 'N/A'}
                  </Text>
                </View>
              )}
            </View>
            <LineChart.Provider data={macdData.map(d => ({ timestamp: d.timestamp, value: d.macd }))}>
              <LineChart width={width} height={120}>
                <LineChart.Path color={theme.colors.bullish} width={2} />
              </LineChart>
            </LineChart.Provider>
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
  chartTypeSelector: {
    flexDirection: 'row',
    gap: 8,
  },
  chartTypeButton: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
    borderWidth: 1,
    flex: 1,
    alignItems: 'center',
  },
  chartTypeText: {
    fontSize: 13,
    fontWeight: '600',
    letterSpacing: 0.5,
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
  volumeTitle: {
    fontSize: 10,
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 8,
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
  indicatorToggles: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  indicatorLabel: {
    fontSize: 11,
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginRight: 4,
  },
  indicatorToggle: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
    borderWidth: 1,
  },
  indicatorToggleText: {
    fontSize: 11,
    letterSpacing: 0.5,
  },
  indicatorValue: {
    fontSize: 12,
    fontWeight: '600',
    fontFamily: 'Courier',
  },
  maLegend: {
    flexDirection: 'row',
    gap: 12,
    flexWrap: 'wrap',
  },
  maLegendItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  maLegendLine: {
    width: 16,
    height: 2,
    borderRadius: 1,
  },
  maLegendText: {
    fontSize: 10,
    fontWeight: '600',
    fontFamily: 'Courier',
  },
});
