/**
 * Connection Settings Component - Configure Trio server and credentials
 */

import React, { useEffect, useState } from 'react';
import { adminApi } from '../../services/adminApi';
import './ConnectionSettings.css';

const defaultForm = {
  base_url: '',
  username: '',
  password: '', // optional on update
  api_token: '',
  contact_center_id: '1',
};

export default function ConnectionSettings() {
  const [form, setForm] = useState(defaultForm);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [testResult, setTestResult] = useState(null);
  const [tokenSaved, setTokenSaved] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showToken, setShowToken] = useState(false);

  useEffect(() => {
    const load = async () => {
      try {
        setLoading(true);
        const data = await adminApi.getConnectionSettings();
        // Do not pre-fill sensitive values into inputs
        const savedToken = Boolean(data?.has_token);
        setTokenSaved(savedToken);
        setForm({
          ...defaultForm,
          ...data,
          api_token: '', // clear input even if token exists server-side
          password: '',
        });
      } catch (e) {
        setError('Kunde inte läsa anslutningsinställningar: ' + e.message);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const onChange = (key, value) => setForm(prev => ({ ...prev, [key]: value }));

  const isValid = () => {
    const base = (form.base_url || '').trim();
    const ccid = (form.contact_center_id || '').trim();
    const user = (form.username || '').trim();
    const pwd = (form.password || '').trim();
    const tok = (form.api_token || '').trim();
    if (!base || !ccid) return false;
    // Either token OR username+password must be present (on update, token may already be saved)
    const hasCreds = tok || (user && pwd) || tokenSaved;
    return Boolean(hasCreds);
  };

  const onSave = async (e) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    setSaving(true);
    try {
      const payload = { ...form };
      if (!payload.password) {
        delete payload.password; // do not overwrite if empty
      }
      if (!payload.api_token && tokenSaved) {
        // keep existing token if user left empty
        delete payload.api_token;
      }
      await adminApi.updateConnectionSettings(payload);
      setSuccess('Inställningar sparade.');
      if (payload.api_token) setTokenSaved(true);
      if (payload.api_token === '') setTokenSaved(false);
    } catch (e) {
      setError('Misslyckades att spara: ' + e.message);
    } finally {
      setSaving(false);
    }
  };

  const onTest = async () => {
    setTesting(true);
    setTestResult(null);
    setError(null);
    try {
      const res = await adminApi.testConnection();
      setTestResult(res.ok ? { ok: true, message: 'Anslutning OK' } : { ok: false, message: 'Anslutning misslyckades' });
    } catch (e) {
      setTestResult({ ok: false, message: 'Fel vid test: ' + e.message });
    } finally {
      setTesting(false);
    }
  };

  if (loading) {
    return (
      <div className="conn-settings">
        <div className="loading-container"><div className="spinner" /> Laddar...</div>
      </div>
    );
  }

  return (
    <div className="conn-settings">
      <div className="section-header">
        <h2><span className="icon">🔗</span> Trio Anslutning</h2>
        <p className="description">Konfigurera serveradress, inloggning och API-nyckel</p>
        <small style={{ color: '#666' }}>
          Autentisering: Om en API-nyckel finns används den i första hand. I andra hand används användarnamn + lösenord.
        </small>
      </div>

      {error && (
        <div className="error-message">
          <span className="error-icon">⚠️</span>
          {error}
          <button onClick={() => setError(null)} className="error-close">×</button>
        </div>
      )}
      {success && (
        <div className="success-message">
          <span className="success-icon">✅</span>
          {success}
          <button onClick={() => setSuccess(null)} className="success-close">×</button>
        </div>
      )}

      <form className="conn-form" onSubmit={onSave}>
        <div className="form-group">
          <label>Serveradress (bas-URL)</label>
          <input
            type="url"
            placeholder="https://trio.example.com/te/api"
            value={form.base_url}
            onChange={(e) => onChange('base_url', e.target.value)}
            required
          />
        </div>

        <div className="form-row">
          <div className="form-group">
            <label>Användarnamn (valfritt om API-nyckel används)</label>
            <input
              type="text"
              value={form.username}
              onChange={(e) => onChange('username', e.target.value)}
            />
          </div>
          <div className="form-group">
            <label>Lösenord (lämna tomt för att behålla)</label>
            <input
              type={showPassword ? 'text' : 'password'}
              value={form.password}
              onChange={(e) => onChange('password', e.target.value)}
            />
            <label style={{ display: 'flex', alignItems: 'center', gap: '.4rem' }}>
              <input type="checkbox" checked={showPassword} onChange={(e) => setShowPassword(e.target.checked)} /> Visa lösenord
            </label>
          </div>
        </div>

        <div className="form-group">
          <label>API-nyckel (Bearer token, valfritt)</label>
          {tokenSaved && !form.api_token && (
            <small style={{ color: '#666' }}>En token är redan sparad. Lämna tomt för att behålla, fyll i för att ersätta.</small>
          )}
          <input
            type={showToken ? 'text' : 'password'}
            value={form.api_token || ''}
            onChange={(e) => onChange('api_token', e.target.value)}
            placeholder={tokenSaved ? '•••••••• (sparad)' : 'Ex: eyJhbGciOi...'}
            autoComplete="off"
          />
          <label style={{ display: 'flex', alignItems: 'center', gap: '.4rem' }}>
            <input type="checkbox" checked={showToken} onChange={(e) => setShowToken(e.target.checked)} /> Visa token
          </label>
        </div>

        <div className="form-group">
          <label>Contact Center ID</label>
          <input
            type="text"
            value={form.contact_center_id}
            onChange={(e) => onChange('contact_center_id', e.target.value)}
            required
          />
        </div>

        {!isValid() && (
          <div className="error-message" style={{ marginTop: '.25rem' }}>
            <span className="error-icon">⚠️</span>
            Ange bas-URL och antingen API-nyckel eller användarnamn + lösenord.
          </div>
        )}

        <div className="form-actions">
          <button type="button" className="secondary" onClick={onTest} disabled={testing}>
            {testing ? 'Testar...' : 'Testa anslutning'}
          </button>
          {testResult && (
            <span className={`test-result ${testResult.ok ? 'ok' : 'fail'}`}>
              {testResult.message}
            </span>
          )}
          <div className="flex-spacer" />
          <button type="submit" className="primary" disabled={saving || !isValid()}>
            {saving ? 'Sparar...' : 'Spara inställningar'}
          </button>
        </div>
      </form>
    </div>
  );
}
