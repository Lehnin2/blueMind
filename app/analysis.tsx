import { useState } from 'react';
import { StyleSheet, View, Text, Alert } from 'react-native';
import { useAuthStore } from '@/services/auth';
import { useReports } from '@/services/reports';
import PageContainer from '@/components/PageContainer';
import Button from '@/components/Button';
import Colors from '@/constants/Colors';
import { useColorScheme } from '@/hooks/useColorScheme';

export default function AnalysisScreen({ route }: { route: { params: { analysis: any } } }) {
  const colorScheme = useColorScheme();
  const { user } = useAuthStore();
  const { createReport } = useReports();
  const [saving, setSaving] = useState(false);
  
  const { analysis } = route.params;

  const handleSaveReport = async () => {
    if (!user?.id) {
      Alert.alert('Error', 'You must be logged in to save reports');
      return;
    }

    try {
      setSaving(true);
      await createReport({
        user_id: user.id,
        title: `Analysis Report - ${new Date().toLocaleDateString()}`,
        description: `Analysis Results:\n\n${JSON.stringify(analysis, null, 2)}`,
        status: 'pending'
      });
      Alert.alert('Success', 'Report saved successfully');
    } catch (error) {
      console.error('Failed to save report:', error);
      Alert.alert('Error', 'Failed to save report. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <PageContainer>
      <View style={styles.container}>
        <Text style={[styles.title, { color: Colors[colorScheme].text }]}>
          Analysis Results
        </Text>

        <View style={styles.resultContainer}>
          <Text style={[styles.resultText, { color: Colors[colorScheme].text }]}>
            {JSON.stringify(analysis, null, 2)}
          </Text>
        </View>

        <Button
          title={saving ? 'Saving...' : 'Save to Reports'}
          onPress={handleSaveReport}
          disabled={saving}
          style={styles.saveButton}
        />
      </View>
    </PageContainer>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 20,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 20,
  },
  resultContainer: {
    flex: 1,
    backgroundColor: '#f5f5f5',
    borderRadius: 8,
    padding: 16,
    marginBottom: 20,
  },
  resultText: {
    fontSize: 16,
  },
  saveButton: {
    marginTop: 'auto',
  },
}); 