import { useTheme } from '@/context/ThemeContext';
import { useLocale } from '@/context/LocaleContext';

export const Settings = () => {
  const { theme, toggleTheme } = useTheme();
  const { locale, toggleLocale, t } = useLocale();

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">{t('settings')}</h1>

      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6 mb-6">
        <h2 className="text-lg font-medium mb-4">{t('theme')}</h2>
        <div className="flex items-center space-x-4">
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
            {theme === 'light' ? '☀️ Light' : '🌙 Dark'}
          </span>
          <button
            onClick={toggleTheme}
            className="ml-2 h-8 w-12 flex items-center justify-center rounded border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700"
          >
            <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M20.354 15.354A9 9 0 018.646 3.646M9.75 9.75v4.5m4.5-4.5H9.75m0 0L12 6m0 0l2.25 2.25" />
            </svg>
          </button>
        </div>
      </div>

      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6 mb-6">
        <h2 className="text-lg font-medium mb-4">{t('language')}</h2>
        <div className="flex items-center space-x-4">
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
            {locale === 'en' ? 'English' : 'Hindi'}
          </span>
          <button
            onClick={toggleLocale}
            className="ml-2 h-8 w-12 flex items-center justify-center rounded border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700"
          >
            <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 10h18M7 15h10m0 0l-3-3m3 3l3-3" />
            </svg>
          </button>
        </div>
      </div>

      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
        <h2 className="text-lg font-medium mb-4">Map Preferences</h2>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          Map preferences will be implemented in a future update.
        </p>
      </div>
    </div>
  );
};