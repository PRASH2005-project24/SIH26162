import { useQuery } from '@tanstack/react-query';
import { useDeferredValue, useMemo } from 'react';
import apiService from '@/services/apiService';
import type { ApiEventsListResponse } from '@/types/api';
import type { NormalizedEvent } from '@/types/normalized';
import type { SIHCategory } from '@/types/index';
import { useFilters } from '@/hooks/useFilters';
import { normalizeEvent } from '@/services/apiAdapter';
import { isInsideIndia } from '@/utils/indiaBoundary';

const API_PAGE_SIZE = 1000;

export interface UseEventsResult {
  data: {
    events: NormalizedEvent[];
    total: number;
    limit: number;
    offset: number;
    has_more: boolean;
    liveCount: number;
    historicalCount: number;
  };
  allRawEventsCount: number;
  rawResponse?: ApiEventsListResponse;
  isLoading: boolean;
  error: Error | null;
  refetch: () => void;
}

export const useEvents = (): UseEventsResult => {
  const { filters } = useFilters();
  const {
    timeRange,
    customStartDate,
    customEndDate,
    categories,
    minConfidence,
    onlyWithSatelliteImage,
    searchQuery,
  } = filters;
  const deferredMinConfidence = useDeferredValue(minConfidence);

  // Compute sinceHours for API calls
  const sinceHours = useMemo(() => {
    const now = new Date();
    switch (timeRange) {
      case 'live':
        return 24;
      case 'today':
      case '24h':
        return 24;
      case '7d':
        return 24 * 7;
      case '30d':
        return 24 * 30;
      case 'all':
        return 24 * 365; // All time up to 1 year
      case 'custom':
        if (customStartDate) {
          return Math.max(1, Math.floor((now.getTime() - customStartDate.getTime()) / (1000 * 60 * 60)));
        }
        return 720;
      default:
        return 24 * 365;
    }
  }, [timeRange, customStartDate]);

  // Prepare API parameters
  const params: Record<string, any> = {
    limit: API_PAGE_SIZE,
    include_ml: true,
    include_enrichment: true,
    since_hours: sinceHours,
  };

  const { data, isLoading, error, refetch } = useQuery<ApiEventsListResponse, Error>({
    queryKey: ['events', params],
    queryFn: async () => {
      const allEvents: ApiEventsListResponse['events'] = [];
      let offset = 0;
      let lastPage: ApiEventsListResponse;

      do {
        const response = await apiService.get('/events', {
          params: { ...params, offset },
        });
        lastPage = response.data;
        allEvents.push(...lastPage.events);
        offset += lastPage.limit || API_PAGE_SIZE;
      } while (lastPage.has_more);

      return {
        ...lastPage,
        events: allEvents,
        total: allEvents.length,
        offset: 0,
        has_more: false,
      };
    },
    refetchInterval: 30000, // Refetch every 30 seconds for live updates
    retry: 1,
  });

  // Filter and normalize events
  const { filteredEvents, liveCount, historicalCount, allEventsCount } = useMemo(() => {
    const rawEvents = data?.events ?? [];
    const normalizedList: NormalizedEvent[] = rawEvents
      .map(normalizeEvent)
      .filter((e) => isInsideIndia(e.latitude, e.longitude));

    const now = new Date();
    const nowMs = now.getTime();

    // Calculate total counts
    let totalLive = 0;
    let totalHistorical = 0;
    normalizedList.forEach((e) => {
      const eventTime = new Date(e.acquisition_time).getTime();
      const ageHours = (nowMs - eventTime) / (1000 * 60 * 60);
      if (e.raw?.is_live || ageHours <= 24 || (e.raw?.status === 'active' && ageHours <= 48)) {
        totalLive++;
      } else {
        totalHistorical++;
      }
    });

    let events = normalizedList;

    // 1. Filter by Time Range
    if (timeRange === 'live') {
      events = events.filter((e) => {
        if (e.raw?.is_live) return true;
        const eventTime = new Date(e.acquisition_time).getTime();
        const ageHours = (nowMs - eventTime) / 3600000;
        return ageHours >= -2 && (ageHours <= 24 || (e.raw?.status === 'active' && ageHours <= 48));
      });
    } else if (timeRange === '24h' || timeRange === 'today') {
      events = events.filter((e) => {
        const eventTime = new Date(e.acquisition_time).getTime();
        const ageHours = (nowMs - eventTime) / 3600000;
        return ageHours >= -2 && ageHours <= 36;
      });
    } else if (timeRange === '7d') {
      events = events.filter((e) => {
        const eventTime = new Date(e.acquisition_time).getTime();
        return (nowMs - eventTime) <= 7 * 24 * 3600000;
      });
    } else if (timeRange === '30d') {
      events = events.filter((e) => {
        const eventTime = new Date(e.acquisition_time).getTime();
        return (nowMs - eventTime) <= 30 * 24 * 3600000;
      });
    } else if (timeRange === 'custom' && (customStartDate || customEndDate)) {
      const startTime = customStartDate?.getTime() ?? Number.NEGATIVE_INFINITY;
      const endTime = customEndDate?.getTime() ?? Number.POSITIVE_INFINITY;
      events = events.filter((e) => {
        const eventTime = new Date(e.acquisition_time).getTime();
        return eventTime >= startTime && eventTime <= endTime;
      });
    }
    // timeRange === 'all' includes both live and historical

    // 2. Filter by Categories
    if (categories.length > 0) {
      events = events.filter((e) => {
        const eventCategory = e.classification || 'Unknown / Other';
        return categories.includes(eventCategory as SIHCategory);
      });
    }

    // 3. Filter by Minimum Confidence
    if (deferredMinConfidence > 0) {
      events = events.filter((e) => {
        const confPercent = Math.round((e.confidence <= 1 ? e.confidence * 100 : e.confidence));
        return confPercent >= deferredMinConfidence;
      });
    }

    // 4. Filter by Satellite Image Availability
    if (onlyWithSatelliteImage) {
      events = events.filter((e) => Boolean(e.satellite?.available && e.satellite?.url));
    }

    // 5. Filter by Search Query
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase().trim();
      events = events.filter((e) => {
        return (
          e.event_id.toLowerCase().includes(query) ||
          e.location.city.toLowerCase().includes(query) ||
          e.location.state.toLowerCase().includes(query) ||
          e.classification.toLowerCase().includes(query)
        );
      });
    }

    return {
      filteredEvents: events,
      liveCount: totalLive,
      historicalCount: totalHistorical,
      allEventsCount: normalizedList.length,
    };
  }, [
    data,
    timeRange,
    customStartDate,
    customEndDate,
    categories,
    deferredMinConfidence,
    onlyWithSatelliteImage,
    searchQuery,
  ]);

  return {
    data: {
      events: filteredEvents,
      total: filteredEvents.length,
      limit: data?.limit || 200,
      offset: data?.offset || 0,
      has_more: false,
      liveCount,
      historicalCount,
    },
    allRawEventsCount: allEventsCount,
    rawResponse: data,
    isLoading,
    error,
    refetch,
  };
};