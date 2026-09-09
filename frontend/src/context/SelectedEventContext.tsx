import { createContext, useContext, useState, type ReactNode } from 'react';
import type { NormalizedEvent } from '@/types/normalized';
import { normalizeEvent } from '@/services/apiAdapter';

interface SelectedEventContextValue {
  selectedEvent: NormalizedEvent | null;
  selectEvent: (event: any) => void;
  clearSelection: () => void;
}

const SelectedEventContext = createContext<SelectedEventContextValue | null>(null);

export const SelectedEventProvider = ({ children }: { children: ReactNode }) => {
  const [selectedEvent, setSelectedEvent] = useState<NormalizedEvent | null>(null);

  const selectEvent = (event: any) => {
    if (!event) {
      setSelectedEvent(null);
      return;
    }
    // Automatically normalize if raw backend event is provided
    const normalized = event.event_id && event.location ? (event as NormalizedEvent) : normalizeEvent(event);
    setSelectedEvent(normalized);
  };

  const clearSelection = () => setSelectedEvent(null);

  return (
    <SelectedEventContext.Provider value={{ selectedEvent, selectEvent, clearSelection }}>
      {children}
    </SelectedEventContext.Provider>
  );
};

export const useSelectedEventContext = () => {
  const ctx = useContext(SelectedEventContext);
  if (!ctx) throw new Error('useSelectedEventContext must be inside SelectedEventProvider');
  return ctx;
};
