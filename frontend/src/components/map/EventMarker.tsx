import { Marker, Popup, Tooltip } from 'react-leaflet';
import L from 'leaflet';
import type { NormalizedEvent } from '@/types/normalized';
import { useSelectedEventContext } from '@/context/SelectedEventContext';

interface EventMarkerProps {
  event: NormalizedEvent;
  isSelected?: boolean;
}

export const EventMarker = ({ event, isSelected }: EventMarkerProps) => {
  const { selectEvent } = useSelectedEventContext();
  const { latitude, longitude, classification, frp, confidence, color, risk_score, risk_level, location } = event;

  // Use normalized color from contract
  const markerColor = color || '#ef4444';

  const size = isSelected ? 18 : 13;
  const icon = L.divIcon({
    className: 'custom-fire-marker',
    html: `<div style="
      width: ${size}px;
      height: ${size}px;
      border-radius: 50%;
      background: ${markerColor};
      border: 2px solid white;
      box-shadow: ${isSelected ? '0 0 0 4px rgba(239, 68, 68, 0.4), 0 2px 6px rgba(0,0,0,0.3)' : '0 1px 4px rgba(0,0,0,0.35)'};
      cursor: pointer;
      transition: all 0.2s ease;
    "></div>`,
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
    popupAnchor: [0, -size],
    tooltipAnchor: [0, -size],
  });

  return (
    <Marker
      position={[latitude, longitude]}
      icon={icon}
      eventHandlers={{
        click: () => {
          selectEvent(event);
        },
      }}
    >
      <Tooltip direction="top" offset={[0, -5]}>
        <div className="font-semibold text-xs">{classification}</div>
      </Tooltip>
      <Popup>
        <div className="p-1 min-w-44">
          <div className="font-bold text-xs text-gray-900">{classification}</div>
          <div className="text-[11px] text-gray-500 mt-0.5">
            {location.city}, {location.state}
          </div>
          <div className="mt-1.5 pt-1.5 border-t border-gray-100 space-y-0.5 text-xs">
            <div className="flex items-center justify-between">
              <span className="text-gray-600">Risk Score:</span>
              <span className="font-bold text-red-600">{risk_score} / 100 ({risk_level})</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-600">Confidence:</span>
              <span className="font-bold text-emerald-600">{Math.round(confidence * 100)}%</span>
            </div>
            {frp != null && (
              <div className="flex items-center justify-between">
                <span className="text-gray-600">FRP:</span>
                <span className="font-semibold text-gray-900">{Number(frp).toFixed(1)} MW</span>
              </div>
            )}
          </div>
          <button
            onClick={() => selectEvent(event)}
            className="w-full mt-2 py-1 px-2 text-[11px] font-semibold bg-red-50 hover:bg-red-100 text-red-600 rounded transition-colors text-center cursor-pointer"
          >
            Inspect Detection
          </button>
        </div>
      </Popup>
    </Marker>
  );
};