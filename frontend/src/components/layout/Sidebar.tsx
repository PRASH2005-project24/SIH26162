import { NavLink } from 'react-router-dom';
import { useFilters } from '@/hooks/useFilters';

interface SidebarProps {
  isOpen: boolean;
  onToggleSidebar: () => void;
}

export const Sidebar = ({ isOpen, onToggleSidebar }: SidebarProps) => {
  const { resetFilters } = useFilters();

  return (
    <>
      {/* Backdrop */}
      <div
        className={`fixed inset-0 bg-black/60 z-40 backdrop-blur-xs transition-opacity duration-300 ${
          isOpen ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'
        }`}
        onClick={onToggleSidebar}
        aria-hidden="true"
      />

      {/* Slide-over Drawer */}
      <aside
        className={`fixed top-0 left-0 z-50 h-screen w-72 sm:w-80 bg-white/95 dark:bg-[#0c101c]/95 backdrop-blur-xl border-r border-gray-200/80 dark:border-slate-800/80 flex flex-col shadow-2xl transition-transform duration-300 ease-in-out ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        } select-none`}
      >
        <div className="flex-1 flex flex-col justify-between px-5 py-6 overflow-y-auto custom-scrollbar">
          <div>
            {/* Header with App Logo & Close Button */}
            <div className="flex items-center justify-between pb-4 border-b border-gray-100 dark:border-gray-700/60 mb-6">
              <div className="flex flex-col pr-3">
                <div className="text-base font-black text-gray-900 dark:text-white tracking-wider leading-tight">
                  FIREXIS
                </div>
                <div className="text-[11px] font-semibold text-red-500 dark:text-red-400 mt-1 leading-snug">
                  Fire intelligence and Risk Exploration System
                </div>
              </div>

              {/* Close Button */}
              <button
                onClick={onToggleSidebar}
                className="p-1.5 rounded-xl text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors cursor-pointer"
                aria-label="Close sidebar"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Navigation Links */}
            <nav className="space-y-2">
              {/* 1. Dashboard Map */}
              <NavLink
                to="/"
                end
                onClick={() => {
                  resetFilters();
                  onToggleSidebar();
                }}
                className={({ isActive }) =>
                  `flex items-center gap-3.5 px-3.5 py-3 rounded-2xl text-xs font-bold transition-all ${
                    isActive
                      ? 'bg-red-50 dark:bg-red-950/40 text-red-600 dark:text-red-400 border border-red-200/60 dark:border-red-900/40 shadow-xs'
                      : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100/70 dark:hover:bg-gray-700/50'
                  }`
                }
              >
                <div className="w-7 h-7 rounded-xl bg-gray-100 dark:bg-gray-700 flex items-center justify-center text-gray-600 dark:text-gray-300">
                  <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
                    <rect x="3" y="3" width="7" height="7" rx="1.5" />
                    <rect x="14" y="3" width="7" height="7" rx="1.5" />
                    <rect x="3" y="14" width="7" height="7" rx="1.5" />
                    <rect x="14" y="14" width="7" height="7" rx="1.5" />
                  </svg>
                </div>
                <div>
                  <div className="leading-tight">Dashboard Map</div>
                  <div className="text-[10px] text-gray-400 font-normal">Real-time India detection</div>
                </div>
              </NavLink>

              {/* 2. Historical Records */}
              <NavLink
                to="/historical-events"
                onClick={onToggleSidebar}
                className={({ isActive }) =>
                  `flex items-center justify-between px-3.5 py-3 rounded-2xl text-xs font-bold transition-all ${
                    isActive
                      ? 'bg-red-50 dark:bg-red-950/40 text-red-600 dark:text-red-400 border border-red-200/60 dark:border-red-900/40 shadow-xs'
                      : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100/70 dark:hover:bg-gray-700/50'
                  }`
                }
              >
                <div className="flex items-center gap-3.5">
                  <div className="w-7 h-7 rounded-xl bg-gray-100 dark:bg-gray-700 flex items-center justify-center text-gray-600 dark:text-gray-300">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 10h18M3 14h18m-9-4v8m-7 4h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                  </div>
                  <div>
                    <div className="leading-tight">Historical Records</div>
                    <div className="text-[10px] text-gray-400 font-normal">Table & past database</div>
                  </div>
                </div>
                <span className="text-[10px] px-2 py-0.5 rounded-full font-bold bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300">
                  Data
                </span>
              </NavLink>

              {/* 3. ML Analytics */}
              <NavLink
                to="/analytics"
                onClick={onToggleSidebar}
                className={({ isActive }) =>
                  `flex items-center gap-3.5 px-3.5 py-3 rounded-2xl text-xs font-bold transition-all ${
                    isActive
                      ? 'bg-red-50 dark:bg-red-950/40 text-red-600 dark:text-red-400 border border-red-200/60 dark:border-red-900/40 shadow-xs'
                      : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100/70 dark:hover:bg-gray-700/50'
                  }`
                }
              >
                <div className="w-7 h-7 rounded-xl bg-gray-100 dark:bg-gray-700 flex items-center justify-center text-gray-600 dark:text-gray-300">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                </div>
                <div>
                  <div className="leading-tight">ML Analytics</div>
                  <div className="text-[10px] text-gray-400 font-normal">Classification stats</div>
                </div>
              </NavLink>
              {/* 4. Settings */}
              <NavLink
                to="/settings"
                onClick={onToggleSidebar}
                className={({ isActive }) =>
                  `flex items-center justify-between px-3.5 py-3 rounded-2xl text-xs font-bold transition-all ${
                    isActive
                      ? 'bg-red-50 dark:bg-red-950/40 text-red-600 dark:text-red-400 border border-red-200/60 dark:border-red-900/40 shadow-xs'
                      : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100/70 dark:hover:bg-gray-700/50'
                  }`
                }
              >
                <div className="flex items-center gap-3.5">
                  <div className="w-7 h-7 rounded-xl bg-gray-100 dark:bg-gray-700 flex items-center justify-center text-gray-600 dark:text-gray-300">
                    <svg className="w-4 h-4 text-amber-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth="2"
                        d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
                      />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    </svg>
                  </div>
                  <div>
                    <div className="leading-tight">Settings & Config</div>
                    <div className="text-[10px] text-gray-400 font-normal">Preferences & APIs</div>
                  </div>
                </div>
                <span className="text-[10px] px-2 py-0.5 rounded-full font-semibold bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400">
                  Config
                </span>
              </NavLink>
            </nav>
          </div>

          {/* Bottom System Status Widget */}
          <div className="pt-4 border-t border-gray-100 dark:border-gray-700/60">
            <div className="p-3.5 rounded-2xl bg-gray-50 dark:bg-gray-700/30 border border-gray-100 dark:border-gray-700/60">
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-[11px] font-bold text-gray-700 dark:text-gray-300">System Telemetry</span>
                <span className="flex items-center gap-1 text-[10px] font-bold text-emerald-600 dark:text-emerald-400">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                  Live
                </span>
              </div>
              <div className="text-[10px] text-gray-400 flex items-center justify-between">
                <span>FastAPI Engine</span>
                <span className="font-mono text-gray-600 dark:text-gray-400">Port 8000</span>
              </div>
              <div className="text-[10px] text-gray-400 flex items-center justify-between mt-0.5">
                <span>FIRMS / VIIRS</span>
                <span className="text-emerald-600 dark:text-emerald-400 font-semibold">Active</span>
              </div>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
};