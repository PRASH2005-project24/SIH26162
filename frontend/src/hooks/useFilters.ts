import { createContext, createElement, useContext, useState, type ReactNode } from 'react';

export interface Filters {
  timeRange: 'today' | '24h' | '7d' | '30d' | 'custom';
  customStartDate: Date | null; // used when timeRange is 'custom'
  customEndDate: Date | null; // used when timeRange is 'custom'
  categories: string[]; // List of selected SIH categories
}

const defaultFilters: Filters = {
    timeRange: '7d', // default to last 1 week (matches UI '1 week ago')
    customStartDate: null, // no custom start date by default
    customEndDate: null, // no custom end date by default
    categories: [ // default to all categories selected
      'Industrial Fire',
      'Wildfire / Natural Fire',
      'Agricultural Fire',
      'Persistent Thermal Source',
      'Unknown / Other'
    ]
};

interface FiltersContextValue {
  filters: Filters;
  setFilters: React.Dispatch<React.SetStateAction<Filters>>;
}

const FiltersContext = createContext<FiltersContextValue | null>(null);

export const FiltersProvider = ({ children }: { children: ReactNode }) => {
  const [filters, setFilters] = useState<Filters>(defaultFilters);

  return createElement(
    FiltersContext.Provider,
    { value: { filters, setFilters } },
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