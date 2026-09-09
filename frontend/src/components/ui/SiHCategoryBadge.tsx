import type { SIHCategory } from '@/types';

interface SiHCategoryBadgeProps {
  category: SIHCategory;
  className?: string;
}

export const SiHCategoryBadge = ({ category, className = '' }: SiHCategoryBadgeProps) => {
  // Define colors for each category
  const colorMap: Record<SIHCategory, string> = {
    'Industrial Fire': 'bg-red-100 text-red-800',
    'Wildfire / Natural Fire': 'bg-orange-100 text-orange-800',
    'Agricultural Fire': 'bg-yellow-100 text-yellow-800',
    'Persistent Thermal Source': 'bg-blue-100 text-blue-800',
    'Unknown / Other': 'bg-gray-100 text-gray-800'
  };

  // Define labels for display
  const labelMap: Record<SIHCategory, string> = {
    'Industrial Fire': 'Industrial',
    'Wildfire / Natural Fire': 'Wildfire',
    'Agricultural Fire': 'Agricultural',
    'Persistent Thermal Source': 'Persistent',
    'Unknown / Other': 'Unknown'
  };

  const bgColor = colorMap[category] || 'bg-gray-100 text-gray-800';
  const label = labelMap[category] || category;

  return (
    <span className={`px-2 py-1 text-xs font-medium rounded-full ${bgColor} ${className}`}>
      {label}
    </span>
  );
};