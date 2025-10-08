/**
 * Stock Detail Screen
 * Simplified version with react-native-gifted-charts for Expo Go compatibility
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
  Alert,
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { LineChart, BarChart } from 'react-native-gifted-charts';
import { useTheme } from '../theme/ThemeContext';
import { Card, PriceText, Button } from '../components';
import { api } from '../api/client';

const { width } = Dimensions.get('window');

export default function StockDetailScreen({ route, navigation }) {
  const { ticker, market = 'SE' } = route.params;
  const { theme } = useTheme();

  const [loading, setLoading] = useState(true);
  const [chartData, setChartData] = useState([]);
  const [volumeData, setVolumeData] = useState([]);
  const [rsiData, setRsiData] = useState([]);
  const [macdData, setMacdData] = useState({ macd: [], signal: [] });
  const [stochasticData, setStochasticData] = useState({ k: [], d: [] });
  const [stockInfo, setStockInfo] = useState(null);
  const [currentPrice, setCurrentPrice] = useState(null);
  const [period, setPeriod] = useState('3mo');
  const [bottomIndicator, setBottomIndicator] = useState('volume'); // 'volume' | 'rsi' | 'macd' | 'stochastic' | 'none'
  const [isInWatchlist, setIsInWatchlist] = useState(false);
  const [signalMode, setSignalMode] = useState('conservative');

  const periods = [
    { label: '1V', value: '5d' },
    { label: '1M', value: '1mo' },
    { label: '3M', value: '3mo' },
    { label: '6M', value: '6mo' },
    { label: 'ÅR', value: 'ytd' },
    { label: '1Å', value: '1y' },
    { label: '5Å', value: '5y' },
  ];

  useEffect(() => {
    loadStockData();
    checkWatchlistStatus();
    loadSignalMode();
  }, [ticker, period]);

  const loadSignalMode = async () => {
    try {
      const response = await api.getCurrentSignalMode();
      setSignalMode(response.data.mode);
    } catch (error) {
      console.error('Error loading signal mode:', error);
    }
  };

  const checkWatchlistStatus = async () => {
    try {
      const watchlistJson = await AsyncStorage.getItem('watchlist');
      if (watchlistJson) {
        const watchlist = JSON.parse(watchlistJson);
        // Watchlist is an array of strings (tickers)
        setIsInWatchlist(watchlist.includes(ticker));
      }
    } catch (error) {
      console.error('Error checking watchlist:', error);
    }
  };

  const toggleWatchlist = async () => {
    try {
      const watchlistJson = await AsyncStorage.getItem('watchlist');
      let watchlist = watchlistJson ? JSON.parse(watchlistJson) : [];

      if (isInWatchlist) {
        // Remove from watchlist
        watchlist = watchlist.filter(item => item !== ticker);
        Alert.alert('Borttagen', `${ticker} borttagen från watchlist`);
      } else {
        // Add to watchlist
        watchlist.push(ticker);
        Alert.alert('Tillagd!', `${ticker} tillagd i watchlist`);
      }

      await AsyncStorage.setItem('watchlist', JSON.stringify(watchlist));
      setIsInWatchlist(!isInWatchlist);
    } catch (error) {
      console.error('Error toggling watchlist:', error);
      Alert.alert('Fel', 'Kunde inte uppdatera watchlist');
    }
  };

  // Helper function to format date labels in Swedish (Avanza-style)
  const formatDateLabel = (timestamp, periodType) => {
    if (!timestamp) return '';

    const date = new Date(timestamp);
    if (isNaN(date.getTime())) return ''; // Invalid date

    const day = date.getDate();
    const monthNames = ['jan', 'feb', 'mar', 'apr', 'maj', 'jun', 'jul', 'aug', 'sep', 'okt', 'nov', 'dec'];
    const month = monthNames[date.getMonth()];
    const weekdayNames = ['sön', 'mån', 'tis', 'ons', 'tor', 'fre', 'lör'];
    const weekday = weekdayNames[date.getDay()];
    const year = String(date.getFullYear()).slice(-2); // Last 2 digits of year (e.g., "25")
    const fullYear = date.getFullYear(); // Full year (e.g., "2025")

    if (periodType === '5d') {
      // Very short: weekday + day (e.g., "mån 6")
      return `${weekday} ${day}`;
    } else if (periodType === '1mo') {
      // Short: day + month (e.g., "6 jan")
      return `${day} ${month}`;
    } else if (periodType === '3mo' || periodType === '6mo' || periodType === 'ytd' || periodType === '1y') {
      // Medium/Long: month + year (e.g., "jan 25") - AVANZA STYLE
      return `${month} ${year}`;
    } else {
      // Very long (5y): full year (e.g., "2020")
      return String(fullYear);
    }
  };

  // Helper function to format date range display (always shows day + month)
  const formatDateRange = (timestamp) => {
    if (!timestamp) return '';

    const date = new Date(timestamp);
    if (isNaN(date.getTime())) return '';

    const day = date.getDate();
    const monthNames = ['jan', 'feb', 'mar', 'apr', 'maj', 'jun', 'jul', 'aug', 'sep', 'okt', 'nov', 'dec'];
    const month = monthNames[date.getMonth()];
    return `${day} ${month}`;
  };

  const loadStockData = async () => {
    try {
      setLoading(true);

      // Always use daily candles for swing trading
      const interval = '1d';

      // Fetch historical data
      const response = await api.getHistoricalData(ticker, period, interval, market);
      const data = response.data.data;

      console.log(`📊 Chart data loaded: ${data.length} points for period ${period}`);

      // Transform for line chart - NO LABELS (we'll render custom labels outside chart)
      const lineData = data.map((item, index) => {
        return {
          value: item.close,
          label: '', // Empty - we render labels separately
          dataPointText: item.close.toFixed(2),
          timestamp: item.timestamp,
        };
      });
      setChartData(lineData);
      console.log('✅ LineChart data set:', lineData.length, 'points');

      // Transform for volume chart - NO LABELS (we'll render custom labels outside chart)
      const volData = data.map((item, index) => {
        return {
          value: item.volume / 1000000,
          label: '', // Empty - we render labels separately
          frontColor: theme.colors.alpha(theme.colors.primary, 0.6),
        };
      });
      setVolumeData(volData);
      console.log('✅ Volume data set:', volData.length, 'bars');

      // Transform RSI data
      const rsi = data
        .filter(item => item.rsi !== undefined)
        .map((item, index) => ({
          value: item.rsi,
          label: '',
        }));
      setRsiData(rsi);

      // Transform MACD data
      const macdLine = data
        .filter(item => item.macd !== undefined)
        .map((item, index) => ({
          value: item.macd.macd,
          label: '',
        }));
      const signalLine = data
        .filter(item => item.macd !== undefined)
        .map((item, index) => ({
          value: item.macd.signal,
          label: '',
        }));
      setMacdData({ macd: macdLine, signal: signalLine });
      console.log('✅ MACD data set:', macdLine.length, 'points');

      // Transform Stochastic data
      const kLine = data
        .filter(item => item.stochastic !== undefined)
        .map((item, index) => ({
          value: item.stochastic.k,
          label: '',
        }));
      const dLine = data
        .filter(item => item.stochastic !== undefined)
        .map((item, index) => ({
          value: item.stochastic.d,
          label: '',
        }));
      setStochasticData({ k: kLine, d: dLine });
      console.log('✅ Stochastic data set:', kLine.length, 'points');

      // Get current price
      if (data.length > 0) {
        setCurrentPrice(data[data.length - 1].close);
      }

      // Load stock info
      const infoResponse = await api.getStockInfo(ticker, market);
      setStockInfo(infoResponse.data);
    } catch (error) {
      console.error('Error loading stock data:', error);
      Alert.alert('Error', 'Failed to load chart data');
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyze = async () => {
    try {
      const response = await api.analyzeStock(ticker, market, signalMode);
      const data = response.data;

      // Extract from correct structure
      const signal = data.signal;
      const trade = data.trade_setup;
      const analysis = data.analysis;
      const macro = data.macro_context;

      // Build comprehensive analysis message
      const techScore = signal.technical_score ?? 0;
      const macroScore = signal.macro_score ?? 5;
      const totalScore = signal.score ?? 0;

      // Dynamisk formula baserad på mode
      const techWeight = signalMode === 'aggressive' ? '0.85' : '0.7';
      const macroWeight = signalMode === 'aggressive' ? '0.15' : '0.3';
      const modeIcon = signalMode === 'aggressive' ? '⚡' : '🛡️';
      const modeName = signalMode === 'aggressive' ? 'AGGRESSIVE' : 'CONSERVATIVE';

      const message = `
🎯 TOTAL SCORE: ${totalScore}/10 — ${signal.strength}
   Technical: ${techScore}/10
   Macro: ${macroScore}/10
   Formula: (Tech*${techWeight}) + (Macro*${macroWeight})
   Mode: ${modeIcon} ${modeName}

📊 SIGNAL: ${signal.action}
${signal.summary}

💰 TRADE SETUP:
Entry: ${trade.entry ? trade.entry.toFixed(2) : 'N/A'} SEK
Target 1: ${trade.targets?.target_1?.price?.toFixed(2) ?? 'N/A'} SEK (+${trade.targets?.target_1?.gain_percent ?? 0}%)
Target 2: ${trade.targets?.target_2?.price?.toFixed(2) ?? 'N/A'} SEK (+${trade.targets?.target_2?.gain_percent ?? 0}%)
Stop Loss: ${trade.stop_loss?.toFixed(2) ?? 'N/A'} SEK
R/R: ${trade.risk_reward?.toFixed(2) ?? 'N/A'}:1

📈 TEKNISK ANALYS:
Trend: ${analysis.trend.toUpperCase()} (Pris: ${analysis.price.toFixed(2)} / EMA20: ${analysis.ema_20.toFixed(2)})
RSI: ${analysis.rsi.toFixed(1)} — ${analysis.rsi_status} (${analysis.rsi_divergence} divergence)
MACD: ${analysis.macd.crossover} crossover
Stochastic: %K=${analysis.stochastic.k.toFixed(1)} — ${analysis.stochastic.status}
Volym: ${(analysis.volume / 1000000).toFixed(2)}M

🌍 MAKRO CONTEXT:
Regime: ${macro.regime?.toUpperCase() ?? 'Unknown'}
VIX: ${macro.vix?.toFixed(2) ?? 'N/A'} (${macro.fear_greed ?? 'N/A'})
Macro Score: ${macro.macro_score ?? 5}/10 — ${macro.macro_classification ?? 'Unknown'}

✅ ANLEDNINGAR:
${signal.reasons.map((r, i) => `${i + 1}. ${r}`).join('\n')}

⏱ TIDSHORISONT: ${trade.risk_reward >= 2 ? 'Medellång (2-4 veckor)' : 'Kort (1-2 veckor)'}
      `.trim();

      Alert.alert(`${ticker} — ${signal.action} Signal`, message, [
        { text: 'Lägg till Position', onPress: handleAddPosition },
        { text: 'Stäng', style: 'cancel' }
      ]);
    } catch (error) {
      console.error('Error analyzing stock:', error);
      Alert.alert('Fel', 'Kunde inte analysera aktie');
    }
  };

  const handleAddPosition = () => {
    Alert.alert('Lägg till Position', 'Position modal kommer snart!', [
      { text: 'OK' }
    ]);
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
      <View style={[styles.header, { paddingHorizontal: theme.spacing.base }]}>
        <View style={styles.headerRow}>
          <View>
            <Text style={[styles.ticker, { color: theme.colors.text.primary }]}>
              {ticker}
            </Text>
            {stockInfo?.name && (
              <Text style={[styles.companyName, { color: theme.colors.text.secondary }]}>
                {stockInfo.name}
              </Text>
            )}
          </View>
          <TouchableOpacity onPress={toggleWatchlist}>
            <Text style={{ fontSize: 24, color: theme.colors.primary }}>
              {isInWatchlist ? '★' : '☆'}
            </Text>
          </TouchableOpacity>
        </View>
        {currentPrice && (
          <PriceText
            value={currentPrice}
            size="lg"
            suffix=" SEK"
            style={{ marginTop: theme.spacing.xs }}
          />
        )}
      </View>

      {/* Period Selector - Horizontal Scroll */}
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        style={[styles.periodSelector, { paddingHorizontal: theme.spacing.base }]}
        contentContainerStyle={{ gap: 8 }}
      >
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
                borderColor: theme.colors.border.primary,
              },
            ]}
          >
            <Text
              style={[
                styles.periodButtonText,
                {
                  color:
                    period === p.value
                      ? theme.colors.primary
                      : theme.colors.text.secondary,
                },
              ]}
            >
              {p.label}
            </Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      {/* Indicator Selector */}
      <View style={[styles.indicatorSelector, { paddingHorizontal: theme.spacing.base, marginTop: theme.spacing.sm }]}>
        {[
          { label: 'Volume', value: 'volume' },
          { label: 'RSI', value: 'rsi' },
          { label: 'MACD', value: 'macd' },
          { label: 'Stoch', value: 'stochastic' },
        ].map((ind) => (
          <TouchableOpacity
            key={ind.value}
            onPress={() => setBottomIndicator(ind.value)}
            style={[
              styles.indicatorButton,
              {
                backgroundColor:
                  bottomIndicator === ind.value
                    ? theme.colors.alpha(theme.colors.primary, 0.2)
                    : theme.colors.background.secondary,
                borderColor: theme.colors.border.primary,
              },
            ]}
          >
            <Text
              style={[
                styles.indicatorButtonText,
                {
                  color:
                    bottomIndicator === ind.value
                      ? theme.colors.primary
                      : theme.colors.text.secondary,
                },
              ]}
            >
              {ind.label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Combined Price & Volume Chart */}
      <Card style={{ margin: theme.spacing.base }}>
        <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: theme.spacing.md }}>
          <Text style={[styles.chartTitle, { color: theme.colors.text.primary }]}>
            Price Chart
          </Text>
          {chartData.length > 1 && (
            <Text style={{ color: theme.colors.text.tertiary, fontSize: 10 }}>
              {formatDateRange(chartData[0].timestamp || Date.now())}
              {' - '}
              {formatDateRange(chartData[chartData.length - 1].timestamp || Date.now())}
            </Text>
          )}
        </View>
        {chartData.length > 0 ? (
          (() => {
            const values = chartData.map(d => d.value);
            const minPrice = Math.min(...values);
            const maxPrice = Math.max(...values);
            const priceRange = maxPrice - minPrice;
            const padding = priceRange * 0.05;

            console.log('📊 Chart range:', { minPrice, maxPrice, priceRange, padding });

            return (
              <View>
                {/* Price Chart */}
                <LineChart
                  data={chartData.map(d => ({ ...d, value: d.value - minPrice + padding }))}
                  width={width - 80}
                  height={220}
                  color={theme.colors.primary}
                  thickness={2}
                  startFillColor={theme.colors.alpha(theme.colors.primary, 0.15)}
                  endFillColor={theme.colors.alpha(theme.colors.primary, 0.01)}
                  startOpacity={0.3}
                  endOpacity={0.05}
                  areaChart
                  curved
                  hideDataPoints={chartData.length > 50}
                  dataPointsColor={theme.colors.primary}
                  dataPointsRadius={3}
                  hideRules={false}
                  rulesColor={theme.colors.alpha(theme.colors.border.primary, 0.3)}
                  rulesType="solid"
                  yAxisColor={theme.colors.border.primary}
                  xAxisColor={theme.colors.border.primary}
                  yAxisTextStyle={{ color: theme.colors.text.tertiary, fontSize: 11 }}
                  xAxisLabelTextStyle={{ color: theme.colors.text.tertiary, fontSize: 10 }}
                  noOfSections={4}
                  maxValue={priceRange + padding * 2}
                  formatYLabel={(value) => {
                    const actualValue = parseFloat(value) + minPrice - padding;
                    return actualValue.toFixed(1);
                  }}
                  initialSpacing={10}
                  spacing={(width - 100) / Math.max(chartData.length - 1, 1)}
                />

                {/* Custom Date Labels - Rendered separately for perfect spacing */}
                <View style={{ flexDirection: 'row', justifyContent: 'space-between', marginLeft: 38, marginRight: 8, marginTop: 4 }}>
                  <Text style={{ color: theme.colors.text.tertiary, fontSize: 10 }}>
                    {chartData.length > 0 ? formatDateLabel(chartData[0].timestamp, period) : ''}
                  </Text>
                  <Text style={{ color: theme.colors.text.tertiary, fontSize: 10 }}>
                    {chartData.length > 0 ? formatDateLabel(chartData[Math.floor(chartData.length / 2)].timestamp, period) : ''}
                  </Text>
                  <Text style={{ color: theme.colors.text.tertiary, fontSize: 10 }}>
                    {chartData.length > 0 ? formatDateLabel(chartData[chartData.length - 1].timestamp, period) : ''}
                  </Text>
                </View>

                {/* Bottom Indicator Panel */}
                {bottomIndicator !== 'none' && (
                  <View style={{ marginTop: theme.spacing.md }}>
                    {/* Volume */}
                    {bottomIndicator === 'volume' && volumeData.length > 0 && (
                      <View>
                        <Text style={[styles.indicatorLabel, { color: theme.colors.text.tertiary, fontSize: 10, marginBottom: 6 }]}>
                          Volume (M)
                        </Text>
                        <BarChart
                          data={volumeData}
                          width={width - 80}
                          height={80}
                          barWidth={Math.max(2, (width - 100) / volumeData.length - 2)}
                          noOfSections={3}
                          hideRules={false}
                          rulesColor={theme.colors.alpha(theme.colors.border.primary, 0.2)}
                          yAxisColor={theme.colors.border.primary}
                          xAxisColor={theme.colors.border.primary}
                          yAxisTextStyle={{ color: theme.colors.text.tertiary, fontSize: 9 }}
                          xAxisLabelTextStyle={{ color: theme.colors.text.tertiary, fontSize: 10 }}
                          initialSpacing={10}
                          spacing={(width - 100) / Math.max(volumeData.length - 1, 1)}
                          showGradient
                          gradientColor={theme.colors.alpha(theme.colors.primary, 0.6)}
                          maxValue={Math.max(...volumeData.map(d => d.value)) * 1.15}
                        />
                        {/* Custom Date Labels for Volume */}
                        <View style={{ flexDirection: 'row', justifyContent: 'space-between', marginLeft: 38, marginRight: 8, marginTop: 4 }}>
                          <Text style={{ color: theme.colors.text.tertiary, fontSize: 10 }}>
                            {chartData.length > 0 ? formatDateLabel(chartData[0].timestamp, period) : ''}
                          </Text>
                          <Text style={{ color: theme.colors.text.tertiary, fontSize: 10 }}>
                            {chartData.length > 0 ? formatDateLabel(chartData[Math.floor(chartData.length / 2)].timestamp, period) : ''}
                          </Text>
                          <Text style={{ color: theme.colors.text.tertiary, fontSize: 10 }}>
                            {chartData.length > 0 ? formatDateLabel(chartData[chartData.length - 1].timestamp, period) : ''}
                          </Text>
                        </View>
                      </View>
                    )}

                    {/* RSI */}
                    {bottomIndicator === 'rsi' && rsiData.length > 0 && (
                      <View>
                        <Text style={[styles.indicatorLabel, { color: theme.colors.text.tertiary, fontSize: 10, marginBottom: 6 }]}>
                          RSI (14)
                        </Text>
                        <View style={{ position: 'relative' }}>
                          {/* RSI Chart */}
                          <LineChart
                            data={rsiData}
                            width={width - 80}
                            height={100}
                            color={theme.colors.primary}
                            thickness={1.5}
                            hideDataPoints
                            hideRules={false}
                            rulesColor={theme.colors.alpha(theme.colors.border.primary, 0.2)}
                            yAxisColor={theme.colors.border.primary}
                            xAxisColor={theme.colors.border.primary}
                            yAxisTextStyle={{ color: theme.colors.text.tertiary, fontSize: 10 }}
                            noOfSections={4}
                            stepValue={25}
                            maxValue={100}
                            yAxisOffset={0}
                            initialSpacing={10}
                            spacing={(width - 100) / Math.max(rsiData.length - 1, 1)}
                          />

                          {/* 70 line - Overbought (dashed effect with dots) */}
                          <View style={{
                            position: 'absolute',
                            left: 38,
                            right: 8,
                            top: '30%',
                            flexDirection: 'row',
                            alignItems: 'center',
                          }}>
                            {[...Array(40)].map((_, i) => (
                              <View
                                key={i}
                                style={{
                                  width: 4,
                                  height: 1,
                                  backgroundColor: theme.colors.alpha(theme.colors.primary, 0.5),
                                  marginRight: 4,
                                }}
                              />
                            ))}
                          </View>

                          {/* 30 line - Oversold (dashed effect with dots) */}
                          <View style={{
                            position: 'absolute',
                            left: 38,
                            right: 8,
                            bottom: '30%',
                            flexDirection: 'row',
                            alignItems: 'center',
                          }}>
                            {[...Array(40)].map((_, i) => (
                              <View
                                key={i}
                                style={{
                                  width: 4,
                                  height: 1,
                                  backgroundColor: theme.colors.alpha(theme.colors.bearish, 0.5),
                                  marginRight: 4,
                                }}
                              />
                            ))}
                          </View>
                        </View>
                        <View style={[styles.rsiLegend, { marginTop: 4 }]}>
                          <Text style={{ color: theme.colors.primary, fontSize: 10 }}>Overbought (70)</Text>
                          <Text style={{ color: theme.colors.bearish, fontSize: 10 }}>Oversold (30)</Text>
                        </View>
                        {/* Custom Date Labels for RSI */}
                        <View style={{ flexDirection: 'row', justifyContent: 'space-between', marginLeft: 38, marginRight: 8, marginTop: 8 }}>
                          <Text style={{ color: theme.colors.text.tertiary, fontSize: 10 }}>
                            {chartData.length > 0 ? formatDateLabel(chartData[0].timestamp, period) : ''}
                          </Text>
                          <Text style={{ color: theme.colors.text.tertiary, fontSize: 10 }}>
                            {chartData.length > 0 ? formatDateLabel(chartData[Math.floor(chartData.length / 2)].timestamp, period) : ''}
                          </Text>
                          <Text style={{ color: theme.colors.text.tertiary, fontSize: 10 }}>
                            {chartData.length > 0 ? formatDateLabel(chartData[chartData.length - 1].timestamp, period) : ''}
                          </Text>
                        </View>
                      </View>
                    )}

                    {/* MACD */}
                    {bottomIndicator === 'macd' && macdData.macd.length > 0 && (
                      <View>
                        <Text style={[styles.indicatorLabel, { color: theme.colors.text.tertiary, fontSize: 10, marginBottom: 6 }]}>
                          MACD (12, 26, 9)
                        </Text>
                        <View style={{ position: 'relative' }}>
                          {/* MACD Line */}
                          <LineChart
                            data={macdData.macd}
                            width={width - 80}
                            height={100}
                            color={theme.colors.primary}
                            thickness={1.5}
                            hideDataPoints
                            hideRules={false}
                            rulesColor={theme.colors.alpha(theme.colors.border.primary, 0.2)}
                            yAxisColor={theme.colors.border.primary}
                            xAxisColor={theme.colors.border.primary}
                            yAxisTextStyle={{ color: theme.colors.text.tertiary, fontSize: 10 }}
                            noOfSections={4}
                            initialSpacing={10}
                            spacing={(width - 100) / Math.max(macdData.macd.length - 1, 1)}
                          />

                          {/* Signal Line Overlay */}
                          <View style={{ position: 'absolute', top: 0, left: 0 }}>
                            <LineChart
                              data={macdData.signal}
                              width={width - 80}
                              height={100}
                              color="#FF9500"
                              thickness={1.5}
                              hideDataPoints
                              hideRules
                              hideAxes
                              noOfSections={4}
                              initialSpacing={10}
                              spacing={(width - 100) / Math.max(macdData.signal.length - 1, 1)}
                            />
                          </View>

                          {/* Zero line (dashed) */}
                          <View style={{
                            position: 'absolute',
                            left: 38,
                            right: 8,
                            top: '50%',
                            flexDirection: 'row',
                            alignItems: 'center',
                          }}>
                            {[...Array(40)].map((_, i) => (
                              <View
                                key={i}
                                style={{
                                  width: 4,
                                  height: 1,
                                  backgroundColor: theme.colors.alpha(theme.colors.text.tertiary, 0.3),
                                  marginRight: 4,
                                }}
                              />
                            ))}
                          </View>
                        </View>
                        <View style={[styles.rsiLegend, { marginTop: 4 }]}>
                          <Text style={{ color: theme.colors.primary, fontSize: 10 }}>MACD Line</Text>
                          <Text style={{ color: '#FF9500', fontSize: 10 }}>Signal Line</Text>
                        </View>
                        {/* Custom Date Labels for MACD */}
                        <View style={{ flexDirection: 'row', justifyContent: 'space-between', marginLeft: 38, marginRight: 8, marginTop: 8 }}>
                          <Text style={{ color: theme.colors.text.tertiary, fontSize: 10 }}>
                            {chartData.length > 0 ? formatDateLabel(chartData[0].timestamp, period) : ''}
                          </Text>
                          <Text style={{ color: theme.colors.text.tertiary, fontSize: 10 }}>
                            {chartData.length > 0 ? formatDateLabel(chartData[Math.floor(chartData.length / 2)].timestamp, period) : ''}
                          </Text>
                          <Text style={{ color: theme.colors.text.tertiary, fontSize: 10 }}>
                            {chartData.length > 0 ? formatDateLabel(chartData[chartData.length - 1].timestamp, period) : ''}
                          </Text>
                        </View>
                      </View>
                    )}

                    {/* Stochastic */}
                    {bottomIndicator === 'stochastic' && stochasticData.k.length > 0 && (
                      <View>
                        <Text style={[styles.indicatorLabel, { color: theme.colors.text.tertiary, fontSize: 10, marginBottom: 6 }]}>
                          Stochastic (14, 3)
                        </Text>
                        <View style={{ position: 'relative' }}>
                          {/* %K Line */}
                          <LineChart
                            data={stochasticData.k}
                            width={width - 80}
                            height={100}
                            color={theme.colors.primary}
                            thickness={1.5}
                            hideDataPoints
                            hideRules={false}
                            rulesColor={theme.colors.alpha(theme.colors.border.primary, 0.2)}
                            yAxisColor={theme.colors.border.primary}
                            xAxisColor={theme.colors.border.primary}
                            yAxisTextStyle={{ color: theme.colors.text.tertiary, fontSize: 10 }}
                            noOfSections={4}
                            stepValue={25}
                            maxValue={100}
                            yAxisOffset={0}
                            initialSpacing={10}
                            spacing={(width - 100) / Math.max(stochasticData.k.length - 1, 1)}
                          />

                          {/* %D Line Overlay */}
                          <View style={{ position: 'absolute', top: 0, left: 0 }}>
                            <LineChart
                              data={stochasticData.d}
                              width={width - 80}
                              height={100}
                              color="#FF9500"
                              thickness={1.5}
                              hideDataPoints
                              hideRules
                              hideAxes
                              noOfSections={4}
                              stepValue={25}
                              maxValue={100}
                              yAxisOffset={0}
                              initialSpacing={10}
                              spacing={(width - 100) / Math.max(stochasticData.d.length - 1, 1)}
                            />
                          </View>

                          {/* 80 line - Overbought (dashed) */}
                          <View style={{
                            position: 'absolute',
                            left: 38,
                            right: 8,
                            top: '20%',
                            flexDirection: 'row',
                            alignItems: 'center',
                          }}>
                            {[...Array(40)].map((_, i) => (
                              <View
                                key={i}
                                style={{
                                  width: 4,
                                  height: 1,
                                  backgroundColor: theme.colors.alpha(theme.colors.primary, 0.5),
                                  marginRight: 4,
                                }}
                              />
                            ))}
                          </View>

                          {/* 20 line - Oversold (dashed) */}
                          <View style={{
                            position: 'absolute',
                            left: 38,
                            right: 8,
                            bottom: '20%',
                            flexDirection: 'row',
                            alignItems: 'center',
                          }}>
                            {[...Array(40)].map((_, i) => (
                              <View
                                key={i}
                                style={{
                                  width: 4,
                                  height: 1,
                                  backgroundColor: theme.colors.alpha(theme.colors.bearish, 0.5),
                                  marginRight: 4,
                                }}
                              />
                            ))}
                          </View>
                        </View>
                        <View style={{ marginTop: 4 }}>
                          <View style={{ flexDirection: 'row', justifyContent: 'space-between', marginBottom: 4 }}>
                            <Text style={{ color: theme.colors.primary, fontSize: 10 }}>%K (Fast)</Text>
                            <Text style={{ color: '#FF9500', fontSize: 10 }}>%D (Slow)</Text>
                          </View>
                          <View style={{ flexDirection: 'row', justifyContent: 'space-between' }}>
                            <Text style={{ color: theme.colors.primary, fontSize: 10 }}>Overbought (80)</Text>
                            <Text style={{ color: theme.colors.bearish, fontSize: 10 }}>Oversold (20)</Text>
                          </View>
                        </View>
                        {/* Custom Date Labels for Stochastic */}
                        <View style={{ flexDirection: 'row', justifyContent: 'space-between', marginLeft: 38, marginRight: 8, marginTop: 8 }}>
                          <Text style={{ color: theme.colors.text.tertiary, fontSize: 10 }}>
                            {chartData.length > 0 ? formatDateLabel(chartData[0].timestamp, period) : ''}
                          </Text>
                          <Text style={{ color: theme.colors.text.tertiary, fontSize: 10 }}>
                            {chartData.length > 0 ? formatDateLabel(chartData[Math.floor(chartData.length / 2)].timestamp, period) : ''}
                          </Text>
                          <Text style={{ color: theme.colors.text.tertiary, fontSize: 10 }}>
                            {chartData.length > 0 ? formatDateLabel(chartData[chartData.length - 1].timestamp, period) : ''}
                          </Text>
                        </View>
                      </View>
                    )}
                  </View>
                )}
              </View>
            );
          })()
        ) : (
          <Text style={{ color: theme.colors.text.tertiary, textAlign: 'center', padding: 40 }}>
            No chart data available
          </Text>
        )}
      </Card>

      {/* Action Buttons */}
      <View style={[styles.actionButtons, { paddingHorizontal: theme.spacing.base, marginTop: theme.spacing.base, marginBottom: theme.spacing.base }]}>
        <Button
          onPress={handleAnalyze}
          variant="primary"
          style={{ flex: 1, marginRight: theme.spacing.sm }}
        >
          📊 Analysera
        </Button>
        <Button
          onPress={handleAddPosition}
          variant="secondary"
          style={{ flex: 1, marginLeft: theme.spacing.sm }}
        >
          ➕ Lägg till Position
        </Button>
      </View>

      {/* Stock Info */}
      {stockInfo && (
        <Card style={{ margin: theme.spacing.base }}>
          <Text style={[styles.sectionTitle, { color: theme.colors.text.primary, marginBottom: theme.spacing.md }]}>
            Stock Information
          </Text>
          {stockInfo.sector && (
            <View style={styles.infoRow}>
              <Text style={[styles.infoLabel, { color: theme.colors.text.secondary }]}>Sector:</Text>
              <Text style={[styles.infoValue, { color: theme.colors.text.primary }]}>{stockInfo.sector}</Text>
            </View>
          )}
          {stockInfo.industry && (
            <View style={styles.infoRow}>
              <Text style={[styles.infoLabel, { color: theme.colors.text.secondary }]}>Industry:</Text>
              <Text style={[styles.infoValue, { color: theme.colors.text.primary }]}>{stockInfo.industry}</Text>
            </View>
          )}
        </Card>
      )}
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
    fontSize: 14,
  },
  header: {
    paddingTop: 16,
    paddingBottom: 8,
  },
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  ticker: {
    fontSize: 24,
    fontWeight: 'bold',
  },
  companyName: {
    fontSize: 14,
    marginTop: 4,
  },
  periodSelector: {
    marginTop: 16,
    marginBottom: 8,
  },
  periodButton: {
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 8,
    borderWidth: 1,
    alignItems: 'center',
    minWidth: 50,
  },
  periodButtonText: {
    fontSize: 12,
    fontWeight: '600',
  },
  indicatorSelector: {
    flexDirection: 'row',
    gap: 8,
  },
  indicatorButton: {
    flex: 1,
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 8,
    borderWidth: 1,
    alignItems: 'center',
  },
  indicatorButtonText: {
    fontSize: 11,
    fontWeight: '600',
  },
  chartTitle: {
    fontSize: 16,
    fontWeight: '600',
  },
  indicatorLabel: {
    fontSize: 10,
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  rsiLegend: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 8,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
  },
  infoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  infoLabel: {
    fontSize: 14,
  },
  infoValue: {
    fontSize: 14,
    fontWeight: '500',
  },
  actionButtons: {
    flexDirection: 'row',
    marginTop: 16,
  },
});
