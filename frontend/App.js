import React, { useEffect, useRef } from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';
import * as Notifications from 'expo-notifications';

// Screens
import WatchlistScreen from './src/screens/WatchlistScreen';
import SignalsScreen from './src/screens/SignalsScreen';
import PositionsScreen from './src/screens/PositionsScreen';
import SettingsScreen from './src/screens/SettingsScreen';

// Services
import NotificationService from './src/services/NotificationService';
import { api } from './src/api/client';

const Tab = createBottomTabNavigator();

export default function App() {
  const navigationRef = useRef();
  const notificationListener = useRef();
  const responseListener = useRef();

  useEffect(() => {
    // Register for push notifications and send token to backend
    const setupNotifications = async () => {
      const token = await NotificationService.registerForPushNotifications();

      if (token) {
        try {
          // Register token with backend
          await api.registerPushToken(token);
          console.log('Push token registered with backend');
        } catch (error) {
          console.error('Failed to register push token with backend:', error);
        }
      }
    };

    setupNotifications();

    // Listen for notifications
    notificationListener.current = NotificationService.addNotificationListener((notification) => {
      console.log('Notification received:', notification);
    });

    // Handle notification response (when user taps notification)
    responseListener.current = NotificationService.addNotificationResponseListener((response) => {
      const data = response.notification.request.content.data;

      // Navigate to appropriate screen based on notification type
      if (data.type === 'signal') {
        navigationRef.current?.navigate('Signals');
      } else if (data.type === 'position' || data.type === 'exit') {
        navigationRef.current?.navigate('Positions');
      }
    });

    return () => {
      NotificationService.removeListeners();
    };
  }, []);

  return (
    <SafeAreaProvider>
      <NavigationContainer ref={navigationRef}>
        <StatusBar style="auto" />
        <Tab.Navigator
          screenOptions={{
            tabBarActiveTintColor: '#2196F3',
            tabBarInactiveTintColor: 'gray',
            headerStyle: {
              backgroundColor: '#2196F3',
            },
            headerTintColor: '#fff',
            headerTitleStyle: {
              fontWeight: 'bold',
            },
          }}
        >
          <Tab.Screen
            name="Watchlist"
            component={WatchlistScreen}
            options={{
              title: 'Min Watchlist',
              tabBarLabel: 'Watchlist',
            }}
          />
          <Tab.Screen
            name="Signals"
            component={SignalsScreen}
            options={{
              title: 'Kopsignaler',
              tabBarLabel: 'Signaler',
            }}
          />
          <Tab.Screen
            name="Positions"
            component={PositionsScreen}
            options={{
              title: 'Mina Positioner',
              tabBarLabel: 'Positioner',
            }}
          />
          <Tab.Screen
            name="Settings"
            component={SettingsScreen}
            options={{
              title: 'Installningar',
              tabBarLabel: 'Mer',
            }}
          />
        </Tab.Navigator>
      </NavigationContainer>
    </SafeAreaProvider>
  );
}
