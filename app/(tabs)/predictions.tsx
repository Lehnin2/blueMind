import { useState } from 'react';
import { StyleSheet, Text, View, Image, TouchableOpacity } from 'react-native';
import { Search } from 'lucide-react-native';
import PageContainer from '@/components/PageContainer';
import HeaderBar from '@/components/HeaderBar';
import Card from '@/components/Card';
import Colors from '@/constants/Colors';
import { useColorScheme } from '@/hooks/useColorScheme';

// First, let's define the Disease interface
interface Disease {
  id: string;
  name: string;
  description: string;
  symptoms: string[];
  causes: string[];
  treatments: string[];
  imageUrl: string;
}

// Disease data
const diseases: Disease[] = [
  {
    id: '1',
    name: 'Bacterial Red disease',
    description: 'A bacterial infection that causes red lesions and inflammation on the fish body.',
    symptoms: ['Red lesions', 'Inflammation', 'Loss of appetite', 'Lethargy'],
    causes: ['Aeromonas bacteria', 'Poor water quality', 'Stress', 'Overcrowding'],
    treatments: ['Antibiotics', 'Water quality improvement', 'Salt baths', 'Isolation of affected fish'],
    imageUrl: 'https://images.pexels.com/photos/9432979/pexels-photo-9432979.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=2',
  },
  {
    id: '2',
    name: 'Bacterial diseases - Aeromoniasis',
    description: 'A common bacterial infection affecting freshwater fish, characterized by ulcers and fin rot.',
    symptoms: ['Ulcers', 'Fin rot', 'Skin lesions', 'Bloody patches'],
    causes: ['Aeromonas bacteria', 'Poor water quality', 'Physical injury', 'Stress'],
    treatments: ['Antibiotics', 'Clean water', 'Salt treatment', 'Increase oxygenation'],
    imageUrl: 'https://images.pexels.com/photos/128756/pexels-photo-128756.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=2',
  },
  {
    id: '3',
    name: 'Bacterial gill disease',
    description: 'Affects the gills, making breathing difficult for fish. Common in crowded conditions.',
    symptoms: ['Gasping at surface', 'Rapid gill movement', 'Swollen gills', 'Loss of appetite'],
    causes: ['Flavobacterium bacteria', 'Poor water quality', 'High ammonia levels', 'Stress'],
    treatments: ['Antibiotics', 'Improve water circulation', 'Reduce stocking density', 'Clean water'],
    imageUrl: 'https://images.pexels.com/photos/3439545/pexels-photo-3439545.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=2',
  },
  {
    id: '4',
    name: 'Fungal diseases Saprolegniasis',
    description: 'A fungal infection characterized by cotton-like growths on fish skin, fins, and gills.',
    symptoms: ['Cotton-like growths', 'Discolored patches', 'Lethargic behavior', 'Loss of appetite'],
    causes: ['Saprolegnia fungi', 'Poor water quality', 'Physical injury', 'Stress'],
    treatments: ['Antifungal treatments', 'Salt baths', 'Clean water', 'Remove necrotic tissue'],
    imageUrl: 'https://images.pexels.com/photos/7659004/pexels-photo-7659004.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=2',
  },
  {
    id: '5',
    name: 'Parasitic diseases',
    description: 'Various parasites that can infect fish, causing irritation, tissue damage, and secondary infections.',
    symptoms: ['Scratching against objects', 'Visible parasites', 'Erratic swimming', 'White spots'],
    causes: ['Various parasites', 'Introduction of infected fish', 'Poor water quality', 'Overcrowding'],
    treatments: ['Anti-parasitic medications', 'Salt treatments', 'Clean water', 'Quarantine new fish'],
    imageUrl: 'https://images.pexels.com/photos/923360/pexels-photo-923360.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=2',
  },
  {
    id: '6',
    name: 'Viral diseases White tail disease',
    description: 'A viral infection that affects the tail and fins, causing whitening and deterioration.',
    symptoms: ['White tail', 'Fin deterioration', 'Loss of color', 'Lethargy'],
    causes: ['Viral infection', 'Stress', 'Poor immune system', 'Environmental factors'],
    treatments: ['No specific treatment', 'Improve water quality', 'Boost immune system', 'Isolation'],
    imageUrl: 'https://images.pexels.com/photos/2156311/pexels-photo-2156311.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=2',
  },
];

export default function PredictionsScreen() {
  const colorScheme = useColorScheme();
  const [selectedDisease, setSelectedDisease] = useState<Disease | null>(null);
  
  const renderDiseaseList = () => (
    <>
      <Text style={[styles.sectionTitle, { color: Colors[colorScheme].text }]}>
        Disease Database
      </Text>
      <Text style={[styles.description, { color: colorScheme === 'dark' ? '#e1e1e1' : '#333' }]}>
        Learn about common fish diseases, their symptoms, causes, and treatments
      </Text>
      
      <View style={styles.searchContainer}>
        <Search size={20} color="#8f9bb3" />
        <Text style={styles.searchPlaceholder}>Search diseases (coming soon)</Text>
      </View>
      
      <View style={styles.diseaseGrid}>
        {diseases.map((disease) => (
          <TouchableOpacity
            key={disease.id}
            style={styles.diseaseCard}
            onPress={() => setSelectedDisease(disease)}
            activeOpacity={0.8}
          >
            <Image source={{ uri: disease.imageUrl }} style={styles.diseaseImage} />
            <View style={styles.diseaseCardOverlay}>
              <Text style={styles.diseaseCardTitle}>{disease.name}</Text>
            </View>
          </TouchableOpacity>
        ))}
      </View>
      
      <Card style={styles.resourcesCard}>
        <Text style={styles.resourcesTitle}>Additional Resources</Text>
        <Text style={styles.resourcesText}>
          For more detailed information about fish diseases, prevention, and treatment, consult with a veterinarian specializing in aquatic health or visit reputable aquaculture research centers online.
        </Text>
      </Card>
    </>
  );

  const renderDiseaseDetail = () => {
    if (!selectedDisease) return null;
    
    return (
      <>
        <TouchableOpacity
          onPress={() => setSelectedDisease(null)}
          style={styles.backButton}
          activeOpacity={0.7}
        >
          <Text style={[styles.backButtonText, { color: Colors[colorScheme].primary }]}>
            ← Back to Diseases
          </Text>
        </TouchableOpacity>
        
        <View style={styles.diseaseDetailHeader}>
          <Text style={[styles.diseaseDetailTitle, { color: Colors[colorScheme].text }]}>
            {selectedDisease.name}
          </Text>
        </View>
        
        <View style={styles.diseaseImageContainer}>
          <Image 
            source={{ uri: selectedDisease.imageUrl }} 
            style={styles.diseaseDetailImage}
            resizeMode="cover"
          />
        </View>
        
        <Card style={styles.diseaseInfoCard}>
          <Text style={styles.diseaseInfoTitle}>Description</Text>
          <Text style={styles.diseaseInfoText}>{selectedDisease.description}</Text>
          
          <View style={styles.divider} />
          
          <Text style={styles.diseaseInfoTitle}>Symptoms</Text>
          {selectedDisease.symptoms.map((symptom, index) => (
            <View key={index} style={styles.bulletPoint}>
              <View style={styles.bullet} />
              <Text style={styles.bulletText}>{symptom}</Text>
            </View>
          ))}
          
          <View style={styles.divider} />
          
          <Text style={styles.diseaseInfoTitle}>Causes</Text>
          {selectedDisease.causes.map((cause, index) => (
            <View key={index} style={styles.bulletPoint}>
              <View style={styles.bullet} />
              <Text style={styles.bulletText}>{cause}</Text>
            </View>
          ))}
          
          <View style={styles.divider} />
          
          <Text style={styles.diseaseInfoTitle}>Treatments</Text>
          {selectedDisease.treatments.map((treatment, index) => (
            <View key={index} style={styles.bulletPoint}>
              <View style={styles.bullet} />
              <Text style={styles.bulletText}>{treatment}</Text>
            </View>
          ))}
        </Card>
        
        <Card style={styles.preventionCard}>
          <Text style={styles.preventionTitle}>Prevention Tips</Text>
          <View style={styles.bulletPoint}>
            <View style={styles.bullet} />
            <Text style={styles.bulletText}>Maintain optimal water temperature and quality</Text>
          </View>
          <View style={styles.bulletPoint}>
            <View style={styles.bullet} />
            <Text style={styles.bulletText}>Avoid overcrowding in fish tanks or ponds</Text>
          </View>
          <View style={styles.bulletPoint}>
            <View style={styles.bullet} />
            <Text style={styles.bulletText}>Quarantine new fish before adding to main population</Text>
          </View>
          <View style={styles.bulletPoint}>
            <View style={styles.bullet} />
            <Text style={styles.bulletText}>Provide balanced nutrition and reduce stress factors</Text>
          </View>
        </Card>
      </>
    );
  };

  return (
    <PageContainer>
      <HeaderBar 
        title="Disease Information"
        subtitle={
          selectedDisease 
            ? selectedDisease.name 
            : "Learn about fish diseases"
        }
      />
      
      {selectedDisease ? renderDiseaseDetail() : renderDiseaseList()}
    </PageContainer>
  );
}

const styles = StyleSheet.create({
  sectionTitle: {
    fontFamily: 'Inter-Bold',
    fontSize: 20,
    marginBottom: 8,
  },
  description: {
    fontFamily: 'Inter-Regular',
    fontSize: 16,
    marginBottom: 24,
  },
  searchContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#f5f5f5',
    borderRadius: 8,
    padding: 12,
    marginBottom: 24,
  },
  searchPlaceholder: {
    fontFamily: 'Inter-Regular',
    fontSize: 14,
    color: '#8f9bb3',
    marginLeft: 8,
  },
  diseaseGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    marginBottom: 24,
  },
  diseaseCard: {
    width: '48%',
    height: 120,
    borderRadius: 12,
    overflow: 'hidden',
    marginBottom: 16,
    position: 'relative',
  },
  diseaseImage: {
    width: '100%',
    height: '100%',
  },
  diseaseCardOverlay: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    padding: 12,
    backgroundColor: 'rgba(0, 0, 0, 0.6)',
  },
  diseaseCardTitle: {
    fontFamily: 'Inter-Medium',
    fontSize: 12,
    color: '#fff',
  },
  resourcesCard: {
    marginBottom: 24,
  },
  resourcesTitle: {
    fontFamily: 'Inter-Bold',
    fontSize: 16,
    color: '#333',
    marginBottom: 8,
  },
  resourcesText: {
    fontFamily: 'Inter-Regular',
    fontSize: 14,
    lineHeight: 22,
    color: '#555',
  },
  backButton: {
    marginBottom: 16,
  },
  backButtonText: {
    fontFamily: 'Inter-Medium',
    fontSize: 16,
  },
  diseaseDetailHeader: {
    marginBottom: 16,
  },
  diseaseDetailTitle: {
    fontFamily: 'Inter-Bold',
    fontSize: 22,
    marginBottom: 4,
  },
  diseaseImageContainer: {
    height: 200,
    borderRadius: 12,
    overflow: 'hidden',
    marginBottom: 16,
  },
  diseaseDetailImage: {
    width: '100%',
    height: '100%',
  },
  diseaseInfoCard: {
    marginBottom: 16,
  },
  diseaseInfoTitle: {
    fontFamily: 'Inter-Bold',
    fontSize: 16,
    color: '#333',
    marginBottom: 8,
  },
  diseaseInfoText: {
    fontFamily: 'Inter-Regular',
    fontSize: 14,
    lineHeight: 22,
    color: '#555',
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
  preventionCard: {
    marginBottom: 24,
  },
  preventionTitle: {
    fontFamily: 'Inter-Bold',
    fontSize: 16,
    color: '#333',
    marginBottom: 8,
  },
});