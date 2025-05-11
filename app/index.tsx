import { useEffect, useState } from 'react';
import { View, StyleSheet, Text } from 'react-native';
import { Redirect } from 'expo-router';
import { SplashScreen } from 'expo-router';
import { useFonts } from 'expo-font';
import { Inter_400Regular, Inter_500Medium, Inter_700Bold } from '@expo-google-fonts/inter';
import { initTensorFlow } from '@/models';

// Prevent the splash screen from auto-hiding before asset loading is complete
SplashScreen.preventAutoHideAsync();

export default function Index() {
  const [fontsLoaded, fontError] = useFonts({
    'Inter-Regular': Inter_400Regular,
    'Inter-Medium': Inter_500Medium,
    'Inter-Bold': Inter_700Bold,
  });
  
  const [modelInitialized, setModelInitialized] = useState(false);
  const [initError, setInitError] = useState<Error | null>(null);

  useEffect(() => {
    async function initializeModel() {
      try {
        await initTensorFlow();
        setModelInitialized(true);
      } catch (error) {
        console.error('Error initializing TensorFlow:', error);
        setInitError(error as Error);
      }
    }

    initializeModel();
  }, []);

  useEffect(() => {
    if ((fontsLoaded || fontError) && (modelInitialized || initError)) {
      // Hide the splash screen after fonts and model have loaded (or error encountered)
      SplashScreen.hideAsync();
    }
  }, [fontsLoaded, fontError, modelInitialized, initError]);

  // Return null until the fonts and model are loaded
  if ((!fontsLoaded && !fontError) || (!modelInitialized && !initError)) {
    return null;
  }

  // Show error screen if model initialization failed
  if (initError) {
    return (
      <View style={styles.errorContainer}>
        <Text style={styles.errorText}>
          Failed to initialize models. Please try restarting the app.
        </Text>
        <Text style={styles.errorDetail}>
          {initError.message}
        </Text>
      </View>
    );
  }

  // Redirect to the main tabs layout
  return <Redirect href="/(tabs)" />;
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
    backgroundColor: '#f8f8f8',
  },
  errorText: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#d32f2f',
    marginBottom: 10,
    textAlign: 'center',
  },
  errorDetail: {
    fontSize: 14,
    color: '#666666',
    textAlign: 'center',
  },
});