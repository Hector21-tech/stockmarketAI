import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Alert,
  Switch,
} from 'react-native';
import { api } from '../api/client';
import NotificationService from '../services/NotificationService';

export default function SettingsScreen() {
  const [apiStatus, setApiStatus] = useState('Checking...');
  const [notifications, setNotifications] = useState({
    enabled: true,
    signals: true,
    positions: true,
    exits: true,
  });
  const [pushToken, setPushToken] = useState(null);

  useEffect(() => {
    loadNotificationSettings();
    loadPushToken();
  }, []);

  const loadNotificationSettings = async () => {
    const settings = await NotificationService.getNotificationSettings();
    setNotifications(settings);
  };

  const loadPushToken = async () => {
    const token = await NotificationService.getStoredPushToken();
    setPushToken(token);
  };

  const updateNotificationSetting = async (key, value) => {
    const newSettings = { ...notifications, [key]: value };
    setNotifications(newSettings);
    await NotificationService.saveNotificationSettings(newSettings);
  };

  const testNotification = async () => {
    await NotificationService.sendLocalNotification(
      '🔔 Test Notification',
      'Notifikationer fungerar!',
      { type: 'test' }
    );
  };

  const checkAPIHealth = async () => {
    try {
      const response = await api.health();
      if (response.data.status === 'healthy') {
        setApiStatus('Connected');
        Alert.alert('Success', 'Backend API ar online!');
      }
    } catch (error) {
      setApiStatus('Disconnected');
      Alert.alert(
        'Error',
        'Kunde inte ansluta till backend. Kontrollera att servern kor.'
      );
    }
  };

  const viewStrategy = async () => {
    try {
      const response = await api.getStrategy();
      Alert.alert('Marketmate Strategy', response.data.strategy);
    } catch (error) {
      Alert.alert('Error', 'Kunde inte hamta strategi');
    }
  };

  return (
    <ScrollView style={styles.container}>
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>MarketsAI</Text>
        <Text style={styles.version}>Version 1.0.0</Text>
        <Text style={styles.description}>
          Automatisk aktieanalys baserad pa Marketmate-strategin med AI-drivna
          kopsignaler och 1/3-exit regelmotor.
        </Text>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Backend Status</Text>
        <View style={styles.row}>
          <Text style={styles.label}>API Status:</Text>
          <Text
            style={[
              styles.status,
              {
                color:
                  apiStatus === 'Connected'
                    ? '#4CAF50'
                    : apiStatus === 'Disconnected'
                    ? '#F44336'
                    : '#FF9800',
              },
            ]}
          >
            {apiStatus}
          </Text>
        </View>
        <TouchableOpacity style={styles.button} onPress={checkAPIHealth}>
          <Text style={styles.buttonText}>Test Connection</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Notifikationer</Text>

        <View style={styles.row}>
          <Text style={styles.label}>Aktivera notifikationer</Text>
          <Switch
            value={notifications.enabled}
            onValueChange={(value) => updateNotificationSetting('enabled', value)}
            trackColor={{ false: '#767577', true: '#4CAF50' }}
            thumbColor={notifications.enabled ? '#fff' : '#f4f3f4'}
          />
        </View>

        {notifications.enabled && (
          <>
            <View style={styles.row}>
              <Text style={styles.label}>Trading-signaler</Text>
              <Switch
                value={notifications.signals}
                onValueChange={(value) => updateNotificationSetting('signals', value)}
                trackColor={{ false: '#767577', true: '#4CAF50' }}
                thumbColor={notifications.signals ? '#fff' : '#f4f3f4'}
              />
            </View>

            <View style={styles.row}>
              <Text style={styles.label}>Positionsuppdateringar</Text>
              <Switch
                value={notifications.positions}
                onValueChange={(value) => updateNotificationSetting('positions', value)}
                trackColor={{ false: '#767577', true: '#4CAF50' }}
                thumbColor={notifications.positions ? '#fff' : '#f4f3f4'}
              />
            </View>

            <View style={styles.row}>
              <Text style={styles.label}>Exit-signaler</Text>
              <Switch
                value={notifications.exits}
                onValueChange={(value) => updateNotificationSetting('exits', value)}
                trackColor={{ false: '#767577', true: '#4CAF50' }}
                thumbColor={notifications.exits ? '#fff' : '#f4f3f4'}
              />
            </View>
          </>
        )}

        <TouchableOpacity style={styles.button} onPress={testNotification}>
          <Text style={styles.buttonText}>Testa Notifikation</Text>
        </TouchableOpacity>

        {pushToken && (
          <Text style={styles.tokenText} numberOfLines={1}>
            Push Token: {pushToken.substring(0, 20)}...
          </Text>
        )}
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Strategi</Text>
        <TouchableOpacity style={styles.button} onPress={viewStrategy}>
          <Text style={styles.buttonText}>Visa Marketmate-strategi</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Prenumeration</Text>
        <Text style={styles.priceText}>50 kr / manad</Text>
        <Text style={styles.featureText}>• Upp till 30 aktier i watchlist</Text>
        <Text style={styles.featureText}>• AI-drivna kopsignaler</Text>
        <Text style={styles.featureText}>• Automatiska exit-notiser</Text>
        <Text style={styles.featureText}>• Realtids-prisuppdateringar</Text>
        <Text style={styles.featureText}>• Positionshantering</Text>

        <TouchableOpacity
          style={[styles.button, styles.subscribeButton]}
          onPress={() =>
            Alert.alert('Coming Soon', 'Google Play Billing kommer snart!')
          }
        >
          <Text style={styles.buttonText}>Prenumerera</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Om</Text>
        <Text style={styles.infoText}>
          MarketsAI anvander Yahoo Finance for aktiedata och analyserar
          enligt Marketmate-filosofin: Folja marknaden, inte forutse den.
        </Text>
        <Text style={styles.infoText}>
          All handel ar mekanisk och repeterbar med definierad risk.
        </Text>
      </View>

      <View style={styles.footer}>
        <Text style={styles.footerText}>
          Powered by Claude Code & Marketmate Strategy
        </Text>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  section: {
    backgroundColor: '#fff',
    margin: 16,
    marginBottom: 8,
    padding: 16,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 12,
  },
  version: {
    fontSize: 14,
    color: '#666',
    marginBottom: 8,
  },
  description: {
    fontSize: 14,
    color: '#666',
    lineHeight: 20,
  },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  label: {
    fontSize: 14,
    color: '#666',
  },
  status: {
    fontSize: 14,
    fontWeight: 'bold',
  },
  button: {
    backgroundColor: '#2196F3',
    padding: 14,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 8,
  },
  buttonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  subscribeButton: {
    backgroundColor: '#4CAF50',
    marginTop: 16,
  },
  priceText: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#4CAF50',
    marginBottom: 12,
  },
  featureText: {
    fontSize: 14,
    color: '#666',
    marginVertical: 4,
  },
  infoText: {
    fontSize: 14,
    color: '#666',
    lineHeight: 20,
    marginBottom: 8,
  },
  footer: {
    padding: 20,
    alignItems: 'center',
  },
  footerText: {
    fontSize: 12,
    color: '#999',
  },
  tokenText: {
    fontSize: 12,
    color: '#999',
    marginTop: 8,
  },
});
