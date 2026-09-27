import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { lazy, Suspense } from 'react';
import { Layout } from './components/layout/Layout';
import { ThemeProvider } from './context/ThemeContext';
import { LocaleProvider } from './context/LocaleContext';
import { FiltersProvider } from './hooks/useFilters';

import { SelectedEventProvider } from './context/SelectedEventContext';

const Dashboard = lazy(() => import('./pages/Dashboard').then((module) => ({ default: module.Dashboard })));
const LiveEvents = lazy(() => import('./pages/LiveEvents').then((module) => ({ default: module.LiveEvents })));
const HistoricalEvents = lazy(() => import('./pages/HistoricalEvents').then((module) => ({ default: module.HistoricalEvents })));
const Analytics = lazy(() => import('./pages/Analytics').then((module) => ({ default: module.Analytics })));
const Settings = lazy(() => import('./pages/Settings').then((module) => ({ default: module.Settings })));

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <LocaleProvider>
          <FiltersProvider>
            <SelectedEventProvider>
              <BrowserRouter>
                <Layout>
                  <Suspense
                    fallback={(
                      <div className="flex h-full min-h-0 items-center justify-center bg-gray-50 text-sm text-gray-500 dark:bg-gray-900 dark:text-gray-400">
                        <span role="status" aria-live="polite">Loading page...</span>
                      </div>
                    )}
                  >
                    <Routes>
                      <Route path="/" element={<Dashboard />} />
                      <Route path="/live-events" element={<LiveEvents />} />
                      <Route path="/historical-events" element={<HistoricalEvents />} />
                      <Route path="/analytics" element={<Analytics />} />
                      <Route path="/settings" element={<Settings />} />
                      <Route path="*" element={<Navigate to="/" replace />} />
                    </Routes>
                  </Suspense>
                </Layout>
              </BrowserRouter>
            </SelectedEventProvider>
          </FiltersProvider>
        </LocaleProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;