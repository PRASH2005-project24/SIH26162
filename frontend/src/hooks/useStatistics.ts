import { useQuery } from '@tanstack/react-query';
import apiService from '@/services/apiService';
import type { NormalizedStatistics } from '@/types/normalized';
import { normalizeStatistics } from '@/services/apiAdapter';

export const useStatistics = () => {
  return useQuery<NormalizedStatistics | null, Error>({
    queryKey: ['statistics'],
    queryFn: async () => {
      const response = await apiService.get('/events/statistics');
      if (!response.data) return null;
      return normalizeStatistics(response.data);
    },
    // Refetch every 5 minutes for statistics (less frequent than events)
    refetchInterval: 300000,
  });
};