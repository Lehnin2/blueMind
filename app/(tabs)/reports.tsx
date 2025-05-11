import React from 'react';
import { useState, useEffect } from 'react';
import { StyleSheet, Text, View, Image, TouchableOpacity, ScrollView, FlatList, ActivityIndicator } from 'react-native';
import { ChevronRight } from 'lucide-react-native';
import PageContainer from '@/components/PageContainer';
import HeaderBar from '@/components/HeaderBar';
import Card from '@/components/Card';
import Button from '@/components/Button';
import Colors from '@/constants/Colors';
import { useColorScheme } from '@/hooks/useColorScheme';
import { useAuthStore } from '@/services/auth';
import { useReports } from '@/services/reports';

type Report = {
  id: string;
  date: string;
  imageUrl: string;
  isHealthy: boolean;
  diseaseType?: string;
  notes?: string;
};

export default function ReportsScreen() {
  const colorScheme = useColorScheme();
  const { user } = useAuthStore();
  const { getReports } = useReports();
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedReport, setSelectedReport] = useState<Report | null>(null);
  
  useEffect(() => {
    loadReports();
  }, [user?.id]);

  const loadReports = async () => {
    try {
      setLoading(true);
      setError(null);
      
      if (!user?.id) {
        setError('You must be logged in to view reports');
        return;
      }
      
      const userReports = await getReports(user.id);
      // Transform the database reports to match your existing Report type
      const transformedReports = userReports.map(report => ({
        id: report.id,
        date: new Date(report.created_at).toLocaleDateString(),
        imageUrl: report.image_url || 'https://images.pexels.com/photos/128756/pexels-photo-128756.jpeg',
        isHealthy: report.status === 'resolved',
        diseaseType: report.disease_type,
        notes: report.description
      }));
      setReports(transformedReports);
    } catch (error) {
      console.error('Failed to load reports:', error);
      setError('Failed to load reports. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const renderReportList = () => {
    if (error) {
      return (
        <View style={styles.errorContainer}>
          <Text style={[styles.errorText, { color: 'white' }]}>
            {error}
          </Text>
          <Button
            title="Retry"
            onPress={loadReports}
            variant="primary"
          />
        </View>
      );
    }

    if (reports.length === 0) {
      return (
        <View style={styles.emptyContainer}>
          <Text style={[styles.emptyText, { color: 'white' }]}>
            No reports found. Upload some images to get started!
          </Text>
        </View>
      );
    }

    return (
      <>
        <Text style={[styles.sectionTitle, { color: 'white' }]}>
          Your Detection Reports
        </Text>
        
        {reports.map((report) => (
          <TouchableOpacity
            key={report.id}
            onPress={() => setSelectedReport(report)}
            activeOpacity={0.7}
          >
            <Card style={styles.reportCard}>
              <View style={styles.reportContent}>
                <Image source={{ uri: report.imageUrl }} style={styles.reportImage} />
                <View style={styles.reportDetails}>
                  <Text style={[styles.reportDate, { color: 'white' }]}>{report.date}</Text>
                  <View 
                    style={[styles.statusBadge, { 
                      backgroundColor: report.isHealthy 
                        ? Colors[colorScheme].success 
                        : Colors[colorScheme].error,
                      opacity: 0.9 
                    }]}
                  >
                    <Text style={styles.statusText}>
                      {report.isHealthy ? 'Healthy' : 'Disease Detected'}
                    </Text>
                  </View>
                  {!report.isHealthy && report.diseaseType && (
                    <Text style={[styles.diseaseType, { color: 'white' }]}>
                      {report.diseaseType}
                    </Text>
                  )}
                </View>
                <ChevronRight size={20} color="#8f9bb3" />
              </View>
            </Card>
          </TouchableOpacity>
        ))}
      </>
    );
  };

  const renderReportDetail = () => {
    if (!selectedReport) return null;
    
    return (
      <>
        <TouchableOpacity
          onPress={() => setSelectedReport(null)}
          style={styles.backButton}
          activeOpacity={0.7}
        >
          <Text style={[styles.backButtonText, { color: Colors[colorScheme].primary }]}>
            ← Back to Reports
          </Text>
        </TouchableOpacity>
        
        <View style={styles.reportDetailHeader}>
          <Text style={[styles.reportDetailTitle, { color: 'white' }]}>
            Report Detail
          </Text>
          <Text style={[styles.reportDetailDate, { color: 'white' }]}>{selectedReport.date}</Text>
        </View>
        
        <View style={styles.imageContainer}>
          <Image 
            source={{ uri: selectedReport.imageUrl }} 
            style={styles.detailImage}
            resizeMode="cover"
          />
        </View>
        
        <Card style={styles.resultCard}>
          <View 
            style={[styles.resultBadge, { 
              backgroundColor: selectedReport.isHealthy 
                ? Colors[colorScheme].success 
                : Colors[colorScheme].error 
            }]}
          >
            <Text style={styles.resultBadgeText}>
              {selectedReport.isHealthy ? 'Healthy Fish' : 'Disease Detected'}
            </Text>
          </View>
          
          {!selectedReport.isHealthy && selectedReport.diseaseType && (
            <>
              <Text style={[styles.resultDisease, { color: 'white' }]}>
                {selectedReport.diseaseType}
              </Text>
              <View style={styles.divider} />
              <Text style={[styles.diseaseSectionTitle, { color: 'white' }]}>About This Disease:</Text>
              <Text style={[styles.diseaseDescription, { color: 'white' }]}>
                {selectedReport.diseaseType === 'Bacterial Red disease' ? 
                  'A bacterial infection that causes red lesions and inflammation on the fish body. It spreads quickly in warm water conditions and can be fatal if left untreated.' :
                  'A fungal infection characterized by cotton-like growths on the fish body and fins. It typically affects fish with compromised immune systems or previous injuries.'}
              </Text>
              
              <View style={styles.divider} />
              <Text style={[styles.diseaseSectionTitle, { color: 'white' }]}>Recommended Actions:</Text>
              <View style={styles.bulletPoint}>
                <View style={styles.bullet} />
                <Text style={[styles.bulletText, { color: 'white' }]}>Isolate affected fish immediately</Text>
              </View>
              <View style={styles.bulletPoint}>
                <View style={styles.bullet} />
                <Text style={[styles.bulletText, { color: 'white' }]}>Improve water quality and circulation</Text>
              </View>
              <View style={styles.bulletPoint}>
                <View style={styles.bullet} />
                <Text style={[styles.bulletText, { color: 'white' }]}>Begin appropriate treatment regimen</Text>
              </View>
              <View style={styles.bulletPoint}>
                <View style={styles.bullet} />
                <Text style={[styles.bulletText, { color: 'white' }]}>Monitor other fish for early symptoms</Text>
              </View>
            </>
          )}
          
          {selectedReport.notes && (
            <>
              <View style={styles.divider} />
              <Text style={[styles.notesTitle, { color: 'white' }]}>Analysis Details</Text>
              {(() => {
                try {
                  const analysisData = JSON.parse(selectedReport.notes.split('\n\n')[1]);
                  return (
                    <View style={styles.analysisContainer}>
                      <View style={styles.analysisSection}>
                        <Text style={[styles.analysisLabel, { color: 'white' }]}>Status:</Text>
                        <View 
                          style={[
                            styles.statusBadge, 
                            { 
                              backgroundColor: analysisData.isHealthy 
                                ? Colors[colorScheme].success 
                                : Colors[colorScheme].error,
                              opacity: 0.9
                            }
                          ]}
                        >
                          <Text style={styles.statusText}>
                            {analysisData.isHealthy ? 'Healthy' : 'Disease Detected'}
                          </Text>
                        </View>
                      </View>

                      {!analysisData.isHealthy && (
                        <>
                          <View style={styles.analysisSection}>
                            <Text style={[styles.analysisLabel, { color: 'white' }]}>Disease Type:</Text>
                            <Text style={[styles.analysisValue, { color: 'white' }]}>
                              {analysisData.diseaseType}
                            </Text>
                          </View>

                          {analysisData.description && (
                            <View style={styles.analysisSection}>
                              <Text style={[styles.analysisLabel, { color: 'white' }]}>Description:</Text>
                              <Text style={[styles.analysisValue, { color: 'white' }]}>
                                {analysisData.description}
                              </Text>
                            </View>
                          )}

                          {analysisData.symptoms && analysisData.symptoms.length > 0 && (
                            <View style={styles.analysisSection}>
                              <Text style={[styles.analysisLabel, { color: 'white' }]}>Symptoms:</Text>
                              {analysisData.symptoms.map((symptom: string, index: number) => (
                                <View key={index} style={styles.bulletPoint}>
                                  <View style={styles.bullet} />
                                  <Text style={[styles.bulletText, { color: 'white' }]}>{symptom}</Text>
                                </View>
                              ))}
                            </View>
                          )}

                          {analysisData.treatments && analysisData.treatments.length > 0 && (
                            <View style={styles.analysisSection}>
                              <Text style={[styles.analysisLabel, { color: 'white' }]}>Recommended Treatments:</Text>
                              {analysisData.treatments.map((treatment: string, index: number) => (
                                <View key={index} style={styles.bulletPoint}>
                                  <View style={styles.bullet} />
                                  <Text style={[styles.bulletText, { color: 'white' }]}>{treatment}</Text>
                                </View>
                              ))}
                            </View>
                          )}
                        </>
                      )}
                    </View>
                  );
                } catch (error) {
                  return (
                    <Text style={[styles.notesText, { color: 'white' }]}>
                      {selectedReport.notes}
                    </Text>
                  );
                }
              })()}
            </>
          )}
        </Card>
      </>
    );
  };

  if (loading) {
    return (
      <PageContainer>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={Colors[colorScheme].primary} />
        </View>
      </PageContainer>
    );
  }

  return (
    <PageContainer>
      <HeaderBar 
        title="Detection Reports"
        subtitle={selectedReport ? 'View report details' : 'Review your previous detections'}
      />
      
      {!selectedReport ? renderReportList() : renderReportDetail()}
    </PageContainer>
  );
}

const styles = StyleSheet.create({
  sectionTitle: {
    fontFamily: 'Inter-Bold',
    fontSize: 20,
    marginBottom: 16,
    color: 'white',
  },
  reportCard: {
    marginBottom: 12,
  },
  reportContent: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  reportImage: {
    width: 60,
    height: 60,
    borderRadius: 8,
  },
  reportDetails: {
    flex: 1,
    marginLeft: 12,
  },
  reportDate: {
    fontFamily: 'Inter-Regular',
    fontSize: 14,
    marginBottom: 4,
    color: 'white',
  },
  statusBadge: {
    alignSelf: 'flex-start',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
    marginBottom: 4,
  },
  statusText: {
    color: '#fff',
    fontFamily: 'Inter-Medium',
    fontSize: 12,
  },
  diseaseType: {
    fontFamily: 'Inter-Medium',
    fontSize: 14,
  },
  backButton: {
    marginBottom: 16,
  },
  backButtonText: {
    fontFamily: 'Inter-Medium',
    fontSize: 16,
  },
  reportDetailHeader: {
    marginBottom: 16,
  },
  reportDetailTitle: {
    fontFamily: 'Inter-Bold',
    fontSize: 22,
    marginBottom: 4,
    color: 'white',
  },
  reportDetailDate: {
    fontFamily: 'Inter-Regular',
    fontSize: 14,
    marginBottom: 4,
    color: 'white',
  },
  imageContainer: {
    height: 200,
    borderRadius: 12,
    overflow: 'hidden',
    marginBottom: 16,
  },
  detailImage: {
    width: '100%',
    height: '100%',
  },
  resultCard: {
    marginBottom: 24,
  },
  resultBadge: {
    alignSelf: 'flex-start',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    marginBottom: 12,
  },
  resultBadgeText: {
    color: '#fff',
    fontFamily: 'Inter-Medium',
    fontSize: 14,
  },
  resultDisease: {
    fontFamily: 'Inter-Bold',
    fontSize: 18,
    marginBottom: 4,
    color: 'white',
  },
  divider: {
    height: 1,
    backgroundColor: '#e1e1e1',
    marginVertical: 16,
  },
  diseaseSectionTitle: {
    fontFamily: 'Inter-Bold',
    fontSize: 16,
    marginBottom: 8,
    color: 'white',
  },
  diseaseDescription: {
    fontFamily: 'Inter-Regular',
    fontSize: 14,
    lineHeight: 22,
    color: 'white',
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
    color: 'white',
  },
  notesTitle: {
    fontFamily: 'Inter-Bold',
    fontSize: 16,
    marginBottom: 8,
    color: 'white',
  },
  notesText: {
    fontFamily: 'Inter-Regular',
    fontSize: 14,
    fontStyle: 'italic',
    color: 'white',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  errorText: {
    fontFamily: 'Inter-Medium',
    fontSize: 16,
    textAlign: 'center',
    marginBottom: 16,
    color: 'white',
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  emptyText: {
    fontFamily: 'Inter-Medium',
    fontSize: 16,
    textAlign: 'center',
    color: 'white',
  },
  analysisContainer: {
    marginTop: 8,
  },
  analysisSection: {
    marginBottom: 16,
  },
  analysisLabel: {
    fontFamily: 'Inter-Bold',
    fontSize: 16,
    marginBottom: 8,
  },
  analysisValue: {
    fontFamily: 'Inter-Regular',
    fontSize: 14,
    lineHeight: 20,
  },
});
