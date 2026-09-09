import { useState } from 'react';
import { NavLink } from 'react-router-dom';
import type { SIHCategory } from '@/types';
import { useFilters } from '@/hooks/useFilters';

interface SidebarProps {
  isOpen: boolean;
  onToggleSidebar: () => void;
}

const fireCategories: {
  key: SIHCategory;
  num: string;
  name: string;
  icon: string;
  color: string;
}[] = [
  {
    key: 'Industrial Fire',
    num: '1',
    name: 'Industrial Fire',
    icon: '🏭',
    color: 'text-red-500',
  },
  {
    key: 'Wildfire / Natural Fire',
    num: '2',
    name: 'Wildfire / Natural Fire',
    icon: '🌲',
    color: 'text-emerald-500',
  },
  {
    key: 'Agricultural Fire',
    num: '3',
    name: 'Agricultural Fire',
    icon: '🌾',
    color: 'text-amber-500',
  },
  {
    key: 'Persistent Thermal Source',
    num: '4',
    name: 'Persistent Thermal Source',
    icon: '🌡️',
    color: 'text-orange-500',
  },
  {
    key: 'Unknown / Other',
    num: '5',
    name: 'Unknown / Other',
    icon: '❓',
    color: 'text-gray-400',
  },
];

export const Sidebar = ({ isOpen, onToggleSidebar }: SidebarProps) => {
  const { filters, setFilters } = useFilters();
  const [isClassificationOpen, setIsClassificationOpen] = useState(true);

  const toggleCategory = (category: SIHCategory) => {
    const current = filters.categories;
    const newCategories = current.includes(category)
      ? current.filter((c) => c !== category)
      : [...current, category];
    setFilters({ ...filters, categories: newCategories });
  };

  return (
    <>
      {/* Mobile backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/40 z-30 md:hidden"
          onClick={onToggleSidebar}
        />
      )}

      <aside
        className={`fixed md:sticky top-0 left-0 z-40 h-screen w-64 bg-white dark:bg-gray-800 border-r border-gray-100 dark:border-gray-700/80 flex flex-col transition-transform duration-300 ease-in-out ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        } md:translate-x-0 select-none`}
      >
        <div className="flex-1 overflow-y-auto px-4 py-6">
          {/* Main Navigation */}
          <nav className="space-y-1.5">
            {/* Dashboard (Active in screenshot) */}
            <NavLink
              to="/"
              end
              className={({ isActive }) =>
                `flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-semibold transition-all ${
                  isActive
                    ? 'bg-red-50 dark:bg-red-950/40 text-red-500 shadow-xs'
                    : 'text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700/40 font-medium'
                }`
              }
            >
              {/* 4-square grid icon */}
              <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
                <rect x="3" y="3" width="7" height="7" rx="1.5" />
                <rect x="14" y="3" width="7" height="7" rx="1.5" />
                <rect x="3" y="14" width="7" height="7" rx="1.5" />
                <rect x="14" y="14" width="7" height="7" rx="1.5" />
              </svg>
              <span>Dashboard</span>
            </NavLink>

            {/* Settings */}
            <NavLink
              to="/settings"
              className={({ isActive }) =>
                `flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-medium transition-all ${
                  isActive
                    ? 'bg-red-50 dark:bg-red-950/40 text-red-500 font-semibold shadow-xs'
                    : 'text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700/40'
                }`
              }
            >
              {/* Cog / gear icon */}
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
                />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              <span>Settings</span>
            </NavLink>
          </nav>

          {/* Classification Section */}
          <div className="mt-8 pt-4 border-t border-gray-100 dark:border-gray-700/60">
            <button
              onClick={() => setIsClassificationOpen(!isClassificationOpen)}
              className="w-full flex items-center justify-between text-xs font-bold text-gray-900 dark:text-gray-100 tracking-tight py-2 px-1 hover:text-gray-600 transition-colors"
            >
              <span>Classification of Fire</span>
              <svg
                className={`w-3.5 h-3.5 text-gray-500 transition-transform ${
                  isClassificationOpen ? 'transform rotate-180' : ''
                }`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
              </svg>
            </button>

            {isClassificationOpen && (
              <div className="mt-2 space-y-1">
                {fireCategories.map((cat) => {
                  const isChecked = filters.categories.includes(cat.key);
                  return (
                    <button
                      key={cat.key}
                      onClick={() => toggleCategory(cat.key)}
                      className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs text-left transition-all ${
                        isChecked
                          ? 'text-gray-800 dark:text-gray-200 font-medium hover:bg-gray-50 dark:hover:bg-gray-700/40'
                          : 'text-gray-400 dark:text-gray-500 line-through opacity-60 hover:opacity-100'
                      }`}
                    >
                      <span className="text-xs">{cat.icon}</span>
                      <span className="truncate">
                        {cat.num}. {cat.name}
                      </span>
                    </button>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </aside>
    </>
  );
};