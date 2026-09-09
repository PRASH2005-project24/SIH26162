import { useState } from 'react';
import type { ApiThermalEvent } from '@/types/api';

export const useSelectedEvent = () => {
  const [selectedEvent, setSelectedEvent] = useState<ApiThermalEvent | null>(null);

  const selectEvent = (event: ApiThermalEvent) => {
    setSelectedEvent(event);
  };

  const clearSelection = () => {
    setSelectedEvent(null);
  };

  return { selectedEvent, selectEvent, clearSelection };
};