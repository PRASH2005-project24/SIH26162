import React, { useMemo } from 'react';
import { Marker, Popup, Tooltip } from 'react-leaflet';
import L from 'leaflet';
import type { NormalizedEvent } from '@/types/normalized';
import { useSelectedEventContext } from '@/context/SelectedEventContext';

interface EventMarkerProps {
  event: NormalizedEvent;
  isSelected?: boolean;
}

// Global icon cache to prevent Leaflet from thrashing DOM nodes on every render
const iconCache = new Map<string, L.DivIcon>();

function getMarkerIcon(color: string, isSelected: boolean): L.DivIcon {
  const cacheKey = `${color}-${isSelected ? 1 : 0}`;
  let icon = iconCache.get(cacheKey);
  if (!icon) {
    const size = isSelected ? 18 : 13;
    icon = L.divIcon({
      className: 'custom-fire-marker',
      html: `<div style="
        width: ${size}px;
        height: ${size}px;
        border-radius: 50%;
        background: ${color};
        border: 2px solid #ffffff;
        box-shadow: ${
          isSelected
            ? `0 0 0 4px ${color}66, 0 2px 8px rgba(0,0,0,0.45)`
            : `0 1px 4px rgba(0,0,0,0.35)`
        };
        cursor: pointer;
      "></div>`,
      iconSize: [size, size],
      iconAnchor: [size / 2, size / 2],
      popupAnchor: [0, -size],
      tooltipAnchor: [0, -size],
    });
    iconCache.set(cacheKey, icon);
  }
  return icon;
}

export const EventMarker = React.memo(({ event, isSelected }: EventMarkerProps) => {
  const { selectEvent } = useSelectedEventContext();
  const { latitude, longitude, classification, frp, confidence, color, location } = event;

  // Use normalized color by SIH Category (defaults to standard red #ef4444)
  const markerColor = color || '#ef4444';
  const icon = useMemo(() => getMarkerIcon(markerColor, Boolean(isSelected)), [markerColor, isSelected]);

  const confPercent = Math.round(confidence <= 1 ? confidence * 100 : confidence);
  const timeFormatted = event.acquisition_time
    ? new Date(event.acquisition_time).toLocaleString('en-IN', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      })
    : '';

  return (
    <Marker
      position={[latitude, longitude]}
      icon={icon}
      eventHandlers={{
        click: (e) => {
          L.DomEvent.stopPropagation(e as any);
          selectEvent(event);
        },
      }}
    >
      <Tooltip direction="top" offset={[0, -6]}>
        <div className="font-semibold text-xs py-0.5">
          <span>{classification}</span>
          <span className="text-gray-400 font-normal ml-1">({confPercent}%)</span>
        </div>
      </Tooltip>
      <Popup>
        <div className="p-1 min-w-48 font-sans">
          <div className="flex items-center justify-between gap-2">
            <span
              className="text-xs font-bold px-2 py-0.5 rounded-md"
              style={{ backgroundColor: `${markerColor}20`, color: markerColor }}
            >
              {classification}
            </span>
            <span className="text-[10px] text-gray-500 font-mono">
              #{event.event_id}
            </span>
          </div>

          <div className="text-[11px] font-medium text-gray-800 mt-1.5">
            {location.city}, {location.state}
          </div>

          <div className="mt-2 pt-2 border-t border-gray-100 space-y-1 text-xs">
            <div className="flex items-center justify-between">
              <span className="text-gray-500">Confidence:</span>
              <span className="font-bold text-emerald-600">{confPercent}%</span>
            </div>
            {frp != null && (
              <div className="flex items-center justify-between">
                <span className="text-gray-500">Thermal (FRP):</span>
                <span className="font-semibold text-gray-900">{Number(frp).toFixed(1)} MW</span>
              </div>
            )}
            {event.brightness != null && (
              <div className="flex items-center justify-between">
                <span className="text-gray-500">Brightness:</span>
                <span className="font-semibold text-gray-900">{Number(event.brightness).toFixed(1)} K</span>
              </div>
            )}
            <div className="flex items-center justify-between text-[11px] text-gray-400">
              <span>Sensor:</span>
              <span>{event.satellite_name}</span>
            </div>
            {timeFormatted && (
              <div className="flex items-center justify-between text-[11px] text-gray-400">
                <span>Observed:</span>
                <span>{timeFormatted}</span>
              </div>
            )}
          </div>
        </div>
      </Popup>
    </Marker>
  );
});