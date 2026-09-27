import { createContext, createElement, useContext, useState, type ReactNode } from 'react';

export type TimeRangeOption = 'live' | 'today' | '24h' | '7d' | '30d' | 'all' | 'custom';

export interface Filters {
  timeRange: TimeRangeOption;
  customStartDate: Date | null;
  customEndDate: Date | null;
  categories: string[];
  minConfidence: number; // 0 to 100
  onlyWithSatelliteImage: boolean;
  searchQuery: string;
}

export const ALL_SIH_CATEGORIES = [
  'Industrial Fire',
  'Wildfire / Natural Fire',
  'Agricultural Fire',
  'Persistent Thermal Source',
  'Unknown / Other',
];

const defaultFilters: Filters = {
  timeRange: 'live', // Default to Live Feed on first open
  customStartDate: null,
  customEndDate: null,
  categories: [...ALL_SIH_CATEGORIES],
  minConfidence: 0,
  onlyWithSatelliteImage: false,
  searchQuery: '',
};

interface FiltersContextValue {
  filters: Filters;
  setFilters: React.Dispatch<React.SetStateAction<Filters>>;
  resetFilters: () => void;
}

const FiltersContext = createContext<FiltersContextValue | null>(null);

export const FiltersProvider = ({ children }: { children: ReactNode }) => {
  const [filters, setFilters] = useState<Filters>(defaultFilters);

  const resetFilters = () => {
    setFilters(defaultFilters);
  };

  return createElement(
    FiltersContext.Provider,
    { value: { filters, setFilters, resetFilters } },
    children
  );
};

export const useFilters = () => {
  const context = useContext(FiltersContext);

  if (!context) {
    throw new Error('useFilters must be used within a FiltersProvider');
  }

  return context;
};