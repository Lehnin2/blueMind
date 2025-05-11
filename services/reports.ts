import { supabase } from './supabase';

export interface Report {
  id: string;
  user_id: string;
  title: string;
  description: string;
  status: 'pending' | 'in_progress' | 'resolved';
  image_url?: string;
  disease_type?: string;
  created_at: string;
  updated_at: string;
  latitude?: number;
  longitude?: number;
  location_name?: string;
}

export const useReports = () => {
  const getReports = async (userId?: string) => {
    let query = supabase!
      .from('reports')
      .select('*')
      .order('created_at', { ascending: false });

    if (userId) {
      query = query.eq('user_id', userId);
    }

    const { data, error } = await query;

    if (error) throw error;
    return data as Report[];
  };

  const getReportsWithLocation = async () => {
    const { data, error } = await supabase!
      .from('reports')
      .select('*')
      .not('latitude', 'is', null)
      .not('longitude', 'is', null)
      .order('created_at', { ascending: false });

    if (error) throw error;
    return data as Report[];
  };

  const createReport = async (report: Omit<Report, 'id' | 'created_at' | 'updated_at'>) => {
    const { data, error } = await supabase!
      .from('reports')
      .insert([
        {
          ...report,
          status: report.status || 'pending',
        },
      ])
      .select()
      .single();

    if (error) {
      console.error('Error creating report:', error);
      throw error;
    }
    return data as Report;
  };

  const updateReport = async (id: string, updates: Partial<Report>) => {
    const { data, error } = await supabase!
      .from('reports')
      .update(updates)
      .eq('id', id)
      .select()
      .single();

    if (error) throw error;
    return data as Report;
  };

  const deleteReport = async (id: string) => {
    const { error } = await supabase!.from('reports').delete().eq('id', id);
    if (error) throw error;
  };

  return {
    getReports,
    getReportsWithLocation,
    createReport,
    updateReport,
    deleteReport,
  };
};
