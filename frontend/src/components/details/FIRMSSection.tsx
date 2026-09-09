import type { ApiThermalEvent } from '@/types/api';

interface FIRMSSectionProps {
  event: ApiThermalEvent;
}

export const FIRMSSection = ({ event }: FIRMSSectionProps) => {
  const { brightness, frp, confidence, satellite, day_night, status, acquisition_time } = event;

  return (
    <div className="border border-gray-200 rounded-lg p-4">
      <div className="flex justify-between items-start mb-2">
        <h3 className="text-lg font-medium">FIRMS Data</h3>
      </div>

      <div className="space-y-2 text-sm">
        <div className="flex justify-between">
          <span>Acquisition Time:</span>
          <span>{new Date(acquisition_time).toLocaleString()}</span>
        </div>
        <div className="flex justify-between">
          <span>Satellite:</span>
          <span>{satellite}</span>
        </div>
        <div className="flex justify-between">
          <span>Day/Night:</span>
          <span>{day_night === 'D' ? 'Day' : day_night === 'N' ? 'Night' : 'Unknown'}</span>
        </div>
        <div className="flex justify-between">
          <span>Status:</span>
          <span className={status === 'active' ? 'text-green-600' : status === 'duplicate' ? 'text-yellow-600' : 'text-gray-600'}>
            {status}
          </span>
        </div>
        <div className="flex justify-between">
          <span>Confidence:</span>
          <span>{confidence !== null ? confidence + '%' : 'N/A'}</span>
        </div>
        <div className="flex justify-between">
          <span>Brightness Temperature:</span>
          <span>
            {brightness !== null && brightness !== undefined
              ? brightness.toFixed(1) + ' K'
              : 'N/A'}
          </span>
        </div>
        <div className="flex justify-between">
          <span>Fire Radiative Power (FRP):</span>
          <span>
            {frp !== null && frp !== undefined
              ? frp.toFixed(2) + ' MW'
              : 'N/A'}
          </span>
        </div>
      </div>
    </div>
  );
};