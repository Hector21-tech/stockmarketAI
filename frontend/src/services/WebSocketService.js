import { io } from 'socket.io-client';

const WEBSOCKET_URL = 'http://192.168.1.46:5000';

class WebSocketService {
  constructor() {
    this.socket = null;
    this.connected = false;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 2000;
    this.listeners = {
      onPriceUpdate: null,
      onConnectionChange: null,
    };
  }

  // Connect to WebSocket server
  connect() {
    if (this.socket && this.connected) {
      console.log('WebSocket already connected');
      return;
    }

    console.log('Connecting to WebSocket server...');

    this.socket = io(WEBSOCKET_URL, {
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionDelay: this.reconnectDelay,
      reconnectionAttempts: this.maxReconnectAttempts,
      timeout: 10000,
    });

    this.setupEventHandlers();
  }

  // Setup event handlers
  setupEventHandlers() {
    this.socket.on('connect', () => {
      console.log('✅ WebSocket connected');
      this.connected = true;
      this.reconnectAttempts = 0;
      this.notifyConnectionChange(true);
    });

    this.socket.on('disconnect', (reason) => {
      console.log('❌ WebSocket disconnected:', reason);
      this.connected = false;
      this.notifyConnectionChange(false);
    });

    this.socket.on('connect_error', (error) => {
      console.log('WebSocket connection error:', error.message);
      this.reconnectAttempts++;

      if (this.reconnectAttempts >= this.maxReconnectAttempts) {
        console.log('Max reconnection attempts reached');
      }
    });

    this.socket.on('connection_status', (data) => {
      console.log('Connection status:', data);
    });

    this.socket.on('subscribed', (data) => {
      console.log('Subscribed to watchlist:', data);
    });

    this.socket.on('price_update', (data) => {
      console.log('Price update received:', data);
      this.notifyPriceUpdate(data);
    });

    this.socket.on('reconnect_attempt', (attemptNumber) => {
      console.log(`Reconnection attempt ${attemptNumber}...`);
    });

    this.socket.on('reconnect', (attemptNumber) => {
      console.log(`Reconnected after ${attemptNumber} attempts`);
      this.reconnectAttempts = 0;
    });
  }

  // Subscribe to watchlist price updates
  subscribeToWatchlist(tickers, market = 'SE') {
    if (!this.socket || !this.connected) {
      console.warn('Cannot subscribe: WebSocket not connected');
      return;
    }

    console.log(`Subscribing to watchlist: ${tickers.join(', ')} (${market})`);
    this.socket.emit('subscribe_watchlist', { tickers, market });
  }

  // Unsubscribe from watchlist updates
  unsubscribeFromWatchlist() {
    if (!this.socket || !this.connected) {
      return;
    }

    console.log('Unsubscribing from watchlist');
    this.socket.emit('unsubscribe_watchlist');
  }

  // Set price update listener
  onPriceUpdate(callback) {
    this.listeners.onPriceUpdate = callback;
  }

  // Set connection change listener
  onConnectionChange(callback) {
    this.listeners.onConnectionChange = callback;
  }

  // Notify price update
  notifyPriceUpdate(data) {
    if (this.listeners.onPriceUpdate) {
      this.listeners.onPriceUpdate(data);
    }
  }

  // Notify connection change
  notifyConnectionChange(connected) {
    if (this.listeners.onConnectionChange) {
      this.listeners.onConnectionChange(connected);
    }
  }

  // Check if connected
  isConnected() {
    return this.connected;
  }

  // Disconnect from WebSocket
  disconnect() {
    if (this.socket) {
      console.log('Disconnecting from WebSocket...');
      this.socket.disconnect();
      this.socket = null;
      this.connected = false;
    }
  }

  // Reconnect manually
  reconnect() {
    this.disconnect();
    this.reconnectAttempts = 0;
    this.connect();
  }
}

export default new WebSocketService();
