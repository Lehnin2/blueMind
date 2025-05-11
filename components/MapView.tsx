import React, { useEffect, useRef, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap, ZoomControl, useMapEvents } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { StyleSheet, View, Text } from 'react-native';
import L from 'leaflet';

// Create a map of disease types to colors
const diseaseColorMap: Record<string, string> = {
  'Bacterial Red disease': 'red',
  'Bacterial diseases - Aeromoniasis': 'darkred',
  'Bacterial gill disease': 'orange',
  'Fungal diseases Saprolegniasis': 'purple',
  'Parasitic diseases': 'cadetblue',
  'Viral diseases White tail disease': 'blue',
  'Unknown': 'grey',
  'Healthy': 'green'
};

// Function to get a marker icon based on disease type
const getMarkerIcon = (diseaseType: string | null, isHealthy: boolean) => {
  if (isHealthy) {
    return new L.Icon({
      iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-green.png',
      shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
      iconSize: [25, 41],
      iconAnchor: [12, 41],
      popupAnchor: [1, -34],
      shadowSize: [41, 41]
    });
  }

  // Get color based on disease type
  let color = diseaseColorMap[diseaseType || 'Unknown'] || 'red';
  
  // Map color name to marker URL
  const colorUrlMap: Record<string, string> = {
    'red': 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png',
    'darkred': 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png',
    'orange': 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-orange.png',
    'purple': 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-violet.png',
    'cadetblue': 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-blue.png',
    'blue': 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-blue.png',
    'grey': 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-grey.png',
    'green': 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-green.png'
  };

  return new L.Icon({
    iconUrl: colorUrlMap[color] || 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41]
  });
};

// This component handles map center updates and events
const MapController = ({ 
  center, 
  zoom,
  onMoveEnd
}: { 
  center: [number, number], 
  zoom: number,
  onMoveEnd: (center: L.LatLng, zoom: number) => void
}) => {
  const map = useMap();
  
  // Set view when center or zoom changes
  useEffect(() => {
    if (map) {
      map.setView(center, zoom);
    }
  }, [map, center, zoom]);
  
  // Set up event listeners
  useEffect(() => {
    if (!map) return;
    
    const moveEndHandler = () => {
      const center = map.getCenter();
      const zoom = map.getZoom();
      console.log("Map moved/zoomed:", { center, zoom });
      onMoveEnd(center, zoom);
    };
    
    // Add event listeners for all map interactions
    map.on('moveend', moveEndHandler);
    map.on('zoomend', moveEndHandler);
    map.on('drag', () => console.log("Map dragging"));
    map.on('click', (e) => console.log("Map clicked at:", e.latlng));
    
    // Enable all map interactions
    map.dragging.enable();
    map.touchZoom.enable();
    map.doubleClickZoom.enable();
    map.scrollWheelZoom.enable();
    map.boxZoom.enable();
    map.keyboard.enable();
    
    // Check if tap exists (it's not in the type definitions but may exist at runtime)
    if (map.hasOwnProperty('tap')) {
      (map as any).tap.enable();
    }
    
    return () => {
      map.off('moveend', moveEndHandler);
      map.off('zoomend', moveEndHandler);
      map.off('drag');
      map.off('click');
    };
  }, [map, onMoveEnd]);
  
  return null;
};

// Component to handle map click events
const MapClickHandler = ({ onClick }: { onClick: (e: L.LeafletMouseEvent) => void }) => {
  const map = useMapEvents({
    click: (e) => {
      console.log('Map clicked at:', e.latlng);
      onClick(e);
    }
  });
  
  return null;
};

// MapView for Web (using react-leaflet)
const WebMapView = ({ 
  markers, 
  region, 
  onRegionChange,
  filteredDiseaseTypes = []
}: {
  markers: Array<{
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
  }>;
  region: {
    latitude: number;
    longitude: number;
    latitudeDelta: number;
    longitudeDelta: number;
    zoom?: number;
  };
  onRegionChange: (region: {
    latitude: number;
    longitude: number;
    latitudeDelta: number;
    longitudeDelta: number;
    zoom: number;
  }) => void;
  filteredDiseaseTypes?: string[];
}) => {
  // Fix Leaflet's default icon issue
  useEffect(() => {
    // This is needed to fix the missing icon issue in Leaflet
    delete (L.Icon.Default.prototype as any)._getIconUrl;
    
    L.Icon.Default.mergeOptions({
      iconRetinaUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon-2x.png',
      iconUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon.png',
      shadowUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-shadow.png',
    });
  }, []);

  // Default center if region is not provided
  const center: [number, number] = [
    region?.latitude || 0, 
    region?.longitude || 0
  ];
  
  // Use the zoom from region or default to 13
  const zoom = region?.zoom || 13;
  
  // Handle map move events
  const handleMapMove = (mapCenter: L.LatLng, mapZoom: number) => {
    onRegionChange({
      latitude: mapCenter.lat,
      longitude: mapCenter.lng,
      latitudeDelta: 0.0922,
      longitudeDelta: 0.0421,
      zoom: mapZoom
    });
  };

  // Handle map click events
  const handleMapClick = (e: L.LeafletMouseEvent) => {
    console.log("Map clicked at:", e.latlng);
    // Pass the click event to the onRegionChange handler
    // This will be used to update the marker position
    onRegionChange({
      latitude: e.latlng.lat,
      longitude: e.latlng.lng,
      latitudeDelta: 0.0922,
      longitudeDelta: 0.0421,
      zoom: zoom
    });
  };

  // Filter markers based on selected disease types
  const filteredMarkers = markers.filter(marker => {
    // If no filters are selected, show all markers
    if (filteredDiseaseTypes.length === 0) return true;
    
    // If marker is healthy and "Healthy" is in the filter, show it
    if (marker.isHealthy && filteredDiseaseTypes.includes('Healthy')) return true;
    
    // If marker has a disease type and it's in the filter, show it
    return marker.diseaseType && filteredDiseaseTypes.includes(marker.diseaseType);
  });

  return (
    <View style={styles.container}>
      <MapContainer
        center={center}
        zoom={zoom}
        style={{ height: '100%', width: '100%' }}
        zoomControl={false} // Disable default zoom control to use our custom one
        doubleClickZoom={true}
        scrollWheelZoom={true}
        dragging={true}
        touchZoom={true}
      >
        {/* Add zoom control in a better position */}
        <ZoomControl position="bottomright" />
        
        {/* Controller component to update map center when region changes */}
        <MapController 
          center={center} 
          zoom={zoom} 
          onMoveEnd={handleMapMove}
        />
        
        {/* Component to handle map clicks */}
        <MapClickHandler onClick={handleMapClick} />
        
        <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
        
        {filteredMarkers.map((marker) => (
          <Marker
            key={marker.id}
            position={[
              marker.coordinate?.latitude || 0, 
              marker.coordinate?.longitude || 0
            ]}
            icon={getMarkerIcon(marker.diseaseType || null, marker.isHealthy)}
            eventHandlers={{
              click: () => marker.onPress && marker.onPress(),
            }}
          >
            <Popup>
              <div style={{ padding: '5px', maxWidth: '250px' }}>
                <h3 style={{ 
                  margin: '0 0 8px 0', 
                  color: marker.isHealthy ? '#2e7d32' : 
                    (diseaseColorMap[marker.diseaseType || 'Unknown'] || '#d32f2f')
                }}>
                  {marker.title}
                </h3>
                <p style={{ margin: '0 0 5px 0' }}>
                  <strong>Status:</strong> {marker.isHealthy ? 'Healthy' : 'Disease Detected'}
                </p>
                {!marker.isHealthy && marker.diseaseType && (
                  <p style={{ margin: '0 0 5px 0' }}>
                    <strong>Disease:</strong> {marker.diseaseType}
                  </p>
                )}
                <button 
                  onClick={() => marker.onPress()} 
                  style={{
                    background: '#1976d2',
                    color: 'white',
                    border: 'none',
                    padding: '5px 10px',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    marginTop: '5px'
                  }}
                >
                  View Details
                </button>
              </div>
            </Popup>
          </Marker>
        ))}
      </MapContainer>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    margin: 0,
    borderRadius: 12,
    overflow: 'hidden',
  },
});

export default WebMapView;