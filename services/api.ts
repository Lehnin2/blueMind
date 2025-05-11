import axios from 'axios';
import * as FileSystem from 'expo-file-system';
import { Platform } from 'react-native';

// Replace with your actual Flask backend URL
// In development, use your local machine's IP address or ngrok URL
// In production, use your deployed API endpoint
const API_URL = 'http://192.168.1.18:5000/api';

// Create axios instance with base URL and common headers
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Type definitions
export type DiseaseDetectionResult = {
  isHealthy: boolean;
  diseaseType?: string;
  confidence: number;
  description?: string;
  symptoms?: string[];
  causes?: string[];
  treatments?: string[];
  error?: string;
};

export type UploadResponse = {
  id: string;
  results: DiseaseDetectionResult[];
};

// API functions
export const uploadImages = async (images: { uri: string }[]): Promise<DiseaseDetectionResult[]> => {
  try {
    console.log('Starting image upload process with API URL:', API_URL);
    console.log('Number of images to process:', images.length);
    
    const results: DiseaseDetectionResult[] = [];
    
    // Process each image
    for (const image of images) {
      let result: DiseaseDetectionResult;
      
      try {
        console.log('Processing image with URI:', image.uri.substring(0, 30) + '...');
        
        // Get the base64 data of the image
        console.log('Converting image to base64...');
        const base64 = await getBase64FromUri(image.uri);
        console.log('Base64 conversion successful, length:', base64.length);
        
        // Send to API
        console.log('Sending POST request to:', `${API_URL}/predict`);
        const response = await api.post('/predict', {
          imageBase64: base64
        });
        
        console.log('API response received:', JSON.stringify(response.status));
        
        // Parse response
        result = response.data;
        console.log('Parsed result:', JSON.stringify(result));
      } catch (error: any) {
        console.error('Error processing individual image:', error);
        console.error('Error details:', error.message);
        if (error.response) {
          console.error('Response status:', error.response.status);
          console.error('Response data:', JSON.stringify(error.response.data));
        }
        // Generate fallback result with error
        result = generateFallbackResult(error);
      }
      
      results.push(result);
    }
    
    return results;
    
  } catch (error) {
    console.error('Error uploading images:', error);
    return [generateFallbackResult(error)];
  }
};

// Helper function to convert image URI to base64
const getBase64FromUri = async (uri: string): Promise<string> => {
  try {
    console.log('Getting base64 from URI:', uri.substring(0, 30) + '...');
    console.log('URI type:', typeof uri);
    console.log('Platform:', Platform.OS);
    
    // For web platform
    if (Platform.OS === 'web') {
      console.log('Using web platform method');
      return await fetchImageAsBase64(uri);
    }
    
    // Check if URI is already a base64 data URI
    if (uri.startsWith('data:image')) {
      console.log('URI is already in base64 format');
      return uri;
    }
    
    // For native platforms
    try {
      console.log('Using Expo FileSystem to read image');
      // Check if the file exists first
      if (uri.startsWith('file://')) {
        const fileInfo = await FileSystem.getInfoAsync(uri);
        console.log('File exists:', fileInfo.exists);
        if (fileInfo.exists) {
          console.log('File size:', (fileInfo as any).size);
        }
        if (!fileInfo.exists) {
          throw new Error(`File does not exist at path: ${uri}`);
        }
      }
      
      // Use Expo FileSystem to read the image
      const base64 = await FileSystem.readAsStringAsync(uri, {
        encoding: FileSystem.EncodingType.Base64,
      });
      
      console.log('Successfully read file, base64 length:', base64.length);
      return `data:image/jpeg;base64,${base64}`;
    } catch (fsError: any) {
      console.error('FileSystem error details:', fsError.message);
      console.log('Trying alternative method for URI:', uri.substring(0, 30) + '...');
      
      // Alternative method using fetch for content:// URIs
      if (uri.startsWith('content://')) {
        console.log('Using fetch method for content:// URI');
        return await fetchImageAsBase64(uri);
      }
      
      throw fsError;
    }
  } catch (error: any) {
    console.error('Error converting image to base64:', error);
    console.error('Error message:', error.message);
    console.error('URI that caused error (partial):', uri.substring(0, 30) + '...');
    throw error;
  }
};

// Fetch image as base64 for web platform
const fetchImageAsBase64 = async (url: string): Promise<string> => {
  console.log('fetchImageAsBase64 called with URL:', url.substring(0, 30) + '...');
  try {
    console.log('Fetching image data...');
    const response = await fetch(url);
    
    if (!response.ok) {
      throw new Error(`Fetch failed with status: ${response.status}`);
    }
    
    console.log('Response received, converting to blob...');
    const blob = await response.blob();
    console.log('Blob created, size:', blob.size);
    
    return new Promise((resolve, reject) => {
      console.log('Setting up FileReader...');
      const reader = new FileReader();
      reader.onload = () => {
        console.log('FileReader loaded successfully');
        const result = reader.result as string;
        console.log('Result length:', result.length);
        resolve(result);
      };
      reader.onerror = (error) => {
        console.error('FileReader error:', error);
        reject(error);
      };
      console.log('Starting to read as DataURL...');
      reader.readAsDataURL(blob);
    });
  } catch (error) {
    console.error('Error in fetchImageAsBase64:', error);
    throw error;
  }
};

// Generate a fallback result in case of API failure
const generateFallbackResult = (error: any): DiseaseDetectionResult => {
  return {
    isHealthy: false,
    diseaseType: 'Unknown',
    confidence: 0.5,
    description: 'Unable to determine disease due to API error',
    symptoms: ['API connection error'],
    causes: ['Network issue', 'Server error', 'Invalid image format'],
    treatments: ['Try again with a clearer image', 'Check internet connection'],
    error: error?.message || 'Unknown error occurred'
  };
};

export const getDetectionHistory = async (): Promise<UploadResponse[]> => {
  try {
    const response = await api.get('/history');
    return response.data;
  } catch (error) {
    console.error('Error fetching detection history:', error);
    throw error;
  }
};

export const getDiseaseInfo = async (diseaseType: string): Promise<DiseaseDetectionResult> => {
  try {
    const response = await api.get(`/disease/${encodeURIComponent(diseaseType)}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching disease info:', error);
    throw error;
  }
};

// Check if the API is available (for status checks)
export const checkApiStatus = async (): Promise<boolean> => {
  try {
    const response = await api.get('/healthcheck');
    return response.data.status === 'healthy';
  } catch (error) {
    console.error('API health check failed:', error);
    return false;
  }
};

export default api;