import React from 'react';
import Upload from '../components/Upload';
import FileList from '../components/FileList';
import { authApi } from '../services/api';

export const Home = () => {
  const [refreshKey, setRefreshKey] = React.useState(0);

  const handleLogout = async () => {
    const refreshToken = localStorage.getItem('refresh_token');

    try {
      if (refreshToken) {
        await authApi.logout(refreshToken);
      }
    } catch {
      // Keep local logout resilient even if the API is unavailable.
    } finally {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      window.location.href = '/login';
    }
  };

  return (
    <main className="dashboard-shell">
      <div className="dashboard-header">
        <div>
          <span className="eyebrow">Document workspace</span>
          <h1>Link1Die Dashboard</h1>
          <p>Upload files, manage your library, and send expiring share links.</p>
        </div>
        <button onClick={handleLogout} className="secondary-button">
          Logout
        </button>
      </div>

      <section className="dashboard-grid">
        <Upload onUploadSuccess={() => setRefreshKey((prev) => prev + 1)} />
        <FileList key={refreshKey} />
      </section>
    </main>
  );
};

export default Home;
