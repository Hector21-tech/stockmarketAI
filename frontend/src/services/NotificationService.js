import * as Notifications from 'expo-notifications';
import { Platform } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';

// Configure notification handler
Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: true,
  }),
});

class NotificationService {
  constructor() {
    this.expoPushToken = null;
    this.notificationListener = null;
    this.responseListener = null;
  }

  // Request permissions and get push token
  async registerForPushNotifications() {
    // Skip push notifications on web (requires VAPID key setup)
    if (Platform.OS === 'web') {
      console.log('Push notifications not supported on web in development mode');
      return null;
    }

    let token;

    if (Platform.OS === 'android') {
      await Notifications.setNotificationChannelAsync('default', {
        name: 'default',
        importance: Notifications.AndroidImportance.MAX,
        vibrationPattern: [0, 250, 250, 250],
        lightColor: '#4CAF50',
      });
    }

    const { status: existingStatus } = await Notifications.getPermissionsAsync();
    let finalStatus = existingStatus;

    if (existingStatus !== 'granted') {
      const { status } = await Notifications.requestPermissionsAsync();
      finalStatus = status;
    }

    if (finalStatus !== 'granted') {
      console.log('Failed to get push token for push notification!');
      return null;
    }

    token = (await Notifications.getExpoPushTokenAsync()).data;
    this.expoPushToken = token;

    // Save token to AsyncStorage
    await AsyncStorage.setItem('expoPushToken', token);

    return token;
  }

  // Get stored push token
  async getStoredPushToken() {
    return await AsyncStorage.getItem('expoPushToken');
  }

  // Send local notification
  async sendLocalNotification(title, body, data = {}) {
    await Notifications.scheduleNotificationAsync({
      content: {
        title,
        body,
        data,
        sound: true,
        priority: Notifications.AndroidNotificationPriority.HIGH,
      },
      trigger: null, // Send immediately
    });
  }

  // Send notification about new trading signal
  async notifyNewSignal(signal) {
    const title = `📈 Ny Trading Signal: ${signal.ticker}`;
    const body = `${signal.action} - Styrka: ${signal.strength}/10\n${signal.reason}`;

    await this.sendLocalNotification(title, body, {
      type: 'signal',
      ticker: signal.ticker,
      action: signal.action,
    });
  }

  // Send notification about position update
  async notifyPositionUpdate(position) {
    const title = `💰 Position Update: ${position.ticker}`;
    const profitLoss = position.current_value - position.entry_value;
    const profitLossPercent = ((profitLoss / position.entry_value) * 100).toFixed(2);
    const emoji = profitLoss >= 0 ? '📈' : '📉';

    const body = `${emoji} ${profitLossPercent}% (${profitLoss.toFixed(2)} kr)`;

    await this.sendLocalNotification(title, body, {
      type: 'position',
      ticker: position.ticker,
      profitLoss,
    });
  }

  // Send notification about exit signal
  async notifyExitSignal(position, reason) {
    const title = `🚪 Exit Signal: ${position.ticker}`;
    const body = reason;

    await this.sendLocalNotification(title, body, {
      type: 'exit',
      ticker: position.ticker,
    });
  }

  // Listen for notifications
  addNotificationListener(callback) {
    this.notificationListener = Notifications.addNotificationReceivedListener(callback);
    return this.notificationListener;
  }

  // Listen for notification responses (when user taps notification)
  addNotificationResponseListener(callback) {
    this.responseListener = Notifications.addNotificationResponseReceivedListener(callback);
    return this.responseListener;
  }

  // Remove listeners
  removeListeners() {
    if (this.notificationListener) {
      this.notificationListener.remove();
    }
    if (this.responseListener) {
      this.responseListener.remove();
    }
  }

  // Cancel all notifications
  async cancelAllNotifications() {
    await Notifications.cancelAllScheduledNotificationsAsync();
  }

  // Get notification settings from AsyncStorage
  async getNotificationSettings() {
    const settings = await AsyncStorage.getItem('notificationSettings');
    return settings ? JSON.parse(settings) : {
      enabled: true,
      signals: true,
      positions: true,
      exits: true,
    };
  }

  // Save notification settings
  async saveNotificationSettings(settings) {
    await AsyncStorage.setItem('notificationSettings', JSON.stringify(settings));
  }
}

export default new NotificationService();
