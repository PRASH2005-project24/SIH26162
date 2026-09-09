import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Layout } from './components/layout/Layout';
import { Dashboard } from './pages/Dashboard';
import { LiveEvents } from './pages/LiveEvents';
import { HistoricalEvents } from './pages/HistoricalEvents';
import { Analytics } from './pages/Analytics';
import { Settings } from './pages/Settings';
import { ThemeProvider } from './context/ThemeContext';
import { LocaleProvider } from './context/LocaleContext';
import { FiltersProvider } from './hooks/useFilters';

import { SelectedEventProvider } from './context/SelectedEventContext';

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
                  <Routes>
                    <Route path="/" element={<Dashboard />} />
                    <Route path="/live-events" element={<LiveEvents />} />
                    <Route path="/historical-events" element={<HistoricalEvents />} />
                    <Route path="/analytics" element={<Analytics />} />
                    <Route path="/settings" element={<Settings />} />
                    <Route path="*" element={<Navigate to="/" replace />} />
                  </Routes>
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