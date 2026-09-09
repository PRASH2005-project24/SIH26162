import { useQuery } from '@tanstack/react-query';
import { useMemo } from 'react';
import apiService from '@/services/apiService';
import type { ApiEventsListResponse } from '@/types/api';
import type { NormalizedEvent } from '@/types/normalized';
import type { SIHCategory } from '@/types/index';
import { useFilters } from '@/hooks/useFilters';
import { normalizeEvent } from '@/services/apiAdapter';

export interface UseEventsResult {
  data: {
    events: NormalizedEvent[];
    total: number;
    limit: number;
    offset: number;
    has_more: boolean;
  };
  rawResponse?: ApiEventsListResponse;
  isLoading: boolean;
  error: Error | null;
  refetch: () => void;
}

export const useEvents = (): UseEventsResult => {
  const { filters } = useFilters();
  const { timeRange, customStartDate, customEndDate, categories } = filters;

  // Compute sinceHours based on timeRange
  const sinceHours = useMemo(() => {
    const now = new Date();
    switch (timeRange) {
      case 'today': {
        const startOfToday = new Date(now.getFullYear(), now.getMonth(), now.getDate());
        return Math.max(1, Math.floor((now.getTime() - startOfToday.getTime()) / (1000 * 60 * 60)));
      }
      case '24h':
        return 24;
      case '7d':
        return 24 * 7;
      case '30d':
        return 24 * 30;
      case 'custom':
        if (customStartDate) {
          return Math.floor((now.getTime() - customStartDate.getTime()) / (1000 * 60 * 60));
        }
        return 720; // fallback to 30 days
      default:
        return 168; // default to 7 days
    }
  }, [timeRange, customStartDate]);

  // Prepare API parameters
  const params: Record<string, any> = {
    limit: 200,
    include_ml: true,
    include_enrichment: true,
    since_hours: sinceHours,
  };

  const { data, isLoading, error, refetch } = useQuery<ApiEventsListResponse, Error>({
    queryKey: ['events', params],
    queryFn: async () => {
      const response = await apiService.get('/events', { params });
      return response.data;
    },
    refetchInterval: 60000, // Refetch every minute for live data
  });

  // Filter and normalize events
  const filteredEvents = useMemo(() => {
    if (!data?.events) return { events: [], total: 0, limit: 0, offset: 0, has_more: false };

    // Convert all events into normalized shape
    const normalizedList: NormalizedEvent[] = data.events.map(normalizeEvent);

    let events = normalizedList;

    // Filter by custom date range if applicable
    if (timeRange === 'custom' && (customStartDate || customEndDate)) {
      const startTime = customStartDate?.getTime() ?? Number.NEGATIVE_INFINITY;
      const endTime = customEndDate?.getTime() ?? Number.POSITIVE_INFINITY;
      events = events.filter((event) => {
        const eventTime = new Date(event.raw?.acquisition_time || event.satellite?.acquisition_date).getTime();
        return eventTime >= startTime && eventTime <= endTime;
      });
    }

    // Filter by selected categories
    if (categories.length > 0) {
      events = events.filter((event) => {
        const eventCategory = event.classification || 'Unknown / Other';
        return categories.includes(eventCategory as SIHCategory);
      });
    }

    return {
      events,
      total: events.length,
      limit: data.limit || 200,
      offset: data.offset || 0,
      has_more: events.length === data.limit && Boolean(data.has_more),
    };
  }, [data, timeRange, customStartDate, customEndDate, categories]);

  return {
    data: filteredEvents,
    rawResponse: data,
    isLoading,
    error,
    refetch,
  };
};