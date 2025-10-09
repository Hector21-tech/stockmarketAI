import React, { useEffect, useRef } from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createStackNavigator } from '@react-navigation/stack';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';
import * as Notifications from 'expo-notifications';
import { Ionicons } from '@expo/vector-icons';

// Theme
import { ThemeProvider, useTheme } from './src/theme/ThemeContext';

// Screens
import DashboardScreen from './src/screens/DashboardScreen';
import MacroScreen from './src/screens/MacroScreen';
import WatchlistScreen from './src/screens/WatchlistScreen';
import StockDetailScreen from './src/screens/StockDetailScreen';
import SignalsScreen from './src/screens/SignalsScreen';
import PositionsScreen from './src/screens/PositionsScreen';
import PortfolioAnalyticsScreen from './src/screens/PortfolioAnalyticsScreen';
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

// Positions Stack Navigator (includes Portfolio Analytics)
function PositionsStack() {
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
        name="PositionsMain"
        component={PositionsScreen}
        options={{ headerShown: false }}
      />
      <Stack.Screen
        name="Analytics"
        component={PortfolioAnalyticsScreen}
        options={{
          title: 'Portfolio Analytics',
        }}
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
          screenOptions={({ route }) => ({
            tabBarIcon: ({ focused, color, size }) => {
              let iconName;

              if (route.name === 'Dashboard') {
                iconName = focused ? 'trending-up' : 'trending-up-outline';
              } else if (route.name === 'Macro') {
                iconName = focused ? 'globe' : 'globe-outline';
              } else if (route.name === 'Watchlist') {
                iconName = focused ? 'star' : 'star-outline';
              } else if (route.name === 'Signals') {
                iconName = focused ? 'notifications' : 'notifications-outline';
              } else if (route.name === 'Positions') {
                iconName = focused ? 'briefcase' : 'briefcase-outline';
              } else if (route.name === 'Settings') {
                iconName = focused ? 'settings' : 'settings-outline';
              }

              return <Ionicons name={iconName} size={size} color={color} />;
            },
            tabBarActiveTintColor: theme.colors.primary,
            tabBarInactiveTintColor: theme.colors.text.tertiary,
            tabBarStyle: {
              backgroundColor: theme.colors.background.secondary,
              borderTopColor: theme.colors.border.primary,
              borderTopWidth: 1,
              height: 65,
              paddingBottom: 8,
              paddingTop: 8,
              elevation: 8,
              shadowColor: '#000',
              shadowOffset: { width: 0, height: -2 },
              shadowOpacity: 0.1,
              shadowRadius: 8,
            },
            tabBarLabelStyle: {
              fontSize: 10,
              fontWeight: '600',
              marginTop: 0,
            },
            tabBarIconStyle: {
              marginTop: 2,
            },
            headerStyle: {
              backgroundColor: theme.colors.background.secondary,
              borderBottomColor: theme.colors.border.primary,
              elevation: 4,
              shadowColor: '#000',
              shadowOffset: { width: 0, height: 2 },
              shadowOpacity: 0.1,
              shadowRadius: 4,
            },
            headerTintColor: theme.colors.text.primary,
            headerTitleStyle: {
              fontWeight: theme.typography.fontWeight.bold,
              fontSize: theme.typography.fontSize.lg,
            },
          })}
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
            name="Macro"
            component={MacroScreen}
            options={{
              title: 'Macro Dashboard',
              tabBarLabel: 'Macro',
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
            component={PositionsStack}
            options={{
              title: 'Mina Positioner',
              tabBarLabel: 'Portfolio',
              headerShown: false,
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
