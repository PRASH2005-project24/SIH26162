import React, { useState, useEffect } from 'react';
import './App.css';

function App() {
  const [backendStatus, setBackendStatus] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const checkBackend = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/v1/health');
        if (!response.ok) throw new Error('Backend unreachable');
        const data = await response.json();
        setBackendStatus(data);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    };

    checkBackend();
  }, []);

  return (
    <div className="App">
      <header className="App-header">
        <h1>🔥 SIH26162 Thermal Event Intelligence Platform</h1>
        <p>Stage 1A: FIRMS Ingestion &amp; Fusion</p>
      </header>

      <main>
        <section className="status-section">
          <h2>Backend Status</h2>
          {loading && <p>Loading...</p>}
          {error && <p className="error">❌ {error}</p>}
          {backendStatus && (
            <div className="status-box">
              <p>✓ Backend is running</p>
              <p>Version: {backendStatus.version}</p>
              <p>Database: {backendStatus.database.status}</p>
            </div>
          )}
        </section>

        <section className="placeholder-section">
          <h2>Map View (Coming Soon)</h2>
          <p>Thermal event map will be displayed here in Stage 1B with GIS enrichment.</p>
        </section>

        <section className="placeholder-section">
          <h2>Events (Coming Soon)</h2>
          <p>Recent thermal events list will be displayed here.</p>
        </section>
      </main>
    </div>
  );
}

export default App;
