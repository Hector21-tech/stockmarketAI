/**
 * Settings Screen
 * App configuration and theme toggle
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Alert,
  Switch,
} from 'react-native';
import { useTheme } from '../theme/ThemeContext';
import { Card, Button } from '../components';
import { api } from '../api/client';
import NotificationService from '../services/NotificationService';

export default function SettingsScreen() {
  const { theme, isDark, toggleTheme } = useTheme();
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
        Alert.alert('Success', 'Backend API är online!');
      }
    } catch (error) {
      setApiStatus('Disconnected');
      Alert.alert(
        'Error',
        'Kunde inte ansluta till backend. Kontrollera att servern körs.'
      );
    }
  };

  const viewStrategy = async () => {
    try {
      const response = await api.getStrategy();
      Alert.alert('Marketmate Strategy', response.data.strategy);
    } catch (error) {
      Alert.alert('Error', 'Kunde inte hämta strategi');
    }
  };

  return (
    <ScrollView style={[styles.container, { backgroundColor: theme.colors.background.primary }]}>
      {/* App Info */}
      <Card variant="elevated" style={{ margin: theme.spacing.base, marginBottom: theme.spacing.sm }}>
        <Text style={[styles.sectionTitle, { color: theme.colors.text.primary, ...theme.typography.styles.h5 }]}>
          MarketsAI
        </Text>
        <Text style={[styles.version, { color: theme.colors.text.secondary }]}>
          Version 1.0.0
        </Text>
        <Text style={[styles.description, { color: theme.colors.text.secondary }]}>
          Automatisk aktieanalys baserad på Marketmate-strategin med AI-drivna
          köpsignaler och 1/3-exit regelmotor.
        </Text>
      </Card>

      {/* Theme Settings */}
      <Card variant="elevated" style={{ margin: theme.spacing.base, marginBottom: theme.spacing.sm }}>
        <Text style={[styles.sectionTitle, { color: theme.colors.text.primary, ...theme.typography.styles.h6 }]}>
          Utseende
        </Text>

        <View style={styles.row}>
          <View style={{ flex: 1 }}>
            <Text style={[styles.label, { color: theme.colors.text.primary }]}>
              Dark Mode
            </Text>
            <Text style={[styles.sublabel, { color: theme.colors.text.tertiary }]}>
              Professionell mörk design
            </Text>
          </View>
          <Switch
            value={isDark}
            onValueChange={toggleTheme}
            trackColor={{ false: theme.colors.text.tertiary, true: theme.colors.primary }}
            thumbColor={isDark ? '#fff' : '#f4f3f4'}
          />
        </View>
      </Card>

      {/* Backend Status */}
      <Card variant="elevated" style={{ margin: theme.spacing.base, marginBottom: theme.spacing.sm }}>
        <Text style={[styles.sectionTitle, { color: theme.colors.text.primary, ...theme.typography.styles.h6 }]}>
          Backend Status
        </Text>
        <View style={styles.row}>
          <Text style={[styles.label, { color: theme.colors.text.secondary }]}>
            API Status:
          </Text>
          <Text
            style={[
              styles.status,
              {
                color:
                  apiStatus === 'Connected'
                    ? theme.colors.bullish
                    : apiStatus === 'Disconnected'
                    ? theme.colors.bearish
                    : theme.colors.warning || '#FF9800',
              },
            ]}
          >
            {apiStatus}
          </Text>
        </View>
        <Button onPress={checkAPIHealth} style={{ marginTop: theme.spacing.sm }}>
          Test Connection
        </Button>
      </Card>

      {/* Notifications */}
      <Card variant="elevated" style={{ margin: theme.spacing.base, marginBottom: theme.spacing.sm }}>
        <Text style={[styles.sectionTitle, { color: theme.colors.text.primary, ...theme.typography.styles.h6 }]}>
          Notifikationer
        </Text>

        <View style={styles.row}>
          <Text style={[styles.label, { color: theme.colors.text.primary }]}>
            Aktivera notifikationer
          </Text>
          <Switch
            value={notifications.enabled}
            onValueChange={(value) => updateNotificationSetting('enabled', value)}
            trackColor={{ false: theme.colors.text.tertiary, true: theme.colors.primary }}
            thumbColor={notifications.enabled ? '#fff' : '#f4f3f4'}
          />
        </View>

        {notifications.enabled && (
          <>
            <View style={[styles.row, { marginTop: theme.spacing.sm }]}>
              <Text style={[styles.label, { color: theme.colors.text.secondary }]}>
                Trading-signaler
              </Text>
              <Switch
                value={notifications.signals}
                onValueChange={(value) => updateNotificationSetting('signals', value)}
                trackColor={{ false: theme.colors.text.tertiary, true: theme.colors.bullish }}
                thumbColor={notifications.signals ? '#fff' : '#f4f3f4'}
              />
            </View>

            <View style={styles.row}>
              <Text style={[styles.label, { color: theme.colors.text.secondary }]}>
                Positionsuppdateringar
              </Text>
              <Switch
                value={notifications.positions}
                onValueChange={(value) => updateNotificationSetting('positions', value)}
                trackColor={{ false: theme.colors.text.tertiary, true: theme.colors.primary }}
                thumbColor={notifications.positions ? '#fff' : '#f4f3f4'}
              />
            </View>

            <View style={styles.row}>
              <Text style={[styles.label, { color: theme.colors.text.secondary }]}>
                Exit-signaler
              </Text>
              <Switch
                value={notifications.exits}
                onValueChange={(value) => updateNotificationSetting('exits', value)}
                trackColor={{ false: theme.colors.text.tertiary, true: theme.colors.warning || '#FF9800' }}
                thumbColor={notifications.exits ? '#fff' : '#f4f3f4'}
              />
            </View>
          </>
        )}

        <Button onPress={testNotification} variant="outline" style={{ marginTop: theme.spacing.md }}>
          Testa Notifikation
        </Button>

        {pushToken && (
          <Text style={[styles.tokenText, { color: theme.colors.text.tertiary }]} numberOfLines={1}>
            Push Token: {pushToken.substring(0, 20)}...
          </Text>
        )}
      </Card>

      {/* Strategy */}
      <Card variant="elevated" style={{ margin: theme.spacing.base, marginBottom: theme.spacing.sm }}>
        <Text style={[styles.sectionTitle, { color: theme.colors.text.primary, ...theme.typography.styles.h6 }]}>
          Strategi
        </Text>
        <Button onPress={viewStrategy} variant="outline">
          Visa Marketmate-strategi
        </Button>
      </Card>

      {/* Subscription */}
      <Card variant="elevated" style={{ margin: theme.spacing.base, marginBottom: theme.spacing.sm }}>
        <Text style={[styles.sectionTitle, { color: theme.colors.text.primary, ...theme.typography.styles.h6 }]}>
          Prenumeration
        </Text>
        <Text style={[styles.priceText, { color: theme.colors.bullish }]}>
          50 kr / månad
        </Text>
        <Text style={[styles.featureText, { color: theme.colors.text.secondary }]}>
          • Upp till 30 aktier i watchlist
        </Text>
        <Text style={[styles.featureText, { color: theme.colors.text.secondary }]}>
          • AI-drivna köpsignaler
        </Text>
        <Text style={[styles.featureText, { color: theme.colors.text.secondary }]}>
          • Automatiska exit-notiser
        </Text>
        <Text style={[styles.featureText, { color: theme.colors.text.secondary }]}>
          • Realtids-prisuppdateringar
        </Text>
        <Text style={[styles.featureText, { color: theme.colors.text.secondary }]}>
          • Positionshantering
        </Text>

        <Button
          onPress={() =>
            Alert.alert('Coming Soon', 'Google Play Billing kommer snart!')
          }
          style={{ marginTop: theme.spacing.md, backgroundColor: theme.colors.bullish }}
        >
          Prenumerera
        </Button>
      </Card>

      {/* About */}
      <Card variant="elevated" style={{ margin: theme.spacing.base, marginBottom: theme.spacing.sm }}>
        <Text style={[styles.sectionTitle, { color: theme.colors.text.primary, ...theme.typography.styles.h6 }]}>
          Om
        </Text>
        <Text style={[styles.infoText, { color: theme.colors.text.secondary }]}>
          MarketsAI använder Yahoo Finance för aktiedata och analyserar
          enligt Marketmate-filosofin: Följa marknaden, inte förutse den.
        </Text>
        <Text style={[styles.infoText, { color: theme.colors.text.secondary }]}>
          All handel är mekanisk och repeterbar med definierad risk.
        </Text>
      </Card>

      {/* Footer */}
      <View style={styles.footer}>
        <Text style={[styles.footerText, { color: theme.colors.text.tertiary }]}>
          Powered by Claude Code & Marketmate Strategy
        </Text>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  sectionTitle: {
    marginBottom: 12,
  },
  version: {
    fontSize: 14,
    marginBottom: 8,
  },
  description: {
    fontSize: 14,
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
  },
  sublabel: {
    fontSize: 12,
    marginTop: 2,
  },
  status: {
    fontSize: 14,
    fontWeight: '700',
  },
  priceText: {
    fontSize: 24,
    fontWeight: '700',
    marginBottom: 12,
  },
  featureText: {
    fontSize: 14,
    marginVertical: 4,
  },
  infoText: {
    fontSize: 14,
    lineHeight: 20,
    marginBottom: 8,
  },
  footer: {
    padding: 20,
    alignItems: 'center',
    marginBottom: 20,
  },
  footerText: {
    fontSize: 12,
  },
  tokenText: {
    fontSize: 12,
    marginTop: 8,
  },
});
