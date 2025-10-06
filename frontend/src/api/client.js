import axios from 'axios';

// Backend API URL - andras till din dators IP nar du testar pa mobil
const API_BASE_URL = 'http://192.168.1.46:5000/api';
// For emulator: http://10.0.2.2:5000/api
// For fysisk enhet: http://DIN_DATORS_IP:5000/api

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// API methods
export const api = {
  // Health check
  health: () => apiClient.get('/health'),

  // Stock data
  getStockPrice: (ticker, market = 'SE') =>
    apiClient.get('/stock/price', { params: { ticker, market } }),

  getMultiplePrices: (tickers, market = 'SE') =>
    apiClient.post('/stock/prices', { tickers, market }),

  getStockInfo: (ticker, market = 'SE') =>
    apiClient.get('/stock/info', { params: { ticker, market } }),

  getHistoricalData: (ticker, period = '3mo', interval = '1d', market = 'SE') =>
    apiClient.get('/stock/historical', { params: { ticker, period, interval, market } }),

  // AI Analysis
  analyzeStock: (ticker, market = 'SE') =>
    apiClient.post('/analyze', { ticker, market }),

  scanWatchlist: (tickers, market = 'SE') =>
    apiClient.post('/scan', { tickers, market }),

  getBuySignals: (tickers, market = 'SE') =>
    apiClient.post('/signals/buy', { tickers, market }),

  // Positions
  getPositions: () => apiClient.get('/positions'),

  addPosition: (positionData) => apiClient.post('/positions', positionData),

  getPositionSummary: (ticker) => apiClient.get(`/positions/${ticker}`),

  checkPositions: () => apiClient.get('/positions/check'),

  executeExit: (exitData) => apiClient.post('/positions/exit', exitData),

  updateStopLoss: (ticker, newStop) =>
    apiClient.put('/positions/stop-loss', { ticker, new_stop: newStop }),

  // Utility
  getMarketStatus: (market = 'SE') =>
    apiClient.get('/market-status', { params: { market } }),

  getStrategy: () => apiClient.get('/strategy'),

  // Notifications
  registerPushToken: (pushToken, userId = 'default') =>
    apiClient.post('/notifications/register', { push_token: pushToken, user_id: userId }),

  unregisterPushToken: (userId = 'default') =>
    apiClient.post('/notifications/unregister', { user_id: userId }),

  sendNotification: (pushToken, title, body, data = {}) =>
    apiClient.post('/notifications/send', { push_token: pushToken, title, body, data }),

  sendSignalNotification: (ticker, action, strength, reason, userId = 'default') =>
    apiClient.post('/notifications/signal', { ticker, action, strength, reason, user_id: userId }),
};

export default apiClient;
