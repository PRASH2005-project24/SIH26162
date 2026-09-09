import type { ApiThermalEvent } from '@/types/api';

interface SIHClassificationSectionProps {
  event: ApiThermalEvent;
}

export const SIHClassificationSection = ({ event }: SIHClassificationSectionProps) => {
  const { classification } = event;

  if (!classification) {
    return null;
  }

  const { category: sihCategory, confidence: sihConfidence, probabilities, model_type } = classification;

  // Compute original ML class from probabilities (argmax)
  let mlClass = 'unknown';
  let mlConfidence = 0;
  if (probabilities && Object.keys(probabilities).length > 0) {
    const entries = Object.entries(probabilities);
    const [maxClass, maxProb] = entries.reduce((a, b) => (a[1] > b[1] ? a : b));
    mlClass = maxClass as string;
    mlConfidence = maxProb as number;
  }

  // Map ML model class (3-class) to display string
  const mapMLClassToString = (mlClass: string): string => {
    switch (mlClass) {
      case 'agricultural': return 'Agricultural';
      case 'industrial': return 'Industrial';
      case 'wildfire': return 'Wildfire';
      default: return 'Unknown';
    }
  };

  return (
    <div className="border border-gray-200 rounded-lg p-4">
      <div className="flex justify-between items-start mb-2">
        <h3 className="text-lg font-medium">ML Classification</h3>
        {model_type && (
          <span className="text-xs text-gray-500 ml-2">{model_type}</span>
        )}
      </div>

      <div className="space-y-4">
        {/* Final SIH Classification */}
        <div className="border-t border-gray-200 pt-4">
          <h4 className="font-medium mb-2">Final SIH Classification</h4>
          <div className="flex items-center space-x-3">
            <span className="w-5 h-5 bg-blue-500 text-white rounded flex items-center justify-center text-xs font-medium">
              SIH
            </span>
            <div>
              <p className="text-sm font-medium text-gray-900">{sihCategory}</p>
              <p className="text-xs text-gray-600">
                Confidence: {Math.round(sihConfidence * 100)}%
              </p>
            </div>
          </div>
        </div>

        {/* Original ML Prediction */}
        <div className="border-t border-gray-200 pt-4">
          <h4 className="font-medium mb-2">ML Prediction (Original)</h4>
          <div className="flex items-center space-x-3">
            <span className="w-5 h-5 bg-green-500 text-white rounded flex items-center justify-center text-xs font-medium">
              ML
            </span>
            <div>
              <p className="text-sm font-medium text-gray-900">{mapMLClassToString(mlClass)}</p>
              <p className="text-xs text-gray-600">
                Confidence: {Math.round(mlConfidence * 100)}%
              </p>
            </div>
          </div>
        </div>

        {/* Class Probabilities */}
        {probabilities && Object.keys(probabilities).length > 0 && (
          <div className="border-t border-gray-200 pt-4">
            <h4 className="font-medium mb-2">Class Probabilities</h4>
            <div className="mt-2 text-xs space-y-1">
              <span className="font-medium">Probabilities:</span>
              <div className="mt-1 space-y-1">
                {Object.entries(probabilities).map(([className, prob]) => {
                  const probability = prob as number;
                  return (
                    <div key={className} className="flex justify-between">
                      <span>{className}</span>
                      <span>{(probability * 100).toFixed(1)}%</span>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};