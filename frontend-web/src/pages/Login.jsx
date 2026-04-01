import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { authApi, getApiErrorMessage } from '../services/api';

export const Login = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!username.trim() || !password) {
      setError('Please enter both username and password.');
      return;
    }

    setLoading(true);
    try {
      const response = await authApi.login(username, password);
      localStorage.setItem('access_token', response.data.access_token);
      localStorage.setItem('refresh_token', response.data.refresh_token);
      navigate('/');
    } catch (err) {
      setError(getApiErrorMessage(err, 'Login failed'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="login-shell">
      <section className="login-hero">
        <div className="hero-copy">
          <span className="eyebrow">Secure document access</span>
          <h1>Link1Die</h1>
          <p>
            Manage uploads, generate short-lived share links, and keep internal
            files in one clean workspace.
          </p>
          <div className="hero-points">
            <div>
              <strong>Fast login</strong>
              <span>JWT auth with refresh token support</span>
            </div>
            <div>
              <strong>Simple sharing</strong>
              <span>Create expiring links for one or many files</span>
            </div>
            <div>
              <strong>Better visibility</strong>
              <span>Cleaner dashboard on desktop and mobile</span>
            </div>
          </div>
        </div>

        <div className="login-card">
          <div className="card-header">
            <span className="card-badge">Workspace Login</span>
            <h2>Sign in to continue</h2>
            <p>Use the same credentials defined in the backend user table.</p>
          </div>

          <form onSubmit={handleSubmit} className="auth-form">
            {error && <div className="form-error">{error}</div>}

            <label className="field">
              <span>Username or email</span>
              <input
                type="text"
                placeholder="user@example.com"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                autoComplete="username"
              />
            </label>

            <label className="field">
              <span>Password</span>
              <input
                type="password"
                placeholder="Enter your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="current-password"
              />
            </label>

            <button type="submit" disabled={loading} className="primary-button">
              {loading ? 'Signing in...' : 'Login'}
            </button>
          </form>

          <p className="login-hint">
            Default local API: <code>http://localhost:8000/api/v1</code>
          </p>
        </div>
      </section>
    </main>
  );
};

export default Login;
