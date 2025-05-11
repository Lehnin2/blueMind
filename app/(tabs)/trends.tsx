import React, { useState, useEffect, useRef } from 'react';
import { StyleSheet, View, Text, ScrollView, Image, TextInput, TouchableOpacity, ActivityIndicator, Platform } from 'react-native';
import PageContainer from '@/components/PageContainer';
import HeaderBar from '@/components/HeaderBar';
import Card from '@/components/Card';
import Colors from '@/constants/Colors';
import { useColorScheme } from '@/hooks/useColorScheme';
import { BACKEND_URL } from '@/constants/Config';

// Only import MapView on web
const MapViewComponent = Platform.OS === 'web' 
  ? require('@/components/MapView').default 
  : () => null;

// Define the feature types
interface FeatureInput {
  latitude: string;
  longitude: string;
  water_temperature: string;
  water_salinity: string;
  water_ph: string;
  dissolved_oxygen: string;
  water_turbidity: string;
  fish_density: string;
  season: string;
  fish_species: string;
  fish_age: string;
  title: string;
  description: string;
  location_name: string;
}

// Define the prediction result type
interface PredictionResult {
  prediction_id: string;
  prediction: string;
  probabilities: Record<string, number>;
  input_features: Record<string, any>;
  plots: Record<string, string>;
  xai_results: Record<string, any>;
  top_features: string[];
  gemini_explanation: string;
  errors?: Record<string, string>;
}

// Main component
function ExplainableAIScreen() {
  const colorScheme = useColorScheme();
  const isDark = colorScheme === 'dark';
  
  // Default feature values
  const defaultFeatures: FeatureInput = {
    latitude: '36.8065',
    longitude: '10.1815',
    water_temperature: '27.5',
    water_salinity: '38.2',
    water_ph: '7.9',
    dissolved_oxygen: '5.8',
    water_turbidity: '6.2',
    fish_density: '85',
    season: 'Summer',
    fish_species: 'Sea Bass (Dicentrarchus labrax)',
    fish_age: 'Adult',
    title: 'Sample analysis',
    description: 'Fish showing abnormal behavior',
    location_name: 'Gulf of Tunis',
  };
  
  // State for input features
  const [features, setFeatures] = useState<FeatureInput>(defaultFeatures);
  
  // State for prediction results
  const [predictionResult, setPredictionResult] = useState<PredictionResult | null>(null);
  
  // Loading state
  const [loading, setLoading] = useState(false);
  
  // Error state
  const [error, setError] = useState<string | null>(null);
  
  // Map marker position
  const [markerPosition, setMarkerPosition] = useState({
    latitude: parseFloat(defaultFeatures.latitude),
    longitude: parseFloat(defaultFeatures.longitude),
  });
  
  // Season options with icons
  const seasonOptions = [
    { value: 'Spring', icon: '🌱', color: '#4caf50' },
    { value: 'Summer', icon: '☀️', color: '#ff9800' },
    { value: 'Fall', icon: '🍂', color: '#795548' },
    { value: 'Winter', icon: '❄️', color: '#2196f3' },
  ];
  
  // Handle input change
  const handleInputChange = (name: keyof FeatureInput, value: string) => {
    setFeatures(prev => ({ ...prev, [name]: value }));
  };
  
  // Handle map marker change from region change event
  const handleRegionChange = (region: {
    latitude: number;
    longitude: number;
    latitudeDelta: number;
    longitudeDelta: number;
    zoom: number;
  }) => {
    console.log("Region changed:", region);
    
    // Check if this is a click event (we can tell by checking if the lat/lng values have many decimal places)
    const isClickEvent = 
      region.latitude.toString().includes('.') && 
      region.latitude.toString().split('.')[1].length > 5;
      
    if (isClickEvent) {
      // Update marker position when it's a click event
      setMarkerPosition({
        latitude: region.latitude,
        longitude: region.longitude
      });
      setFeatures(prev => ({
        ...prev,
        latitude: region.latitude.toString(),
        longitude: region.longitude.toString(),
      }));
    }
    // Otherwise, it's just a zoom/pan event, so don't update the marker
  };
  
  // Handle map marker change
  const handleMapPress = (event: any) => {
    if (Platform.OS === 'web') {
      // For web, we'll get the coordinates from the event
      const { lat, lng } = event.latlng;
      setMarkerPosition({ latitude: lat, longitude: lng });
      setFeatures(prev => ({
        ...prev,
        latitude: lat.toString(),
        longitude: lng.toString(),
      }));
    } else {
      // For mobile (if we ever implement a map on mobile)
      const { latitude, longitude } = event.nativeEvent.coordinate;
      setMarkerPosition({ latitude, longitude });
      setFeatures(prev => ({
        ...prev,
        latitude: latitude.toString(),
        longitude: longitude.toString(),
      }));
    }
  };
  
  // Handle form submission
  const handleSubmit = async () => {
    setLoading(true);
    setError(null);
    setPredictionResult(null);
    
    try {
      // Prepare all features - use the visible ones from the form and defaults for the rest
      const processedFeatures = {
        ...defaultFeatures,
        ...features,
        latitude: markerPosition.latitude.toString(),
        longitude: markerPosition.longitude.toString(),
      };
      
      // Convert numeric values to numbers
      const numericFeatures = ['water_temperature', 'water_salinity', 'water_ph', 
                              'dissolved_oxygen', 'water_turbidity', 'fish_density',
                              'latitude', 'longitude'];
      
      numericFeatures.forEach(feature => {
        const key = feature as keyof FeatureInput;
        processedFeatures[key] = processedFeatures[key].trim();
        if (processedFeatures[key] !== '') {
          processedFeatures[key] = parseFloat(processedFeatures[key]) as any;
        }
      });
      
      // Make API call
      const response = await fetch(`${BACKEND_URL}/api/xai/predict`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(processedFeatures),
      });
      
      if (!response.ok) {
        throw new Error(`Server responded with status: ${response.status}`);
      }
      
      const result = await response.json();
      
      if (result.error) {
        throw new Error(result.error);
      }
      
      setPredictionResult(result);
    } catch (err: any) {
      setError(err.message || 'An error occurred during prediction');
      console.error('Prediction error:', err);
    } finally {
      setLoading(false);
    }
  };
  
  // Reset form to default values
  const handleReset = () => {
    setFeatures(defaultFeatures);
    setMarkerPosition({
      latitude: parseFloat(defaultFeatures.latitude),
      longitude: parseFloat(defaultFeatures.longitude),
    });
    setPredictionResult(null);
    setError(null);
  };
  
  // Format probability as percentage
  const formatProbability = (prob: number) => {
    return `${(prob * 100).toFixed(1)}%`;
  };
  
  // Get color based on disease type
  const getDiseaseColor = (disease: string) => {
    const colors: Record<string, string> = {
      'Bacterial Red disease': '#ff3b30',
      'Fungal diseases Saprolegniasis': '#ff9500',
      'Parasitic diseases': '#5856d6',
      'Bacterial diseases - Aeromoniasis': '#ff2d55',
      'Bacterial gill disease': '#af52de',
      'Viral diseases White tail disease': '#007aff',
    };
    
    return colors[disease] || Colors[colorScheme].primary;
  };
  
  // Render map for web or location input for mobile
  const renderLocationInput = () => {
    if (Platform.OS === 'web') {
      return (
        <View style={styles.mapContainer}>
          <View style={styles.map}>
            {MapViewComponent && (
              <MapViewComponent
                markers={[{
                  id: '1',
                  coordinate: {
                    latitude: markerPosition.latitude,
                    longitude: markerPosition.longitude
                  },
                  isHealthy: false,
                  title: 'Selected Location',
                  description: `Lat: ${markerPosition.latitude.toFixed(4)}, Lng: ${markerPosition.longitude.toFixed(4)}`,
                  onPress: () => {}
                }]}
                region={{
                  latitude: parseFloat(defaultFeatures.latitude),
                  longitude: parseFloat(defaultFeatures.longitude),
                  latitudeDelta: 2,
                  longitudeDelta: 2,
                  zoom: 8
                }}
                onRegionChange={handleRegionChange}
                filteredDiseaseTypes={[]}
              />
            )}
          </View>
          <View style={styles.mapOverlay}>
            <Text style={styles.mapInstructions}>
              Tap to select a location
            </Text>
            <Text style={styles.coordinatesText}>
              {`Lat: ${markerPosition.latitude.toFixed(4)}, Lng: ${markerPosition.longitude.toFixed(4)}`}
            </Text>
          </View>
        </View>
      );
    } else {
      // Simple location input for mobile
      return (
        <View style={styles.mobileLocationContainer}>
          <Text style={styles.mobileLocationTitle}>Location</Text>
          <View style={styles.locationPresets}>
            {['Gulf of Tunis', 'Monastir', 'Sfax', 'Bizerte', 'Sousse'].map(location => (
              <TouchableOpacity
                key={location}
                style={[
                  styles.locationPresetButton,
                  features.location_name === location && styles.locationPresetButtonActive
                ]}
                onPress={() => {
                  // Set predefined coordinates based on location
                  let lat = 36.8065;
                  let lng = 10.1815;
                  
                  if (location === 'Monastir') {
                    lat = 35.7775;
                    lng = 10.8262;
                  } else if (location === 'Sfax') {
                    lat = 34.7478;
                    lng = 10.7661;
                  } else if (location === 'Bizerte') {
                    lat = 37.2746;
                    lng = 9.8714;
                  } else if (location === 'Sousse') {
                    lat = 35.8245;
                    lng = 10.6346;
                  }
                  
                  setMarkerPosition({ latitude: lat, longitude: lng });
                  setFeatures(prev => ({
                    ...prev,
                    latitude: lat.toString(),
                    longitude: lng.toString(),
                    location_name: location
                  }));
                }}
              >
                <Text style={[
                  styles.locationPresetText,
                  features.location_name === location && styles.locationPresetTextActive
                ]}>
                  {location}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>
      );
    }
  };
  
  return (
    <PageContainer>
      <HeaderBar 
        title="Explainable AI"
        subtitle="Analyze and predict fish diseases"
      />
      
      <ScrollView style={styles.container} showsVerticalScrollIndicator={false}>
        {!predictionResult ? (
          <Card style={styles.formCard}>
            <Text style={[styles.sectionTitle, { color: Colors[colorScheme].text }]}>
              Disease Prediction
            </Text>
            <Text style={styles.sectionDescription}>
              {Platform.OS === 'web' 
                ? 'Select a location on the map and choose a season to predict potential fish diseases.'
                : 'Select a location and season to predict potential fish diseases.'}
            </Text>
            
            {/* Map for web or location selector for mobile */}
            {renderLocationInput()}
            
            {/* Season selection */}
            <View style={styles.formSection}>
              <Text style={styles.formSectionTitle}>Select Season</Text>
              <View style={styles.seasonContainer}>
                {seasonOptions.map((season) => (
                  <TouchableOpacity
                    key={season.value}
                    style={[
                      styles.seasonButton,
                      features.season === season.value && { 
                        backgroundColor: season.color,
                        borderColor: season.color,
                      }
                    ]}
                    onPress={() => handleInputChange('season', season.value)}
                  >
                    <Text style={styles.seasonIcon}>{season.icon}</Text>
                    <Text 
                      style={[
                        styles.seasonText,
                        features.season === season.value && { color: '#fff' }
                      ]}
                    >
                      {season.value}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>
            
            <View style={styles.buttonContainer}>
              <TouchableOpacity 
                style={[styles.button, styles.resetButton]} 
                onPress={handleReset}
              >
                <Text style={[styles.buttonText, { color: '#555' }]}>Reset</Text>
              </TouchableOpacity>
              <TouchableOpacity 
                style={[styles.button, styles.predictButton]} 
                onPress={handleSubmit}
                disabled={loading}
              >
                {loading ? (
                  <ActivityIndicator color="#fff" size="small" />
                ) : (
                  <Text style={styles.buttonText}>Predict</Text>
                )}
              </TouchableOpacity>
            </View>
            
            {error && (
              <View style={styles.errorContainer}>
                <Text style={styles.errorText}>{error}</Text>
              </View>
            )}
          </Card>
        ) : (
          <>
            <Card style={{
              ...styles.resultCard, 
              backgroundColor: isDark ? '#1c1c1e' : '#fff'
            }}>
              <View style={styles.resultHeader}>
                <Text style={[styles.resultTitle, { color: isDark ? '#fff' : '#333' }]}>Prediction Results</Text>
                <TouchableOpacity 
                  style={styles.backButton} 
                  onPress={() => setPredictionResult(null)}
                >
                  <Text style={styles.backButtonText}>Back to Form</Text>
                </TouchableOpacity>
              </View>
              
              <View style={styles.predictionContainer}>
                <Text style={[styles.predictionLabel, { color: isDark ? '#fff' : '#333' }]}>Predicted Disease:</Text>
                <View style={[styles.diseaseBadge, { backgroundColor: getDiseaseColor(predictionResult.prediction) }]}>
                  <Text style={styles.diseaseName}>{predictionResult.prediction}</Text>
                </View>
              </View>
              
              <Text style={[styles.probabilitiesTitle, { color: isDark ? '#fff' : '#333' }]}>Prediction Probabilities:</Text>
              {Object.entries(predictionResult.probabilities)
                .sort(([, a], [, b]) => b - a)
                .map(([disease, probability]) => (
                  <View key={disease} style={styles.probabilityItem}>
                    <View style={styles.probabilityLabelContainer}>
                      <View 
                        style={[
                          styles.diseaseIndicator, 
                          { backgroundColor: getDiseaseColor(disease) }
                        ]} 
                      />
                      <Text style={[styles.probabilityLabel, { color: isDark ? '#eee' : '#555' }]}>{disease}</Text>
                    </View>
                    <View style={[styles.probabilityBarContainer, { backgroundColor: isDark ? '#333' : '#f1f1f1' }]}>
                      <View 
                        style={[
                          styles.probabilityBar, 
                          { 
                            width: `${probability * 100}%`,
                            backgroundColor: getDiseaseColor(disease)
                          }
                        ]} 
                      />
                      <Text style={styles.probabilityValue}>
                        {formatProbability(probability)}
                      </Text>
                    </View>
                  </View>
                ))}
            </Card>
            
            <Card style={{
              ...styles.explanationCard, 
              backgroundColor: isDark ? '#1c1c1e' : '#fff'
            }}>
              <Text style={[styles.explanationTitle, { color: isDark ? '#fff' : '#333' }]}>Explainable AI Analysis</Text>
              
              <View style={styles.plotsContainer}>
                {predictionResult.plots.rf_importance && (
                  <View style={styles.plotWrapper}>
                    <Text style={[styles.plotTitle, { color: isDark ? '#fff' : '#333' }]}>Feature Importance</Text>
                    <Image
                      source={{ uri: `${BACKEND_URL}${predictionResult.plots.rf_importance}` }}
                      style={styles.plotImage}
                      resizeMode="contain"
                    />
                  </View>
                )}
                
                {predictionResult.plots.lime && (
                  <View style={styles.plotWrapper}>
                    <Text style={[styles.plotTitle, { color: isDark ? '#fff' : '#333' }]}>LIME Explanation</Text>
                    <Image
                      source={{ uri: `${BACKEND_URL}${predictionResult.plots.lime}` }}
                      style={styles.plotImage}
                      resizeMode="contain"
                    />
                  </View>
                )}
              </View>
              
              {predictionResult.top_features && predictionResult.top_features.length > 0 && (
                <>
                  <Text style={[styles.featureListTitle, { color: isDark ? '#fff' : '#333' }]}>Top Influential Features:</Text>
                  <View style={[styles.featureList, { backgroundColor: isDark ? '#2c2c2e' : '#f9f9f9' }]}>
                    {predictionResult.top_features.map((feature, index) => (
                      <View key={feature} style={styles.featureItem}>
                        <Text style={[styles.featureRank, { backgroundColor: getDiseaseColor(predictionResult.prediction) }]}>{index + 1}</Text>
                        <Text style={[styles.featureName, { color: isDark ? '#eee' : '#555' }]}>{feature}</Text>
                      </View>
                    ))}
                  </View>
                </>
              )}
            </Card>
            
            <Card style={{
              ...styles.geminiCard, 
              backgroundColor: isDark ? '#1c1c1e' : '#fff'
            }}>
              <Text style={[styles.geminiTitle, { color: isDark ? '#fff' : '#333' }]}>AI-Powered Analysis</Text>
              {predictionResult.gemini_explanation ? (
                <Text style={[styles.geminiText, { color: isDark ? '#eee' : '#333' }]}>
                  {predictionResult.gemini_explanation}
                </Text>
              ) : (
                <Text style={styles.loadingText}>
                  Generating detailed analysis...
                </Text>
              )}
            </Card>
          </>
        )}
      </ScrollView>
    </PageContainer>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  formCard: {
    marginBottom: 24,
    padding: 20,
  },
  sectionTitle: {
    fontFamily: 'Inter-Bold',
    fontSize: 22,
    marginBottom: 8,
  },
  sectionDescription: {
    fontFamily: 'Inter-Regular',
    fontSize: 16,
    color: '#666',
    marginBottom: 24,
  },
  mapContainer: {
    height: 300,
    borderRadius: 16,
    overflow: 'hidden',
    marginBottom: 24,
    position: 'relative',
  },
  map: {
    width: '100%',
    height: '100%',
  },
  mapOverlay: {
    position: 'absolute',
    bottom: 16,
    left: 16,
    right: 16,
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
    borderRadius: 8,
    padding: 12,
  },
  mapInstructions: {
    color: '#fff',
    fontFamily: 'Inter-Medium',
    fontSize: 14,
    marginBottom: 4,
  },
  coordinatesText: {
    color: '#fff',
    fontFamily: 'Inter-Regular',
    fontSize: 12,
  },
  // Mobile location styles
  mobileLocationContainer: {
    marginBottom: 24,
  },
  mobileLocationTitle: {
    fontFamily: 'Inter-SemiBold',
    fontSize: 18,
    color: '#333',
    marginBottom: 16,
  },
  locationPresets: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  locationPresetButton: {
    width: '48%',
    backgroundColor: '#f9f9f9',
    borderRadius: 12,
    borderWidth: 2,
    borderColor: '#ddd',
    padding: 16,
    marginBottom: 12,
    alignItems: 'center',
  },
  locationPresetButtonActive: {
    backgroundColor: '#38ada9',
    borderColor: '#38ada9',
  },
  locationPresetText: {
    fontFamily: 'Inter-Medium',
    fontSize: 14,
    color: '#333',
  },
  locationPresetTextActive: {
    color: '#fff',
  },
  formSection: {
    marginBottom: 24,
  },
  formSectionTitle: {
    fontFamily: 'Inter-SemiBold',
    fontSize: 18,
    color: '#333',
    marginBottom: 16,
  },
  seasonContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    flexWrap: 'wrap',
  },
  seasonButton: {
    width: '48%',
    backgroundColor: '#f9f9f9',
    borderRadius: 12,
    borderWidth: 2,
    borderColor: '#ddd',
    padding: 16,
    marginBottom: 16,
    alignItems: 'center',
  },
  seasonIcon: {
    fontSize: 24,
    marginBottom: 8,
  },
  seasonText: {
    fontFamily: 'Inter-Medium',
    fontSize: 16,
    color: '#333',
  },
  buttonContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 16,
  },
  button: {
    flex: 1,
    height: 50,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
    marginHorizontal: 4,
  },
  resetButton: {
    backgroundColor: '#f1f1f1',
    borderWidth: 1,
    borderColor: '#ddd',
  },
  predictButton: {
    backgroundColor: '#38ada9',
  },
  buttonText: {
    fontFamily: 'Inter-SemiBold',
    fontSize: 16,
    color: '#fff',
  },
  errorContainer: {
    marginTop: 16,
    padding: 12,
    backgroundColor: '#ffebee',
    borderRadius: 8,
  },
  errorText: {
    fontFamily: 'Inter-Regular',
    fontSize: 14,
    color: '#d32f2f',
  },
  resultCard: {
    marginBottom: 24,
    padding: 20,
    borderRadius: 16,
  },
  resultHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
  },
  resultTitle: {
    fontFamily: 'Inter-Bold',
    fontSize: 22,
  },
  backButton: {
    padding: 8,
    backgroundColor: '#38ada9',
    borderRadius: 8,
  },
  backButtonText: {
    fontFamily: 'Inter-Medium',
    fontSize: 14,
    color: '#fff',
  },
  predictionContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 20,
  },
  predictionLabel: {
    fontFamily: 'Inter-SemiBold',
    fontSize: 18,
    marginRight: 10,
  },
  diseaseBadge: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
  },
  diseaseName: {
    fontFamily: 'Inter-SemiBold',
    fontSize: 16,
    color: '#fff',
  },
  probabilitiesTitle: {
    fontFamily: 'Inter-SemiBold',
    fontSize: 16,
    marginBottom: 12,
  },
  probabilityItem: {
    marginBottom: 12,
  },
  probabilityLabelContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 4,
  },
  diseaseIndicator: {
    width: 12,
    height: 12,
    borderRadius: 6,
    marginRight: 8,
  },
  probabilityLabel: {
    fontFamily: 'Inter-Medium',
    fontSize: 14,
    flex: 1,
  },
  probabilityBarContainer: {
    height: 20,
    borderRadius: 10,
    overflow: 'hidden',
    position: 'relative',
  },
  probabilityBar: {
    height: '100%',
    borderRadius: 10,
  },
  probabilityValue: {
    position: 'absolute',
    right: 8,
    top: 0,
    bottom: 0,
    textAlignVertical: 'center',
    fontFamily: 'Inter-Bold',
    fontSize: 12,
    color: '#fff',
  },
  explanationCard: {
    marginBottom: 24,
    padding: 20,
    borderRadius: 16,
  },
  explanationTitle: {
    fontFamily: 'Inter-Bold',
    fontSize: 20,
    marginBottom: 16,
  },
  plotsContainer: {
    flexDirection: 'column',
  },
  plotWrapper: {
    marginBottom: 24,
  },
  plotTitle: {
    fontFamily: 'Inter-SemiBold',
    fontSize: 16,
    marginBottom: 12,
  },
  plotImage: {
    width: '100%',
    height: 300,
    backgroundColor: '#fff',
    borderRadius: 12,
  },
  featureListTitle: {
    fontFamily: 'Inter-SemiBold',
    fontSize: 16,
    marginBottom: 12,
  },
  featureList: {
    borderRadius: 12,
    padding: 16,
  },
  featureItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  featureRank: {
    width: 28,
    height: 28,
    borderRadius: 14,
    color: '#fff',
    fontFamily: 'Inter-Bold',
    fontSize: 14,
    textAlign: 'center',
    textAlignVertical: 'center',
    marginRight: 12,
    paddingTop: Platform.OS === 'android' ? 2 : 4,
  },
  featureName: {
    fontFamily: 'Inter-Medium',
    fontSize: 15,
  },
  geminiCard: {
    marginBottom: 24,
    padding: 20,
    borderRadius: 16,
  },
  geminiTitle: {
    fontFamily: 'Inter-Bold',
    fontSize: 20,
    marginBottom: 16,
  },
  geminiText: {
    fontFamily: 'Inter-Regular',
    fontSize: 16,
    lineHeight: 24,
  },
  loadingText: {
    fontFamily: 'Inter-Italic',
    fontSize: 16,
    color: '#888',
    fontStyle: 'italic',
  },
});

// Export the component as default
export default ExplainableAIScreen;