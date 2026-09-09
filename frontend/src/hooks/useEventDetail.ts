import { useQuery } from '@tanstack/react-query';
import apiService from '@/services/apiService';
import type { ApiEventDetailResponse } from '@/types/api';

export const useEventDetail = (eventId: string) => {
  return useQuery<ApiEventDetailResponse, Error>({
    queryKey: ['event', eventId],
    queryFn: async () => {
      const response = await apiService.get(`/events/${eventId}`, {
        params: {
          include_enrichment: true,
          include_ml: true
        }
      });
      return response.data;
    },
    enabled: !!eventId, // Only run if eventId is provided
  });
};