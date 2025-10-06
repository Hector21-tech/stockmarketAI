import React, { useEffect, useRef } from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createStackNavigator } from '@react-navigation/stack';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';
import * as Notifications from 'expo-notifications';

// Theme
import { ThemeProvider, useTheme } from './src/theme/ThemeContext';

// Screens
import DashboardScreen from './src/screens/DashboardScreen';
import WatchlistScreen from './src/screens/WatchlistScreen';
import StockDetailScreen from './src/screens/StockDetailScreen';
import SignalsScreen from './src/screens/SignalsScreen';
import PositionsScreen from './src/screens/PositionsScreen';
import SettingsScreen from './src/screens/SettingsScreen';

// Services
import NotificationService from './src/services/NotificationService';
import { api } from './src/api/client';

const Tab = createBottomTabNavigator();
const Stack = createStackNavigator();

// Watchlist Stack Navigator
function WatchlistStack() {
  const { theme } = useTheme();

  return (
    <Stack.Navigator
      screenOptions={{
        headerStyle: {
          backgroundColor: theme.colors.background.secondary,
        },
        headerTintColor: theme.colors.text.primary,
        headerTitleStyle: {
          fontWeight: theme.typography.fontWeight.bold,
        },
      }}
    >
      <Stack.Screen
        name="WatchlistMain"
        component={WatchlistScreen}
        options={{ headerShown: false }}
      />
      <Stack.Screen
        name="StockDetail"
        component={StockDetailScreen}
        options={({ route }) => ({
          title: route.params?.ticker || 'Stock Detail',
        })}
      />
    </Stack.Navigator>
  );
}

function AppContent() {
  const { theme, isDark } = useTheme();
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
        <StatusBar style={isDark ? 'light' : 'dark'} />
        <Tab.Navigator
          screenOptions={{
            tabBarActiveTintColor: theme.colors.primary,
            tabBarInactiveTintColor: theme.colors.text.tertiary,
            tabBarStyle: {
              backgroundColor: theme.colors.background.secondary,
              borderTopColor: theme.colors.border.primary,
            },
            headerStyle: {
              backgroundColor: theme.colors.background.secondary,
              borderBottomColor: theme.colors.border.primary,
            },
            headerTintColor: theme.colors.text.primary,
            headerTitleStyle: {
              fontWeight: theme.typography.fontWeight.bold,
              fontSize: theme.typography.fontSize.lg,
            },
          }}
        >
          <Tab.Screen
            name="Dashboard"
            component={DashboardScreen}
            options={{
              title: 'Dashboard',
              tabBarLabel: 'Dashboard',
            }}
          />
          <Tab.Screen
            name="Watchlist"
            component={WatchlistStack}
            options={{
              title: 'Min Watchlist',
              tabBarLabel: 'Watchlist',
              headerShown: false,
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

export default function App() {
  return (
    <ThemeProvider>
      <AppContent />
    </ThemeProvider>
  );
}
