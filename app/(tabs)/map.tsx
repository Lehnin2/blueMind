import React, { useState, useEffect } from 'react';
import { StyleSheet, View, Text, ActivityIndicator, ScrollView, TouchableOpacity } from 'react-native';
import { useColorScheme } from '@/hooks/useColorScheme';
import PageContainer from '@/components/PageContainer';
import HeaderBar from '@/components/HeaderBar';
import Map from '@/components/Map';
import Colors from '@/constants/Colors';
import { Platform } from 'react-native';
import { useReports, Report } from '@/services/reports';
import { router } from 'expo-router';

// Interface for map markers
interface MapMarker {
  id: string;
  coordinate: {
    latitude: number;
    longitude: number;
  };
  isHealthy: boolean;
  title: string;
  description: string;
  diseaseType?: string;
  onPress: () => void;
}

// Disease types and their colors for the filter
const diseaseTypes = [
  { id: 'Healthy', name: 'Healthy Fish', color: '#2e7d32' },
  { id: 'Bacterial Red disease', name: 'Bacterial Red', color: '#d32f2f' },
  { id: 'Bacterial diseases - Aeromoniasis', name: 'Aeromoniasis', color: '#c62828' },
  { id: 'Bacterial gill disease', name: 'Gill Disease', color: '#ff9800' },
  { id: 'Fungal diseases Saprolegniasis', name: 'Fungal', color: '#9c27b0' },
  { id: 'Parasitic diseases', name: 'Parasitic', color: '#5d8aa8' },
  { id: 'Viral diseases White tail disease', name: 'Viral', color: '#1976d2' },
  { id: 'Unknown', name: 'Unknown', color: '#757575' }
];

// Simple map screen component that works on both web and mobile
export default function MapScreen() {
  const colorScheme = useColorScheme();
  const { getReportsWithLocation } = useReports();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [markers, setMarkers] = useState<MapMarker[]>([]);
  const [region, setRegion] = useState({
    latitude: 0,
    longitude: 0,
    latitudeDelta: 0.0922,
    longitudeDelta: 0.0421,
    zoom: 13
  });
  const [showFilters, setShowFilters] = useState(false);
  const [selectedDiseaseTypes, setSelectedDiseaseTypes] = useState<string[]>([]);

  useEffect(() => {
    loadReportsWithLocation();
  }, []);

  const loadReportsWithLocation = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const reports = await getReportsWithLocation();
      
      if (reports.length > 0) {
        // Set initial map region to the first report's location
        const firstReport = reports[0];
        if (firstReport.latitude && firstReport.longitude) {
          setRegion({
            latitude: firstReport.latitude,
            longitude: firstReport.longitude,
            latitudeDelta: 0.0922,
            longitudeDelta: 0.0421,
            zoom: 13
          });
        }
        
        // Convert reports to map markers
        const mapMarkers = reports.map((report) => ({
          id: report.id,
          coordinate: {
            latitude: report.latitude || 0,
            longitude: report.longitude || 0,
          },
          isHealthy: report.status === 'resolved',
          title: report.title || 'Fish Disease Report',
          description: report.description || 'No description provided',
          diseaseType: report.disease_type || 'Unknown',
          onPress: () => handleMarkerPress(report),
        }));
        
        setMarkers(mapMarkers);
      }
    } catch (error) {
      console.error('Failed to load reports with location:', error);
      setError('Failed to load disease reports. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleMarkerPress = (report: Report) => {
    // Navigate to report detail or show a modal with report details
    console.log('Report selected:', report);
    // You could implement navigation to a detail screen here
    // router.push(`/reports/${report.id}`);
  };

  const handleRegionChange = (newRegion: typeof region) => {
    setRegion(newRegion);
  };

  const toggleDiseaseTypeFilter = (diseaseType: string) => {
    setSelectedDiseaseTypes(prev => {
      if (prev.includes(diseaseType)) {
        return prev.filter(type => type !== diseaseType);
      } else {
        return [...prev, diseaseType];
      }
    });
  };

  const toggleAllDiseaseTypes = () => {
    if (selectedDiseaseTypes.length === diseaseTypes.length) {
      // If all are selected, clear all
      setSelectedDiseaseTypes([]);
    } else {
      // Otherwise, select all
      setSelectedDiseaseTypes(diseaseTypes.map(type => type.id));
    }
  };

  const renderFilterChips = () => {
    return (
      <View style={styles.filterContainer}>
        <View style={styles.filterHeader}>
          <Text style={[styles.filterTitle, { color: Colors[colorScheme].text }]}>
            Filter by Disease Type
          </Text>
          <TouchableOpacity 
            style={styles.toggleAllButton}
            onPress={toggleAllDiseaseTypes}
          >
            <Text style={[styles.toggleAllText, { color: Colors[colorScheme].primary }]}>
              {selectedDiseaseTypes.length === diseaseTypes.length ? 'Clear All' : 'Select All'}
            </Text>
          </TouchableOpacity>
        </View>
        
        <ScrollView 
          horizontal 
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.chipContainer}
        >
          {diseaseTypes.map(type => (
            <TouchableOpacity
              key={type.id}
              style={[
                styles.chip,
                { 
                  backgroundColor: selectedDiseaseTypes.includes(type.id) 
                    ? type.color 
                    : 'transparent',
                  borderColor: type.color
                }
              ]}
              onPress={() => toggleDiseaseTypeFilter(type.id)}
            >
              <Text 
                style={[
                  styles.chipText, 
                  { 
                    color: selectedDiseaseTypes.includes(type.id) 
                      ? 'white' 
                      : type.color 
                  }
                ]}
              >
                {type.name}
              </Text>
            </TouchableOpacity>
          ))}
        </ScrollView>
      </View>
    );
  };

  return (
    <PageContainer>
      <HeaderBar 
        title="Disease Map"
        subtitle="View disease reports by location"
        rightAction={{
          icon: 'filter',
          onPress: () => setShowFilters(!showFilters)
        }}
      />
      
      {showFilters && renderFilterChips()}
      
      {loading ? (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={Colors[colorScheme].primary} />
          <Text style={[styles.loadingText, { color: Colors[colorScheme].text }]}>
            Loading disease reports...
          </Text>
        </View>
      ) : error ? (
        <View style={styles.errorContainer}>
          <Text style={[styles.errorText, { color: Colors[colorScheme].error }]}>
            {error}
          </Text>
          <Text 
            style={[styles.retryText, { color: Colors[colorScheme].primary }]}
            onPress={loadReportsWithLocation}
          >
            Tap to retry
          </Text>
        </View>
      ) : (
        <View style={styles.mapContainer}>
          <Map
            region={region}
            markers={markers}
            onRegionChange={handleRegionChange}
            filteredDiseaseTypes={selectedDiseaseTypes}
          />
          <View style={styles.statsContainer}>
            <Text style={[styles.statsText, { color: Colors[colorScheme].text }]}>
              {markers.length} disease reports found
              {selectedDiseaseTypes.length > 0 && ` • ${selectedDiseaseTypes.length} filters active`}
            </Text>
          </View>
        </View>
      )}
    </PageContainer>
  );
}

const styles = StyleSheet.create({
  mapContainer: {
    flex: 1,
    margin: 16,
    borderRadius: 12,
    overflow: 'hidden',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 12,
    fontSize: 16,
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  errorText: {
    fontSize: 16,
    textAlign: 'center',
    marginBottom: 12,
  },
  retryText: {
    fontSize: 16,
    fontWeight: 'bold',
  },
  statsContainer: {
    position: 'absolute',
    bottom: 16,
    left: 16,
    right: 16,
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
    padding: 8,
    borderRadius: 8,
    alignItems: 'center',
  },
  statsText: {
    fontSize: 14,
    fontWeight: 'bold',
  },
  filterContainer: {
    padding: 16,
    backgroundColor: 'rgba(0, 0, 0, 0.05)',
    borderRadius: 12,
    margin: 16,
    marginBottom: 0,
  },
  filterHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  filterTitle: {
    fontSize: 16,
    fontWeight: 'bold',
  },
  toggleAllButton: {
    padding: 4,
  },
  toggleAllText: {
    fontSize: 14,
    fontWeight: 'bold',
  },
  chipContainer: {
    paddingVertical: 8,
  },
  chip: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
    marginRight: 8,
    borderWidth: 1,
  },
  chipText: {
    fontSize: 14,
    fontWeight: '500',
  },
});