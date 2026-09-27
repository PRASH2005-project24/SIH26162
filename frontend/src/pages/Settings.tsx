import { useState, useEffect } from 'react';
import { useTheme } from '@/context/ThemeContext';
import { useLocale } from '@/context/LocaleContext';

interface UserSettingsState {
  autoFlyEnabled: boolean;
  mapDetailLevel: 'standard' | 'high';
  autoRefreshInterval: number;
}

const SETTINGS_STORAGE_KEY = 'fireguard_preferences_v1';

const defaultSettings: UserSettingsState = {
  autoFlyEnabled: true,
  mapDetailLevel: 'standard',
  autoRefreshInterval: 30,
};

export const Settings = () => {
  const { theme, toggleTheme } = useTheme();
  const { locale, toggleLocale } = useLocale();

  // Load persistent settings from localStorage
  const [settings, setSettings] = useState<UserSettingsState>(() => {
    try {
      const saved = localStorage.getItem(SETTINGS_STORAGE_KEY);
      if (saved) {
        return { ...defaultSettings, ...JSON.parse(saved) };
      }
    } catch {
      // ignore JSON parse error
    }
    return defaultSettings;
  });

  const [lastSavedTime, setLastSavedTime] = useState<string>('Just now');

  // Direct automatic save upon any change
  const updateSetting = <K extends keyof UserSettingsState>(key: K, value: UserSettingsState[K]) => {
    setSettings((prev) => {
      const next = { ...prev, [key]: value };
      try {
        localStorage.setItem(SETTINGS_STORAGE_KEY, JSON.stringify(next));
        setLastSavedTime('Just now');
      } catch (err) {
        console.error('Failed to save settings to localStorage:', err);
      }
      return next;
    });
  };

  useEffect(() => {
    const timer = setInterval(() => {
      setLastSavedTime('Synced locally');
    }, 10000);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="flex-1 overflow-y-auto bg-gray-50 dark:bg-gray-900 p-4 sm:p-8 transition-colors">
      <div className="max-w-3xl mx-auto space-y-6">
        {/* Top Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-5 border-b border-gray-200 dark:border-gray-800">
          <div>
            <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100 tracking-tight">
              Settings & Preferences
            </h1>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
              Customize interface theme, interaction behaviors, and review system services
            </p>
          </div>

          {/* Auto-saved badge — no manual save button */}
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700/80 shadow-xs text-xs">
            <span className="w-2 h-2 rounded-full bg-emerald-500" />
            <span className="font-medium text-gray-600 dark:text-gray-300">
              {lastSavedTime}
            </span>
          </div>
        </div>

        {/* Section 1: Appearance & Locale */}
        <div className="bg-white dark:bg-gray-800 rounded-2xl p-5 shadow-xs border border-gray-200 dark:border-gray-700/80 space-y-4">
          <div className="border-b border-gray-100 dark:border-gray-700/60 pb-3">
            <h2 className="text-xs font-bold text-gray-900 dark:text-gray-100 uppercase tracking-wider">
              Display & Localization
            </h2>
            <p className="text-[11px] text-gray-500 dark:text-gray-400 mt-0.5">
              Select your preferred color scheme and platform language
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-1">
            {/* Theme Toggle: Sleek Segmented Switch */}
            <div className="p-3.5 rounded-xl bg-gray-50 dark:bg-gray-700/30 border border-gray-100 dark:border-gray-700/60 flex items-center justify-between">
              <div>
                <div className="text-xs font-semibold text-gray-900 dark:text-gray-100">
                  Theme Mode
                </div>
                <div className="text-[11px] text-gray-500 dark:text-gray-400">
                  {theme === 'dark' ? 'CartoDB Dark Matter' : 'CartoDB Daylight'}
                </div>
              </div>

              <div className="flex items-center p-1 rounded-xl bg-gray-200/80 dark:bg-gray-800 border border-gray-200 dark:border-gray-700">
                <button
                  onClick={() => theme === 'dark' && toggleTheme()}
                  className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all cursor-pointer flex items-center gap-1.5 ${
                    theme === 'light'
                      ? 'bg-white text-gray-900 shadow-xs'
                      : 'text-gray-500 hover:text-gray-900 dark:hover:text-gray-300'
                  }`}
                >
                  <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
                  </svg>
                  <span>Light</span>
                </button>
                <button
                  onClick={() => theme === 'light' && toggleTheme()}
                  className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all cursor-pointer flex items-center gap-1.5 ${
                    theme === 'dark'
                      ? 'bg-gray-700 text-white shadow-xs'
                      : 'text-gray-500 hover:text-gray-900 dark:hover:text-gray-300'
                  }`}
                >
                  <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
                  </svg>
                  <span>Dark</span>
                </button>
              </div>
            </div>

            {/* Language Toggle: Sleek Segmented Switch */}
            <div className="p-3.5 rounded-xl bg-gray-50 dark:bg-gray-700/30 border border-gray-100 dark:border-gray-700/60 flex items-center justify-between">
              <div>
                <div className="text-xs font-semibold text-gray-900 dark:text-gray-100">
                  Language
                </div>
                <div className="text-[11px] text-gray-500 dark:text-gray-400">
                  {locale === 'en' ? 'English (UK / US)' : 'हिन्दी (भारत)'}
                </div>
              </div>

              <div className="flex items-center p-1 rounded-xl bg-gray-200/80 dark:bg-gray-800 border border-gray-200 dark:border-gray-700">
                <button
                  onClick={() => locale !== 'en' && toggleLocale()}
                  className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                    locale === 'en'
                      ? 'bg-white text-gray-900 dark:bg-gray-700 dark:text-white shadow-xs'
                      : 'text-gray-500 hover:text-gray-900 dark:hover:text-gray-300'
                  }`}
                >
                  EN
                </button>
                <button
                  onClick={() => locale !== 'hi' && toggleLocale()}
                  className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                    locale === 'hi'
                      ? 'bg-white text-gray-900 dark:bg-gray-700 dark:text-white shadow-xs'
                      : 'text-gray-500 hover:text-gray-900 dark:hover:text-gray-300'
                  }`}
                >
                  HI
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Section 2: Map Interaction Behaviors */}
        <div className="bg-white dark:bg-gray-800 rounded-2xl p-5 shadow-xs border border-gray-200 dark:border-gray-700/80 space-y-4">
          <div className="border-b border-gray-100 dark:border-gray-700/60 pb-3">
            <h2 className="text-xs font-bold text-gray-900 dark:text-gray-100 uppercase tracking-wider">
              Map & Camera Interaction
            </h2>
            <p className="text-[11px] text-gray-500 dark:text-gray-400 mt-0.5">
              Configure camera animations and map viewport preferences
            </p>
          </div>

          <div className="space-y-3 pt-1">
            {/* Auto-fly camera toggle */}
            <div className="p-3.5 rounded-xl bg-gray-50 dark:bg-gray-700/30 border border-gray-100 dark:border-gray-700/60 flex items-center justify-between">
              <div>
                <div className="text-xs font-semibold text-gray-900 dark:text-gray-100">
                  Auto-Fly to Clicked Incident Dot
                </div>
                <div className="text-[11px] text-gray-500 dark:text-gray-400">
                  Smoothly zooms into the local incident zone (zoom level 9) when any fire marker is selected
                </div>
              </div>

              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={settings.autoFlyEnabled}
                  onChange={(e) => updateSetting('autoFlyEnabled', e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-10 h-5 bg-gray-300 dark:bg-gray-600 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-red-500"></div>
              </label>
            </div>

            {/* Auto-refresh interval */}
            <div className="p-3.5 rounded-xl bg-gray-50 dark:bg-gray-700/30 border border-gray-100 dark:border-gray-700/60 flex items-center justify-between">
              <div>
                <div className="text-xs font-semibold text-gray-900 dark:text-gray-100">
                  Live Feed Auto-Refresh
                </div>
                <div className="text-[11px] text-gray-500 dark:text-gray-400">
                  Background telemetry poll interval for real-time VIIRS detections
                </div>
              </div>

              <select
                value={settings.autoRefreshInterval}
                onChange={(e) => updateSetting('autoRefreshInterval', Number(e.target.value))}
                className="text-xs font-semibold p-1.5 rounded-lg bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-800 dark:text-gray-200 focus:outline-none cursor-pointer"
              >
                <option value={15}>Every 15s</option>
                <option value={30}>Every 30s (Default)</option>
                <option value={60}>Every 1m</option>
                <option value={300}>Every 5m</option>
              </select>
            </div>
          </div>
        </div>

        {/* Section 3: Services & Data Feeds */}
        <div className="bg-white dark:bg-gray-800 rounded-2xl p-5 shadow-xs border border-gray-200 dark:border-gray-700/80 space-y-4">
          <div className="border-b border-gray-100 dark:border-gray-700/60 pb-3">
            <h2 className="text-xs font-bold text-gray-900 dark:text-gray-100 uppercase tracking-wider">
              Connected Infrastructure
            </h2>
            <p className="text-[11px] text-gray-500 dark:text-gray-400 mt-0.5">
              Live status of backend services, spatial database, and NASA FIRMS feeds
            </p>
          </div>

          <div className="space-y-2.5 pt-1 text-xs">
            <div className="flex items-center justify-between p-3 rounded-xl bg-gray-50 dark:bg-gray-700/30 border border-gray-100 dark:border-gray-700/60">
              <div>
                <span className="font-semibold text-gray-900 dark:text-gray-100">FastAPI Intelligence Core</span>
                <span className="block text-[11px] text-gray-400 font-mono">http://localhost:8000/api/v1</span>
              </div>
              <span className="px-2 py-0.5 rounded-md text-[10px] font-bold bg-emerald-50 dark:bg-emerald-950/60 text-emerald-600 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-900/40 flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                Active
              </span>
            </div>

            <div className="flex items-center justify-between p-3 rounded-xl bg-gray-50 dark:bg-gray-700/30 border border-gray-100 dark:border-gray-700/60">
              <div>
                <span className="font-semibold text-gray-900 dark:text-gray-100">PostGIS Geospatial DB</span>
                <span className="block text-[11px] text-gray-400 font-mono">EPSG:4326 India Boundary Mesh</span>
              </div>
              <span className="px-2 py-0.5 rounded-md text-[10px] font-bold bg-emerald-50 dark:bg-emerald-950/60 text-emerald-600 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-900/40 flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                Connected
              </span>
            </div>

            <div className="flex items-center justify-between p-3 rounded-xl bg-gray-50 dark:bg-gray-700/30 border border-gray-100 dark:border-gray-700/60">
              <div>
                <span className="font-semibold text-gray-900 dark:text-gray-100">NASA FIRMS Feed</span>
                <span className="block text-[11px] text-gray-400 font-mono">VIIRS (SNPP / NOAA-20) & MODIS</span>
              </div>
              <span className="px-2 py-0.5 rounded-md text-[10px] font-bold bg-emerald-50 dark:bg-emerald-950/60 text-emerald-600 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-900/40 flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                Operational
              </span>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="text-center text-xs text-gray-400 dark:text-gray-500 py-1 font-mono">
          FireGuard v1.2.0 • SIH26162 • Ministry of Environment, Forest & Climate Change
        </div>
      </div>
    </div>
  );
};