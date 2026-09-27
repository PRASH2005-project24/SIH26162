import React from 'react';
import type { SIHCategory } from '@/types/index';
import { Factory, Trees, Wheat, Zap, HelpCircle, Flame } from 'lucide-react';

interface SiHCategoryCheckboxProps {
  category: SIHCategory;
  checked: boolean;
  onChange: (category: SIHCategory, checked: boolean) => void;
}

const CATEGORY_ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  'Industrial Fire': Factory,
  'Wildfire / Natural Fire': Trees,
  'Agricultural Fire': Wheat,
  'Persistent Thermal Source': Zap,
  'Unknown / Other': HelpCircle,
};

const CHECKED_STYLES: Record<string, string> = {
  'Industrial Fire': 'bg-red-500 text-white border-red-500 shadow-xs shadow-red-500/30',
  'Wildfire / Natural Fire': 'bg-orange-500 text-white border-orange-500 shadow-xs shadow-orange-500/30',
  'Agricultural Fire': 'bg-amber-500 text-white border-amber-500 shadow-xs shadow-amber-500/30',
  'Persistent Thermal Source': 'bg-blue-500 text-white border-blue-500 shadow-xs shadow-blue-500/30',
  'Unknown / Other': 'bg-gray-600 text-white border-gray-600 shadow-xs shadow-gray-500/20',
};

export const SiHCategoryCheckbox = ({
  category,
  checked,
  onChange
}: SiHCategoryCheckboxProps) => {
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onChange(category, e.target.checked);
  };

  const IconComponent = CATEGORY_ICONS[category] || Flame;
  const checkedClass = CHECKED_STYLES[category] || 'bg-red-500 text-white border-red-500';

  return (
    <label
      className={`px-3 py-1.5 rounded-xl border text-xs font-semibold cursor-pointer select-none transition-all flex items-center gap-1.5 active:scale-95 ${
        checked
          ? checkedClass
          : 'bg-white dark:bg-slate-800/80 border-gray-200 dark:border-slate-700 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-slate-700/60'
      }`}
    >
      <input
        type="checkbox"
        checked={checked}
        onChange={handleChange}
        className="sr-only"
      />
      <IconComponent className="w-3.5 h-3.5 shrink-0" />
      <span>{category}</span>
    </label>
  );
};