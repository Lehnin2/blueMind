// components/Map.tsx
import React from 'react';
import { Platform, View, Text, StyleSheet } from 'react-native';

// The Map component will conditionally import WebMapView only on web platforms
const Map = (props: any) => {
  // Only import and render the map on web platforms
  if (Platform.OS === 'web') {
    // Dynamic import to avoid loading Leaflet on mobile
    const WebMapView = require('./MapView').default;
    return <WebMapView {...props} />;
  }
  
  // For mobile platforms, render a placeholder
  return (
    <View style={styles.container}>
      <Text style={styles.text}>
        Map view is currently only available on web.
      </Text>
      <Text style={styles.subText}>
        Please use the web version to view the disease map.
      </Text>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
    backgroundColor: '#f5f5f5',
    borderRadius: 12,
  },
  text: {
    fontSize: 18,
    fontWeight: 'bold',
    textAlign: 'center',
    marginBottom: 10,
  },
  subText: {
    fontSize: 14,
    textAlign: 'center',
    opacity: 0.7,
  }
});

export default Map;
