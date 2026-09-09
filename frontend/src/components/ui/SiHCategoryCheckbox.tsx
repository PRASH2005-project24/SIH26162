import React from 'react';
import type { SIHCategory } from '@/types/index';

interface SiHCategoryCheckboxProps {
  category: SIHCategory;
  checked: boolean;
  onChange: (category: SIHCategory, checked: boolean) => void;
}

export const SiHCategoryCheckbox = ({
  category,
  checked,
  onChange
}: SiHCategoryCheckboxProps) => {
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onChange(category, e.target.checked);
  };

  return (
    <label className="flex items-center space-x-2">
      <input
        type="checkbox"
        checked={checked}
        onChange={handleChange}
        className="h-4 w-4 text-indigo-600 border-gray-300 rounded"
      />
      <span className="text-sm">{category}</span>
    </label>
  );
};