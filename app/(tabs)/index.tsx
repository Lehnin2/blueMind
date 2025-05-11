import React from 'react';
import { useState, useEffect } from 'react';
import { StyleSheet, Text, View, Image, Platform, TouchableOpacity, ActivityIndicator } from 'react-native';
import { Link, router } from 'expo-router';
import { Fish, Upload, Map, FileText, Info } from 'lucide-react-native';
import PageContainer from '@/components/PageContainer';
import HeaderBar from '@/components/HeaderBar';
import Card from '@/components/Card';
import Button from '@/components/Button';
import Colors from '@/constants/Colors';
import { useColorScheme } from '@/hooks/useColorScheme';
import { useAuthStore } from '@/services/auth';
import { useReports } from '@/services/reports';

export default function HomeScreen() {
  const colorScheme = useColorScheme();
  const { user, logout } = useAuthStore();
  const { getReports } = useReports();
  const [stats, setStats] = useState({
    detectionsMade: 0,
    healthyFish: 0,
    sickFish: 0,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStats();
  }, [user?.id]);

  const loadStats = async () => {
    try {
      setLoading(true);
      if (!user?.id) return;

      const userReports = await getReports(user.id);
      const totalReports = userReports.length;
      const healthyCount = userReports.filter(report => report.status === 'resolved').length;
      const sickCount = userReports.filter(report => report.status === 'pending').length;

      setStats({
        detectionsMade: totalReports,
        healthyFish: healthyCount,
        sickFish: sickCount,
      });
    } catch (error) {
      console.error('Failed to load stats:', error);
    } finally {
      setLoading(false);
    }
  };

  const features = [
    {
      icon: <Upload size={24} color={Colors[colorScheme].primary} />,
      title: 'Upload Images',
      description: 'Submit fish photos for disease detection',
      route: '/upload',
    },
    {
      icon: <Map size={24} color={Colors[colorScheme].primary} />,
      title: 'Disease Map',
      description: 'View disease occurrence by location',
      route: '/map',
    },
    {
      icon: <FileText size={24} color={Colors[colorScheme].primary} />,
      title: 'Reports',
      description: 'Access your previous detection reports',
      route: '/reports',
    },
    {
      icon: <Info size={24} color={Colors[colorScheme].primary} />,
      title: 'Disease Database',
      description: 'Learn about common fish diseases',
      route: '/predictions',
    },
  ];

  const handleLogout = async () => {
    try {
      await logout();
      router.replace('/login');
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  return (
    <PageContainer>
      <HeaderBar 
        title="EcoPêche"
        subtitle="Fish Disease Detection"
      />
      
      <View style={styles.heroContainer}>
        <Image
          source={{ uri: 'https://images.pexels.com/photos/1321068/pexels-photo-1321068.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=2' }}
          style={styles.heroImage}
          resizeMode="cover"
        />
        <View style={styles.heroOverlay}>
          <Text style={styles.heroTitle}>Protect Your Fish</Text>
          <Text style={styles.heroSubtitle}>
            Detect and identify fish diseases instantly with AI-powered analysis
          </Text>
          <Link href="/upload" asChild>
            <Button 
              title="Upload Image" 
              onPress={() => {}}
              size="large"
              style={styles.heroButton}
            />
          </Link>
        </View>
      </View>

      <View style={styles.statsContainer}>
        {loading ? (
          <ActivityIndicator size="large" color={Colors[colorScheme].primary} />
        ) : (
          <>
            <Card style={styles.statCard}>
              <Fish size={24} color={Colors[colorScheme].primary} />
              <Text style={styles.statCount}>{stats.detectionsMade}</Text>
              <Text style={styles.statLabel}>Total Detections</Text>
            </Card>
            
            <Card style={styles.statCard}>
              <View style={[styles.statusIndicator, { backgroundColor: Colors[colorScheme].success }]} />
              <Text style={styles.statCount}>{stats.healthyFish}</Text>
              <Text style={styles.statLabel}>Healthy Fish</Text>
            </Card>
            
            <Card style={styles.statCard}>
              <View style={[styles.statusIndicator, { backgroundColor: Colors[colorScheme].error }]} />
              <Text style={styles.statCount}>{stats.sickFish}</Text>
              <Text style={styles.statLabel}>Diseased Fish</Text>
            </Card>
          </>
        )}
      </View>

      <Text style={[styles.sectionTitle, { color: Colors[colorScheme].text }]}>
        Features
      </Text>

      <View style={styles.featuresContainer}>
        {features.map((feature, index) => (
          <Link key={index} href={feature.route} asChild>
            <Button
              onPress={() => {}}
              variant="outline"
              style={styles.featureButton}
              textStyle={styles.featureButtonText}
              title={
                Platform.OS === 'web' ? feature.title : ''  // Show title only on web
              }
            >
              <View style={styles.featureContent}>
                <View style={styles.featureIcon}>{feature.icon}</View>
                <View>
                  <Text style={[styles.featureTitle, { color: Colors[colorScheme].primary }]}>
                    {feature.title}
                  </Text>
                  <Text style={[styles.featureDescription, { color: Colors[colorScheme === 'dark' ? 'light' : 'dark'].text }]}>
                    {feature.description}
                  </Text>
                </View>
              </View>
            </Button>
          </Link>
        ))}
      </View>

      <Card style={styles.infoCard}>
        <Text style={[styles.infoTitle, { color: Colors[colorScheme].text }]}>
          How It Works
        </Text>
        <Text style={[styles.infoText, { color: colorScheme === 'dark' ? '#e1e1e1' : '#333' }]}>
          Our app uses advanced AI to detect fish diseases from images. Upload photos of your fish, and our system will analyze them to determine if they're healthy or identify any diseases present.
        </Text>
      </Card>

      <View style={styles.logoutContainer}>
        <Text style={[styles.logoutTitle, { color: Colors[colorScheme].text }]}>
          Welcome, {user?.name || 'User'}!
        </Text>
        
        <TouchableOpacity
          style={[styles.logoutButton, { backgroundColor: Colors[colorScheme].primary }]}
          onPress={handleLogout}
        >
          <Text style={styles.logoutButtonText}>Logout</Text>
        </TouchableOpacity>
      </View>
    </PageContainer>
  );
}

const styles = StyleSheet.create({
  heroContainer: {
    height: 220,
    borderRadius: 16,
    overflow: 'hidden',
    marginBottom: 24,
    position: 'relative',
  },
  heroImage: {
    width: '100%',
    height: '100%',
  },
  heroOverlay: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    padding: 16,
    backgroundColor: 'rgba(7, 26, 47, 0.7)',
  },
  heroTitle: {
    fontFamily: 'Inter-Bold',
    fontSize: 24,
    color: '#fff',
    marginBottom: 8,
  },
  heroSubtitle: {
    fontFamily: 'Inter-Regular',
    fontSize: 14,
    color: '#fff',
    marginBottom: 16,
    opacity: 0.9,
  },
  heroButton: {
    alignSelf: 'flex-start',
  },
  statsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 24,
  },
  statCard: {
    flex: 1,
    marginHorizontal: 4,
    alignItems: 'center',
    paddingVertical: 12,
  },
  statCount: {
    fontFamily: 'Inter-Bold',
    fontSize: 20,
    marginVertical: 4,
  },
  statLabel: {
    fontFamily: 'Inter-Regular',
    fontSize: 12,
    color: '#8f9bb3',
  },
  statusIndicator: {
    width: 10,
    height: 10,
    borderRadius: 5,
  },
  sectionTitle: {
    fontFamily: 'Inter-Bold',
    fontSize: 20,
    marginBottom: 16,
  },
  featuresContainer: {
    marginBottom: 24,
  },
  featureButton: {
    alignItems: 'flex-start',
    marginBottom: 12,
    paddingVertical: 16,
  },
  featureButtonText: {
    fontSize: 1,  // Use minimum font size instead of 0 to avoid Android errors
    opacity: 0,   // Hide text by making it transparent instead
  },
  featureContent: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  featureIcon: {
    marginRight: 16,
  },
  featureTitle: {
    fontFamily: 'Inter-Medium',
    fontSize: 16,
    marginBottom: 4,
  },
  featureDescription: {
    fontFamily: 'Inter-Regular',
    fontSize: 14,
  },
  infoCard: {
    marginBottom: 32,
  },
  infoTitle: {
    fontFamily: 'Inter-Bold',
    fontSize: 18,
    marginBottom: 8,
  },
  infoText: {
    fontFamily: 'Inter-Regular',
    fontSize: 14,
    lineHeight: 22,
  },
  logoutContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
  },
  logoutTitle: {
    fontFamily: 'Inter-Bold',
    fontSize: 18,
  },
  logoutButton: {
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 8,
  },
  logoutButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
});