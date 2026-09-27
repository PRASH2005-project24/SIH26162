import type { SIHCategory } from '@/types';

interface SiHCategoryBadgeProps {
  category: SIHCategory;
  className?: string;
}

export const SiHCategoryBadge = ({ category, className = '' }: SiHCategoryBadgeProps) => {
  // Define colors for each category with high-clarity dark mode support
  const colorMap: Record<string, string> = {
    'Industrial Fire': 'bg-red-50 text-red-700 dark:bg-red-950/50 dark:text-red-300 border border-red-200 dark:border-red-900/60 shadow-xs shadow-red-500/10',
    'Wildfire / Natural Fire': 'bg-orange-50 text-orange-700 dark:bg-orange-950/50 dark:text-orange-300 border border-orange-200 dark:border-orange-900/60 shadow-xs shadow-orange-500/10',
    'Agricultural Fire': 'bg-amber-50 text-amber-700 dark:bg-amber-950/50 dark:text-amber-300 border border-amber-200 dark:border-amber-900/60 shadow-xs shadow-amber-500/10',
    'Persistent Thermal Source': 'bg-blue-50 text-blue-700 dark:bg-blue-950/50 dark:text-blue-300 border border-blue-200 dark:border-blue-900/60 shadow-xs shadow-blue-500/10',
    'Unknown / Other': 'bg-gray-100 text-gray-700 dark:bg-slate-800 dark:text-gray-300 border border-gray-200 dark:border-slate-700',
  };

  // Define labels for display
  const labelMap: Record<string, string> = {
    'Industrial Fire': 'Industrial',
    'Wildfire / Natural Fire': 'Wildfire',
    'Agricultural Fire': 'Agricultural',
    'Persistent Thermal Source': 'Persistent',
    'Unknown / Other': 'Unknown',
  };

  const badgeStyle = colorMap[category] || 'bg-gray-100 text-gray-700 dark:bg-slate-800 dark:text-gray-300 border border-gray-200 dark:border-slate-700';
  const label = labelMap[category] || category;

  return (
    <span className={`px-2.5 py-0.5 text-[11px] font-bold rounded-full select-none inline-flex items-center gap-1 ${badgeStyle} ${className}`}>
      {label}
    </span>
  );
};