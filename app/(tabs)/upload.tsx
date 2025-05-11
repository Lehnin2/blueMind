import { useState } from 'react';
import { StyleSheet, Text, View, Image, Platform, ActivityIndicator, Alert, TextInput } from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import * as Location from 'expo-location';
import { useRouter } from 'expo-router';
import { Camera, Upload, X, Check } from 'lucide-react-native';
import PageContainer from '@/components/PageContainer';
import HeaderBar from '@/components/HeaderBar';
import Card from '@/components/Card';
import Button from '@/components/Button';
import Colors from '@/constants/Colors';
import { useColorScheme } from '@/hooks/useColorScheme';
import { uploadImages, DiseaseDetectionResult } from '@/services/api';
import { useAuthStore } from '@/services/auth';
import { useReports } from '@/services/reports';

type ImageData = {
  uri: string;
  name: string;
  type: string;
};

export default function UploadScreen() {
  const colorScheme = useColorScheme();
  const router = useRouter();
  const { user } = useAuthStore();
  const { createReport } = useReports();
  const [images, setImages] = useState<ImageData[]>([]);
  const [uploading, setUploading] = useState(false);
  const [results, setResults] = useState<DiseaseDetectionResult[]>([]);
  const [step, setStep] = useState<'select' | 'confirm' | 'results'>('select');
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [analysis, setAnalysis] = useState<any>(null);
  const [saving, setSaving] = useState(false);
  const [location, setLocation] = useState<Location.LocationObject | null>(null);
  const [locationName, setLocationName] = useState<string>('');
  const [customLocationEnabled, setCustomLocationEnabled] = useState(false);
  const [customLocation, setCustomLocation] = useState<string>('');
  const [customLatitude, setCustomLatitude] = useState<string>('');
  const [customLongitude, setCustomLongitude] = useState<string>('');

  const pickImage = async () => {
    try {
      if (Platform.OS !== 'web') {
        const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
        if (status !== 'granted') {
          Alert.alert(
            'Permission Required',
            'Sorry, we need camera roll permissions to make this work! Please enable it in your phone settings.',
            [
              { text: 'OK', style: 'default' }
            ]
          );
          return;
        }
      }

      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Images,
        allowsEditing: true,
        aspect: [4, 3],
        quality: 0.8,
        allowsMultipleSelection: Platform.OS === 'web',
      });

      if (result.canceled) {
        console.log('User canceled image picker');
        return;
      }

      if (result.assets && result.assets.length > 0) {
        for (const asset of result.assets) {
          if (asset.uri) {
            processImage(asset.uri);
          }
        }
      } else {
        console.warn('No assets found in picker result', result);
        Alert.alert('Error', 'Could not get the selected image. Please try again.');
      }
    } catch (error) {
      console.error('Error picking image:', error);
      Alert.alert('Error', 'There was a problem selecting the image. Please try again.');
    }
  };

  const takePhoto = async () => {
    try {
      if (Platform.OS !== 'web') {
        const { status } = await ImagePicker.requestCameraPermissionsAsync();
        if (status !== 'granted') {
          Alert.alert(
            'Permission Required',
            'Sorry, we need camera permissions to make this work! Please enable it in your phone settings.',
            [
              { text: 'OK', style: 'default' }
            ]
          );
          return;
        }
      }

      const result = await ImagePicker.launchCameraAsync({
        allowsEditing: true,
        aspect: [4, 3],
        quality: 0.8,
      });

      if (result.canceled) {
        console.log('User canceled camera');
        return;
      }

      if (result.assets && result.assets.length > 0 && result.assets[0].uri) {
        processImage(result.assets[0].uri);
      } else {
        console.warn('No image captured', result);
        Alert.alert('Error', 'Could not capture the image. Please try again.');
      }
    } catch (error) {
      console.error('Error taking photo:', error);
      Alert.alert('Error', 'There was a problem capturing the image. Please try again.');
    }
  };

  const processImage = async (uri: string) => {
    try {
      console.log('Processing image URI:', uri);

      let fileName = '';
      if (uri.startsWith('file://') || uri.startsWith('content://')) {
        fileName = uri.split('/').pop() || `image-${Date.now()}.jpg`;
      } else if (uri.startsWith('data:')) {
        fileName = `image-${Date.now()}.jpg`;
      } else {
        fileName = uri.split('/').pop() || `image-${Date.now()}.jpg`;
      }

      const newImage = {
        uri,
        name: fileName,
        type: 'image/jpeg',
      };

      setImages(prevImages => [...prevImages, newImage]);
      console.log('Image added successfully:', fileName);
    } catch (error) {
      console.error('Error processing image:', error);
      Alert.alert('Error', 'Failed to process image. Please try again.');
    }
  };

  const removeImage = (index: number) => {
    const newImages = [...images];
    newImages.splice(index, 1);
    setImages(newImages);
  };

  const confirmImages = () => {
    if (images.length > 0) {
      setStep('confirm');
    } else {
      Alert.alert('No Images', 'Please select at least one image to continue.');
    }
  };

  const handleUpload = async () => {
    if (images.length === 0) return;

    setUploading(true);

    try {
      const apiResults = await uploadImages(images);

      if (apiResults.length === 0) {
        throw new Error('No valid predictions could be made from the provided images');
      }

      const firstResult = apiResults[0];
      setAnalysis({
        isHealthy: firstResult.isHealthy,
        diseaseType: firstResult.diseaseType,
        symptoms: firstResult.symptoms,
        treatments: firstResult.treatments,
        description: firstResult.description
      });

      if (images.length > 0) {
        setSelectedImage(images[0].uri);
      }

      setResults(apiResults);
      setStep('results');
    } catch (error) {
      console.error('Error analyzing images:', error);
      Alert.alert('Analysis Failed', 'There was an error analyzing your images. Please try again.');
    } finally {
      setUploading(false);
    }
  };

  const resetUpload = () => {
    setImages([]);
    setResults([]);
    setStep('select');
    setCustomLocation('');
    setCustomLatitude('');
    setCustomLongitude('');
    setLocation(null);
    setLocationName('');
    setCustomLocationEnabled(false);
  };

  // New: Let user choose to provide a custom location or use device location
  const getLocation = async () => {
    if (customLocationEnabled && customLocation && customLatitude && customLongitude) {
      // Use user-provided custom location
      setLocationName(customLocation);
      return {
        coords: {
          latitude: parseFloat(customLatitude),
          longitude: parseFloat(customLongitude),
        }
      } as Location.LocationObject;
    } else {
      // Use device location as fallback
      try {
        const { status } = await Location.requestForegroundPermissionsAsync();
        if (status !== 'granted') {
          Alert.alert(
            'Permission Required',
            'Location permission is required to save the report location. Please enable it in your phone settings.',
            [{ text: 'OK' }]
          );
          return null;
        }

        const deviceLocation = await Location.getCurrentPositionAsync({});
        setLocation(deviceLocation);

        // Get location name using reverse geocoding
        const geocode = await Location.reverseGeocodeAsync({
          latitude: deviceLocation.coords.latitude,
          longitude: deviceLocation.coords.longitude,
        });

        if (geocode.length > 0) {
          const place = geocode[0];
          const name = [
            place.name,
            place.street,
            place.city,
            place.region,
            place.country
          ].filter(Boolean).join(', ');
          setLocationName(name);
        }

        return deviceLocation;
      } catch (error) {
        console.error('Error getting location:', error);
        return null;
      }
    }
  };

  const handleSaveReport = async () => {
    if (!user?.id) {
      Alert.alert('Error', 'You must be logged in to save reports');
      return;
    }

    if (!analysis) {
      Alert.alert('Error', 'No analysis results to save');
      return;
    }

    try {
      setSaving(true);

      // Get location before saving (either user provided or device)
      const selectedLocation = await getLocation();

      const reportData = {
        user_id: user.id,
        title: `Analysis Report - ${new Date().toLocaleDateString()}`,
        description: `Analysis Results:\n\n${JSON.stringify(analysis, null, 2)}`,
        status: analysis.isHealthy ? 'resolved' : 'pending' as const,
        image_url: selectedImage || '',
        disease_type: analysis.diseaseType || null,
        latitude: customLocationEnabled && customLatitude
          ? parseFloat(customLatitude)
          : selectedLocation?.coords.latitude,
        longitude: customLocationEnabled && customLongitude
          ? parseFloat(customLongitude)
          : selectedLocation?.coords.longitude,
        location_name: customLocationEnabled && customLocation
          ? customLocation
          : locationName
      };

      console.log('Saving report with data:', reportData);
      await createReport({
        ...reportData,
        status: reportData.status as 'resolved' | 'pending' | 'in_progress'
      });
      Alert.alert('Success', 'Report saved successfully');
      router.replace('/reports');
    } catch (error) {
      console.error('Failed to save report:', error);
      Alert.alert('Error', 'Failed to save report. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  const renderLocationSection = () => (
    <Card style={styles.customLocationContainer}>
      <Text style={[styles.sectionTitle, { fontSize: 16, marginBottom: 4 }]}>
        Location for Report
      </Text>
      <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 12 }}>
        <Button
          title={customLocationEnabled ? 'Custom Location' : 'Current Location'}
          onPress={() => setCustomLocationEnabled(!customLocationEnabled)}
          variant={customLocationEnabled ? 'primary' : 'outline'}
          style={{ marginRight: 12, paddingHorizontal: 10 }}
        />
        <Text style={{ color: Colors[colorScheme].text, fontSize: 15 }}>
          {customLocationEnabled
            ? 'Enter your location below'
            : 'Using device location by default'}
        </Text>
      </View>
      {customLocationEnabled && (
        <>
          <TextInput
            style={styles.textInput}
            placeholder="Location Name (e.g. My Farm, Lake Victoria)"
            placeholderTextColor="#888"
            value={customLocation}
            onChangeText={setCustomLocation}
          />
          <View style={{ flexDirection: 'row', marginTop: 8 }}>
            <TextInput
              style={[styles.textInput, { flex: 1, marginRight: 6 }]}
              placeholder="Latitude"
              placeholderTextColor="#888"
              keyboardType="numeric"
              value={customLatitude}
              onChangeText={setCustomLatitude}
            />
            <TextInput
              style={[styles.textInput, { flex: 1, marginLeft: 6 }]}
              placeholder="Longitude"
              placeholderTextColor="#888"
              keyboardType="numeric"
              value={customLongitude}
              onChangeText={setCustomLongitude}
            />
          </View>
        </>
      )}
    </Card>
  );

  const renderSelectStep = () => (
    <>
      <Text style={[styles.sectionTitle, { color: Colors[colorScheme].text }]}>
        Upload Fish Images
      </Text>
      <Text style={[styles.description, { color: colorScheme === 'dark' ? '#e1e1e1' : '#333' }]}>
        Take a photo or select images from your device to detect fish diseases
      </Text>

      <View style={styles.uploadOptions}>
        <Button
          title="Take Photo"
          onPress={takePhoto}
          variant="primary"
          style={styles.uploadButton}
          textStyle={styles.uploadButtonText}
        />
        <Button
          title="Select Images"
          onPress={pickImage}
          variant="outline"
          style={styles.uploadButton}
          textStyle={styles.uploadButtonText}
        />
      </View>

      {images.length > 0 && (
        <>
          <Text style={[styles.imagesTitle, { color: Colors[colorScheme].text }]}>
            Selected Images ({images.length})
          </Text>
          <View style={styles.imageGrid}>
            {images.map((image, index) => (
              <View key={index} style={styles.imageWrapper}>
                <Image source={{ uri: image.uri }} style={styles.thumbnail} />
                <Button
                  title=""
                  onPress={() => removeImage(index)}
                  variant="primary"
                  style={styles.removeButton}
                  textStyle={{ fontSize: 1, opacity: 0 }}
                >
                  <X size={16} color="#fff" />
                </Button>
              </View>
            ))}
          </View>

          <Button
            title="Continue"
            onPress={confirmImages}
            style={styles.continueButton}
          />
        </>
      )}

      <Card style={styles.tipsCard}>
        <Text style={[styles.tipsTitle, { color: Colors[colorScheme].text }]}>
          Tips for Better Results
        </Text>
        <View style={styles.tipItem}>
          <View style={styles.tipBullet} />
          <Text style={styles.tipText}>Ensure good lighting when taking photos</Text>
        </View>
        <View style={styles.tipItem}>
          <View style={styles.tipBullet} />
          <Text style={styles.tipText}>Capture clear images of the fish's body</Text>
        </View>
        <View style={styles.tipItem}>
          <View style={styles.tipBullet} />
          <Text style={styles.tipText}>Include close-ups of any visible symptoms</Text>
        </View>
        <View style={styles.tipItem}>
          <View style={styles.tipBullet} />
          <Text style={styles.tipText}>Take multiple angles for better analysis</Text>
        </View>
      </Card>
    </>
  );

  const renderConfirmStep = () => (
    <>
      <Text style={[styles.sectionTitle, { color: Colors[colorScheme].text }]}>
        Confirm Images
      </Text>
      <Text style={[styles.description, { color: colorScheme === 'dark' ? '#e1e1e1' : '#333' }]}>
        Review your selected images before submission
      </Text>

      <View style={styles.confirmGrid}>
        {images.map((image, index) => (
          <View key={index} style={styles.confirmImageWrapper}>
            <Image source={{ uri: image.uri }} style={styles.confirmImage} />
          </View>
        ))}
      </View>

      {renderLocationSection()}

      <View style={styles.confirmButtons}>
        <Button
          title="Back"
          onPress={() => setStep('select')}
          variant="outline"
          style={styles.confirmButton}
        />
        <Button
          title={uploading ? 'Uploading...' : 'Submit for Analysis'}
          onPress={handleUpload}
          disabled={uploading}
          loading={uploading}
          style={styles.confirmButton}
        />
      </View>
    </>
  );

  const renderResultsStep = () => {
    if (!analysis) return null;

    return (
      <>
        <Card style={styles.resultCard}>
          <View style={styles.resultHeader}>
            <Text style={[styles.resultTitle, { color: Colors[colorScheme].text }]}>
              Analysis Results
            </Text>
            <View
              style={[
                styles.statusBadge,
                {
                  backgroundColor: analysis.isHealthy
                    ? Colors[colorScheme].success
                    : Colors[colorScheme].error,
                  opacity: 0.9
                }
              ]}
            >
              <Text style={styles.statusText}>
                {analysis.isHealthy ? 'Healthy' : 'Disease Detected'}
              </Text>
            </View>
          </View>

          {!analysis.isHealthy && analysis.diseaseType && (
            <>
              <Text style={styles.diseaseType}>{analysis.diseaseType}</Text>
              <View style={styles.divider} />
              <Text style={styles.sectionTitle}>Symptoms:</Text>
              {analysis.symptoms?.map((symptom: string, index: number) => (
                <View key={index} style={styles.bulletPoint}>
                  <View style={styles.bullet} />
                  <Text style={styles.bulletText}>{symptom}</Text>
                </View>
              ))}
              <View style={styles.divider} />
              <Text style={styles.sectionTitle}>Recommended Actions:</Text>
              {analysis.treatments?.map((treatment: string, index: number) => (
                <View key={index} style={styles.bulletPoint}>
                  <View style={styles.bullet} />
                  <Text style={styles.bulletText}>{treatment}</Text>
                </View>
              ))}
            </>
          )}
        </Card>

        <View style={styles.resultActions}>
          <Button
            title={saving ? 'Saving...' : 'Save to Reports'}
            onPress={handleSaveReport}
            disabled={saving}
            style={styles.resultAction}
          />
          <Button
            title="New Analysis"
            onPress={resetUpload}
            variant="outline"
            style={styles.resultAction}
          />
        </View>
      </>
    );
  };

  return (
    <PageContainer>
      <HeaderBar
        title="Disease Detection"
        subtitle={
          step === 'select'
            ? 'Upload fish images for analysis'
            : step === 'confirm'
            ? 'Confirm your images'
            : 'View analysis results'
        }
      />

      {step === 'select' && renderSelectStep()}
      {step === 'confirm' && renderConfirmStep()}
      {step === 'results' && renderResultsStep()}
    </PageContainer>
  );
}

const styles = StyleSheet.create({
  sectionTitle: {
    fontFamily: 'Inter-Bold',
    fontSize: 20,
    marginBottom: 8,
  },
  customLocationContainer: {
    marginTop: 24,
    marginBottom: 12,
    paddingHorizontal: 10,
    paddingVertical: 12,
    backgroundColor: '#f8f8f8',
    borderRadius: 10,
  },
  textInput: {
    borderWidth: 1,
    borderColor: '#ccc',
    borderRadius: 10,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 16,
    backgroundColor: '#fff',
    color: '#000',
    marginBottom: 6,
  },
  description: {
    fontFamily: 'Inter-Regular',
    fontSize: 16,
    marginBottom: 24,
  },
  uploadOptions: {
    flexDirection: 'row',
    marginBottom: 24,
  },
  uploadButton: {
    flex: 1,
    marginHorizontal: 8,
    paddingVertical: 14,
  },
  uploadButtonText: {
    fontFamily: 'Inter-Medium',
  },
  imagesTitle: {
    fontFamily: 'Inter-Medium',
    fontSize: 16,
    marginBottom: 12,
  },
  imageGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginBottom: 24,
  },
  imageWrapper: {
    width: '30%',
    aspectRatio: 1,
    margin: '1.66%',
    borderRadius: 8,
    overflow: 'hidden',
    position: 'relative',
  },
  thumbnail: {
    width: '100%',
    height: '100%',
  },
  removeButton: {
    position: 'absolute',
    top: 4,
    right: 4,
    width: 24,
    height: 24,
    padding: 0,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 12,
  },
  continueButton: {
    marginBottom: 24,
  },
  tipsCard: {
    marginBottom: 24,
  },
  tipsTitle: {
    fontFamily: 'Inter-Bold',
    fontSize: 16,
    marginBottom: 12,
  },
  tipItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  tipBullet: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#38ada9',
    marginRight: 8,
  },
  tipText: {
    fontFamily: 'Inter-Regular',
    fontSize: 14,
  },
  confirmGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginBottom: 24,
  },
  confirmImageWrapper: {
    width: '48%',
    aspectRatio: 1,
    margin: '1%',
    borderRadius: 8,
    overflow: 'hidden',
  },
  confirmImage: {
    width: '100%',
    height: '100%',
  },
  confirmButtons: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 24,
  },
  confirmButton: {
    flex: 0.48,
  },
  resultCard: {
    marginVertical: 16,
  },
  resultHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  resultTitle: {
    fontFamily: 'Inter-Bold',
    fontSize: 18,
    marginBottom: 8,
    color: '#333',
  },
  statusBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
  },
  statusText: {
    color: '#fff',
    fontFamily: 'Inter-Medium',
    fontSize: 14,
    marginLeft: 6,
  },
  diseaseType: {
    fontFamily: 'Inter-Bold',
    fontSize: 18,
    marginBottom: 8,
    color: '#333',
  },
  divider: {
    height: 1,
    backgroundColor: '#e1e1e1',
    marginVertical: 16,
  },
  bulletPoint: {
    flexDirection: 'row',
    marginBottom: 8,
  },
  bullet: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#38ada9',
    marginRight: 8,
    marginTop: 6,
  },
  bulletText: {
    fontFamily: 'Inter-Regular',
    fontSize: 14,
    lineHeight: 20,
    flex: 1,
    color: '#555',
  },
  resultActions: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 8,
    marginBottom: 24,
  },
  resultAction: {
    flex: 0.48,
  },
});