/**
 * Service Configuration Component - Manage monitored services and SLA settings
 */

import React, { useState, useEffect } from 'react';
import { adminApi } from '../../services/adminApi';
import './ServiceConfiguration.css';

const ServiceConfiguration = () => {
  const [monitoredServices, setMonitoredServices] = useState([]);
  const [availableServices, setAvailableServices] = useState([]);
  const [monitoredUsers, setMonitoredUsers] = useState([]);
  const [availableUsers, setAvailableUsers] = useState([]);
  const [timeWindows, setTimeWindows] = useState([]);
  const [connectionSettings, setConnectionSettings] = useState({ base_url: '', username: '', password: '', api_token: '', contact_center_id: '1', has_token: false });
  const [themeSchedules, setThemeSchedules] = useState([]);
  const [themeSettings, setThemeSettings] = useState([]); // list of ThemeSettings for both LIGHT/DARK
  const [themeStatus, setThemeStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showAddService, setShowAddService] = useState(false);
  const [editingService, setEditingService] = useState(null);

  // Form state for adding/editing services
  const [serviceForm, setServiceForm] = useState({
    trio_service_id: '',
    service_name: '',
    sla_target_seconds: 20,
    warning_threshold_seconds: 15,
    is_active: true
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [monitored, available, mUsers, aUsers, windows, conn, sched, tSettings, tStatus] = await Promise.all([
        adminApi.getMonitoredServices(),
        adminApi.getAvailableServices(),
        adminApi.getMonitoredUsers(),
        adminApi.getAvailableUsers(),
        adminApi.getTimeWindows(),
        adminApi.getConnectionSettings(),
        adminApi.getThemeSchedules(),
        adminApi.getThemeSettings(),
        adminApi.getThemeStatus(),
      ]);
      setMonitoredServices(monitored);
      setAvailableServices(available);
      setMonitoredUsers(mUsers);
      setAvailableUsers(aUsers);
      setTimeWindows(windows);
      setConnectionSettings(conn);
      setThemeSchedules(sched);
      setThemeSettings(tSettings);
      setThemeStatus(tStatus);
    } catch (err) {
      setError('Kunde inte ladda tjänstedata: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleAddService = (service) => {
    setServiceForm({
      trio_service_id: service.id,
      service_name: service.name,
      sla_target_seconds: 20,
      warning_threshold_seconds: 15,
      is_active: true
    });
    setShowAddService(true);
  };

  const handleEditService = (service) => {
    setServiceForm({
      trio_service_id: service.trio_service_id,
      service_name: service.service_name,
      sla_target_seconds: service.sla_target_seconds,
      warning_threshold_seconds: service.warning_threshold_seconds,
      is_active: service.is_active
    });
    setEditingService(service);
    setShowAddService(true);
  };

  const handleSubmitService = async (e) => {
    e.preventDefault();
    try {
      if (editingService) {
        await adminApi.updateMonitoredService(editingService.id, serviceForm);
      } else {
        await adminApi.addMonitoredService(serviceForm);
      }
      setShowAddService(false);
      setEditingService(null);
      loadData();
    } catch (err) {
      setError('Kunde inte spara tjänst: ' + err.message);
    }
  };

  const handleRemoveService = async (serviceId) => {
    if (window.confirm('Är du säker på att du vill ta bort denna tjänst från övervakning?')) {
      try {
        await adminApi.removeMonitoredService(serviceId);
        loadData();
      } catch (err) {
        setError('Kunde inte ta bort tjänst: ' + err.message);
      }
    }
  };

  const handleToggleActive = async (service) => {
    try {
      await adminApi.updateMonitoredService(service.id, {
        ...service,
        is_active: !service.is_active
      });
      loadData();
    } catch (err) {
      setError('Kunde inte uppdatera tjänst: ' + err.message);
    }
  };

  const resetForm = () => {
    setServiceForm({
      trio_service_id: '',
      service_name: '',
      sla_target_seconds: 20,
      warning_threshold_seconds: 15,
      is_active: true
    });
    setShowAddService(false);
    setEditingService(null);
  };

  // ===== Connection Settings =====
  const [connSaving, setConnSaving] = useState(false);
  const [connTesting, setConnTesting] = useState(false);
  const saveConnection = async (e) => {
    e.preventDefault();
    setConnSaving(true);
    try {
      const toSave = { ...connectionSettings };
      if (!toSave.password) delete toSave.password; // optional
      const saved = await adminApi.updateConnectionSettings(toSave);
      setConnectionSettings(saved);
    } catch (err) {
      setError('Kunde inte spara anslutningsinställningar: ' + err.message);
    } finally {
      setConnSaving(false);
    }
  };
  const testConnection = async () => {
    setConnTesting(true);
    try {
      const res = await adminApi.testConnection();
      alert(res.ok ? 'Anslutningen lyckades' : 'Anslutningen misslyckades');
    } catch (err) {
      alert('Test misslyckades: ' + err.message);
    } finally {
      setConnTesting(false);
    }
  };

  // ===== Time Windows =====
  const addTimeWindow = () => {
    setTimeWindows([...timeWindows, { name: 'Ny period', start_time: '07:00', end_time: '21:00', weekdays: [1,2,3,4,5], is_active: true }]);
  };
  const updateTimeWindowField = (idx, field, value) => {
    const copy = [...timeWindows];
    copy[idx] = { ...copy[idx], [field]: value };
    setTimeWindows(copy);
  };
  const saveTimeWindows = async () => {
    try {
      const saved = await adminApi.updateTimeWindows(timeWindows);
      setTimeWindows(saved);
    } catch (err) {
      setError('Kunde inte spara tidsfönster: ' + err.message);
    }
  };

  // ===== Theme Schedule / Settings =====
  const addThemeSchedule = () => {
    setThemeSchedules([...themeSchedules, { name: 'Ny schema', theme_type: 'light', start_time: '07:00', end_time: '21:00', weekdays: [1,2,3,4,5], is_active: true }]);
  };
  const updateThemeScheduleField = (idx, field, value) => {
    const copy = [...themeSchedules];
    copy[idx] = { ...copy[idx], [field]: value };
    setThemeSchedules(copy);
  };
  const saveThemeSchedules = async () => {
    try {
      const saved = await adminApi.updateThemeSchedules(themeSchedules);
      setThemeSchedules(saved);
    } catch (err) {
      setError('Kunde inte spara temascheman: ' + err.message);
    }
  };
  const setManualTheme = async (theme) => {
    try {
      await adminApi.setManualThemeOverride(theme);
      const status = await adminApi.getThemeStatus();
      setThemeStatus(status);
    } catch (err) {
      setError('Kunde inte sätta manuellt tema: ' + err.message);
    }
  };
  const clearManualTheme = async () => {
    try {
      await adminApi.clearManualOverride();
      const status = await adminApi.getThemeStatus();
      setThemeStatus(status);
    } catch (err) {
      setError('Kunde inte rensa manuellt tema: ' + err.message);
    }
  };
  const updateThemeSettingField = (idx, field, value) => {
    const copy = [...themeSettings];
    copy[idx] = { ...copy[idx], [field]: value };
    setThemeSettings(copy);
  };
  const saveThemeSetting = async (idx) => {
    try {
      const saved = await adminApi.updateThemeSettings(themeSettings[idx]);
      const next = [...themeSettings];
      next[idx] = saved;
      setThemeSettings(next);
    } catch (err) {
      setError('Kunde inte spara temainställningar: ' + err.message);
    }
  };

  // ===== Monitored Users =====
  const addMonitoredUser = async (user) => {
    try {
      await adminApi.addMonitoredUser({ trio_user_id: user.id, user_name: user.name, display_name: user.display_name || user.name, is_active: true });
      const updated = await adminApi.getMonitoredUsers();
      setMonitoredUsers(updated);
    } catch (err) {
      setError('Kunde inte lägga till användare: ' + err.message);
    }
  };
  const toggleUserActive = async (user) => {
    try {
      await adminApi.updateMonitoredUser(user.id, { ...user, is_active: !user.is_active });
      const updated = await adminApi.getMonitoredUsers();
      setMonitoredUsers(updated);
    } catch (err) {
      setError('Kunde inte uppdatera användare: ' + err.message);
    }
  };
  const removeMonitoredUser = async (userId) => {
    if (window.confirm('Ta bort denna användare från övervakning?')) {
      try {
        await adminApi.removeMonitoredUser(userId);
        const updated = await adminApi.getMonitoredUsers();
        setMonitoredUsers(updated);
      } catch (err) {
        setError('Kunde inte ta bort användare: ' + err.message);
      }
    }
  };

  const getStatusIcon = (isActive) => isActive ? '✓' : '✗';
  const getStatusClass = (isActive) => isActive ? 'active' : 'inactive';

  if (loading) {
    return (
      <div className="service-config">
        <div className="loading-container">
          <div className="spinner"></div>
          <p>Laddar tjänstedata...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="service-config">
      <div className="section-header">
        <h2>
          <span className="icon">📋</span>
          Övervakade Tjänster & Köer
        </h2>
        <p className="description">
          Konfigurera vilka tjänster som ska övervakas och deras SLA-nivåer
        </p>
      </div>

      {error && (
        <div className="error-message">
          <span className="error-icon">⚠️</span>
          {error}
          <button onClick={() => setError(null)} className="error-close">×</button>
        </div>
      )}

      {/* Monitored Services List */}
      <div className="monitored-services">
        <div className="section-title">
          <h3>Aktiva Övervakningar</h3>
          <span className="count">({monitoredServices.length} tjänster)</span>
        </div>

        {monitoredServices.length === 0 ? (
          <div className="empty-state">
            <span className="empty-icon">📋</span>
            <h4>Inga tjänster konfigurerade</h4>
            <p>Lägg till tjänster från listan nedan för att börja övervaka</p>
          </div>
        ) : (
          <div className="services-grid">
            {monitoredServices.map(service => (
              <div key={service.id} className={`service-card ${getStatusClass(service.is_active)}`}>
                <div className="service-header">
                  <div className="service-title">
                    <span className={`status-indicator ${getStatusClass(service.is_active)}`}>
                      {getStatusIcon(service.is_active)}
                    </span>
                    <h4>{service.service_name}</h4>
                  </div>
                  <div className="service-actions">
                    <button 
                      onClick={() => handleToggleActive(service)}
                      className={`toggle-btn ${getStatusClass(service.is_active)}`}
                      title={service.is_active ? 'Inaktivera' : 'Aktivera'}
                    >
                      {service.is_active ? '👁️' : '🚫'}
                    </button>
                    <button 
                      onClick={() => handleEditService(service)}
                      className="edit-btn"
                      title="Redigera"
                    >
                      ✏️
                    </button>
                    <button 
                      onClick={() => handleRemoveService(service.id)}
                      className="remove-btn"
                      title="Ta bort"
                    >
                      🗑️
                    </button>
                  </div>
                </div>
                
                <div className="service-details">
                  <div className="sla-info">
                    <div className="sla-item">
                      <span className="sla-label">SLA Mål:</span>
                      <span className="sla-value">{service.sla_target_seconds}s</span>
                    </div>
                    <div className="sla-item">
                      <span className="sla-label">Varning:</span>
                      <span className="sla-value warning">{service.warning_threshold_seconds}s</span>
                    </div>
                  </div>
                  <div className="service-id">
                    ID: {service.trio_service_id}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Available Services */}
      <div className="available-services">
        <div className="section-title">
          <h3>Tillgängliga Tjänster från Trio</h3>
          <span className="count">({availableServices.length} tillgängliga)</span>
        </div>

        {availableServices.length === 0 ? (
          <div className="empty-state">
            <span className="empty-icon">🔌</span>
            <h4>Inga tjänster tillgängliga</h4>
            <p>Kontrollera anslutningen till Trio API</p>
          </div>
        ) : (
          <div className="available-grid">
            {availableServices
              .filter(service => !monitoredServices.some(m => m.trio_service_id === service.id))
              .map(service => (
                <div key={service.id} className="available-card">
                  <div className="available-info">
                    <h4>{service.name}</h4>
                    {service.description && (
                      <p className="service-description">{service.description}</p>
                    )}
                    <div className="service-meta">
                      ID: {service.id} | Status: {service.is_active ? 'Aktiv' : 'Inaktiv'}
                    </div>
                  </div>
                  <button 
                    onClick={() => handleAddService(service)}
                    className="add-service-btn"
                    disabled={!service.is_active}
                  >
                    <span>+</span> Lägg till
                  </button>
                </div>
              ))}
          </div>
        )}
      </div>

      {/* Add/Edit Service Modal */}
      {showAddService && (
        <div className="modal-overlay" onClick={resetForm}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>
                {editingService ? 'Redigera Tjänst' : 'Lägg till Tjänst'}
              </h3>
              <button onClick={resetForm} className="modal-close">×</button>
            </div>

            <form onSubmit={handleSubmitService} className="service-form">
              <div className="form-group">
                <label>Tjänstnamn:</label>
                <input
                  type="text"
                  value={serviceForm.service_name}
                  onChange={(e) => setServiceForm({...serviceForm, service_name: e.target.value})}
                  required
                />
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>SLA Mål (sekunder):</label>
                  <input
                    type="number"
                    min="1"
                    max="300"
                    value={serviceForm.sla_target_seconds}
                    onChange={(e) => setServiceForm({...serviceForm, sla_target_seconds: parseInt(e.target.value)})}
                    required
                  />
                </div>

                <div className="form-group">
                  <label>Varningsgräns (sekunder):</label>
                  <input
                    type="number"
                    min="1"
                    max="300"
                    value={serviceForm.warning_threshold_seconds}
                    onChange={(e) => setServiceForm({...serviceForm, warning_threshold_seconds: parseInt(e.target.value)})}
                    required
                  />
                </div>
              </div>

              <div className="form-group">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={serviceForm.is_active}
                    onChange={(e) => setServiceForm({...serviceForm, is_active: e.target.checked})}
                  />
                  <span className="checkmark"></span>
                  Aktivera övervakning
                </label>
              </div>

              <div className="form-actions">
                <button type="button" onClick={resetForm} className="cancel-btn">
                  Avbryt
                </button>
                <button type="submit" className="save-btn">
                  {editingService ? 'Uppdatera' : 'Lägg till'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Connection Settings */}
      <div className="section-header" style={{ marginTop: '2rem' }}>
        <h2>
          <span className="icon">🔗</span>
          Anslutningsinställningar (Trio)
        </h2>
        <p className="description">Server-URL och autentisering. Lösenord uppdateras endast om ifyllt.</p>
      </div>
      <form onSubmit={saveConnection} className="service-form" style={{ maxWidth: 720 }}>
        <div className="form-group">
          <label>Bas-URL</label>
          <input type="text" value={connectionSettings.base_url || ''} onChange={(e)=>setConnectionSettings({...connectionSettings, base_url: e.target.value})} required />
        </div>
        <div className="form-row">
          <div className="form-group">
            <label>Användarnamn</label>
            <input type="text" value={connectionSettings.username || ''} onChange={(e)=>setConnectionSettings({...connectionSettings, username: e.target.value})} />
          </div>
          <div className="form-group">
            <label>Lösenord</label>
            <input type="password" placeholder={connectionSettings.has_token ? '••••••' : ''} value={connectionSettings.password || ''} onChange={(e)=>setConnectionSettings({...connectionSettings, password: e.target.value})} />
          </div>
        </div>
        <div className="form-row">
          <div className="form-group">
            <label>API-token</label>
            <input type="text" value={connectionSettings.api_token || ''} onChange={(e)=>setConnectionSettings({...connectionSettings, api_token: e.target.value})} />
          </div>
          <div className="form-group">
            <label>Contact Center ID</label>
            <input type="text" value={connectionSettings.contact_center_id || ''} onChange={(e)=>setConnectionSettings({...connectionSettings, contact_center_id: e.target.value})} />
          </div>
        </div>
        <div className="form-actions">
          <button type="button" onClick={testConnection} className="save-btn" disabled={connTesting}>
            {connTesting ? 'Testar...' : 'Testa anslutning'}
          </button>
          <button type="submit" className="save-btn" disabled={connSaving}>
            {connSaving ? 'Sparar...' : 'Spara inställningar'}
          </button>
        </div>
      </form>

      {/* Time Windows */}
      <div className="section-header" style={{ marginTop: '2rem' }}>
        <h2>
          <span className="icon">⏱️</span>
          Tidsfönster (Mätperioder)
        </h2>
        <p className="description">Vardagar 07:00-21:00, helger 09:00-16:00 som standard.</p>
      </div>
      <div className="available-grid">
        {timeWindows.map((w, idx) => (
          <div key={idx} className="available-card" style={{ alignItems: 'stretch' }}>
            <div className="available-info" style={{ width: '100%' }}>
              <div className="form-row">
                <div className="form-group">
                  <label>Namn</label>
                  <input type="text" value={w.name || ''} onChange={(e)=>updateTimeWindowField(idx, 'name', e.target.value)} />
                </div>
                <div className="form-group">
                  <label>Start</label>
                  <input type="time" value={w.start_time} onChange={(e)=>updateTimeWindowField(idx, 'start_time', e.target.value)} />
                </div>
                <div className="form-group">
                  <label>Slut</label>
                  <input type="time" value={w.end_time} onChange={(e)=>updateTimeWindowField(idx, 'end_time', e.target.value)} />
                </div>
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>Veckodagar (1-7, kommaseparerat)</label>
                  <input type="text" value={(w.weekdays||[]).join(',')} onChange={(e)=>updateTimeWindowField(idx, 'weekdays', e.target.value.split(',').map(v=>parseInt(v.trim())).filter(Boolean))} />
                </div>
                <div className="form-group">
                  <label className="checkbox-label">
                    <input type="checkbox" checked={!!w.is_active} onChange={(e)=>updateTimeWindowField(idx, 'is_active', e.target.checked)} />
                    <span className="checkmark"></span>
                    Aktiv
                  </label>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
      <div className="form-actions">
        <button className="save-btn" type="button" onClick={addTimeWindow}>+ Lägg till period</button>
        <button className="save-btn" type="button" onClick={saveTimeWindows}>Spara tidsfönster</button>
      </div>

      {/* Theme Schedule and Override */}
      <div className="section-header" style={{ marginTop: '2rem' }}>
        <h2>
          <span className="icon">🎨</span>
          Tema: Schema och Manuell styrning
        </h2>
        <p className="description">Aktuellt tema: {themeStatus?.current_theme} {themeStatus?.manual_override ? '(manuellt)' : '(automatiskt)'} </p>
      </div>
      <div className="form-actions">
        <button className="save-btn" type="button" onClick={()=>setManualTheme('light')}>Tvinga Ljust</button>
        <button className="save-btn" type="button" onClick={()=>setManualTheme('dark')}>Tvinga Mörkt</button>
        <button className="cancel-btn" type="button" onClick={clearManualTheme}>Rensa Manuell</button>
      </div>
      <div className="available-grid">
        {themeSchedules.map((s, idx) => (
          <div key={idx} className="available-card" style={{ alignItems: 'stretch' }}>
            <div className="available-info" style={{ width: '100%' }}>
              <div className="form-row">
                <div className="form-group">
                  <label>Namn</label>
                  <input type="text" value={s.name || ''} onChange={(e)=>updateThemeScheduleField(idx, 'name', e.target.value)} />
                </div>
                <div className="form-group">
                  <label>Tema</label>
                  <select value={s.theme_type} onChange={(e)=>updateThemeScheduleField(idx, 'theme_type', e.target.value)}>
                    <option value="light">Ljust</option>
                    <option value="dark">Mörkt</option>
                  </select>
                </div>
                <div className="form-group">
                  <label>Start</label>
                  <input type="time" value={s.start_time} onChange={(e)=>updateThemeScheduleField(idx, 'start_time', e.target.value)} />
                </div>
                <div className="form-group">
                  <label>Slut</label>
                  <input type="time" value={s.end_time} onChange={(e)=>updateThemeScheduleField(idx, 'end_time', e.target.value)} />
                </div>
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>Veckodagar (1-7, kommaseparerat)</label>
                  <input type="text" value={(s.weekdays||[]).join(',')} onChange={(e)=>updateThemeScheduleField(idx, 'weekdays', e.target.value.split(',').map(v=>parseInt(v.trim())).filter(Boolean))} />
                </div>
                <div className="form-group">
                  <label className="checkbox-label">
                    <input type="checkbox" checked={!!s.is_active} onChange={(e)=>updateThemeScheduleField(idx, 'is_active', e.target.checked)} />
                    <span className="checkmark"></span>
                    Aktiv
                  </label>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
      <div className="form-actions">
        <button className="save-btn" type="button" onClick={addThemeSchedule}>+ Lägg till schema</button>
        <button className="save-btn" type="button" onClick={saveThemeSchedules}>Spara scheman</button>
      </div>

      {/* Theme Settings */}
      <div className="section-header" style={{ marginTop: '2rem' }}>
        <h2>
          <span className="icon">🧩</span>
          Temainställningar (Färger)
        </h2>
      </div>
      <div className="available-grid">
        {themeSettings.map((ts, idx) => (
          <div key={idx} className="available-card" style={{ alignItems: 'stretch' }}>
            <div className="available-info" style={{ width: '100%' }}>
              <div className="form-row">
                <div className="form-group">
                  <label>Tema</label>
                  <select value={ts.theme_type} onChange={(e)=>updateThemeSettingField(idx, 'theme_type', e.target.value)}>
                    <option value="light">Ljust</option>
                    <option value="dark">Mörkt</option>
                  </select>
                </div>
                <div className="form-group">
                  <label>Primärfärg</label>
                  <input type="color" value={ts.primary_color} onChange={(e)=>updateThemeSettingField(idx, 'primary_color', e.target.value)} />
                </div>
                <div className="form-group">
                  <label>Bakgrund</label>
                  <input type="color" value={ts.background_color} onChange={(e)=>updateThemeSettingField(idx, 'background_color', e.target.value)} />
                </div>
                <div className="form-group">
                  <label>Yta</label>
                  <input type="color" value={ts.surface_color} onChange={(e)=>updateThemeSettingField(idx, 'surface_color', e.target.value)} />
                </div>
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>Text (primär)</label>
                  <input type="color" value={ts.text_primary} onChange={(e)=>updateThemeSettingField(idx, 'text_primary', e.target.value)} />
                </div>
                <div className="form-group">
                  <label>Text (sekundär)</label>
                  <input type="color" value={ts.text_secondary} onChange={(e)=>updateThemeSettingField(idx, 'text_secondary', e.target.value)} />
                </div>
                <div className="form-group">
                  <label>Ramfärg</label>
                  <input type="color" value={ts.border_color} onChange={(e)=>updateThemeSettingField(idx, 'border_color', e.target.value)} />
                </div>
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>Success</label>
                  <input type="color" value={ts.success_color} onChange={(e)=>updateThemeSettingField(idx, 'success_color', e.target.value)} />
                </div>
                <div className="form-group">
                  <label>Varning</label>
                  <input type="color" value={ts.warning_color} onChange={(e)=>updateThemeSettingField(idx, 'warning_color', e.target.value)} />
                </div>
                <div className="form-group">
                  <label>Fel</label>
                  <input type="color" value={ts.error_color} onChange={(e)=>updateThemeSettingField(idx, 'error_color', e.target.value)} />
                </div>
              </div>
              <div className="form-actions">
                <button className="save-btn" type="button" onClick={()=>saveThemeSetting(idx)}>Spara detta tema</button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Monitored Users */}
      <div className="section-header" style={{ marginTop: '2rem' }}>
        <h2>
          <span className="icon">👥</span>
          Övervakade Användare
        </h2>
      </div>
      <div className="services-grid">
        {monitoredUsers.map(u => (
          <div key={u.id} className={`service-card ${u.is_active ? 'active':'inactive'}`}>
            <div className="service-header">
              <div className="service-title">
                <span className={`status-indicator ${u.is_active ? 'active':'inactive'}`}>{u.is_active ? '✓':'✗'}</span>
                <h4>{u.display_name || u.user_name}</h4>
              </div>
              <div className="service-actions">
                <button onClick={()=>toggleUserActive(u)} className={`toggle-btn ${u.is_active ? 'active':'inactive'}`} title={u.is_active ? 'Inaktivera':'Aktivera'}>
                  {u.is_active ? '👁️':'🚫'}
                </button>
                <button onClick={()=>removeMonitoredUser(u.id)} className="remove-btn" title="Ta bort">🗑️</button>
              </div>
            </div>
            <div className="service-details">
              <div className="service-id">ID: {u.trio_user_id}</div>
            </div>
          </div>
        ))}
      </div>
      <div className="available-services">
        <div className="section-title">
          <h3>Tillgängliga Användare</h3>
          <span className="count">({availableUsers.length} tillgängliga)</span>
        </div>
        <div className="available-grid">
          {availableUsers.filter(u => !monitoredUsers.some(mu => mu.trio_user_id === u.id)).map(u => (
            <div key={u.id} className="available-card">
              <div className="available-info">
                <h4>{u.display_name || u.name}</h4>
                <div className="service-meta">ID: {u.id} | Status: {u.is_active ? 'Aktiv':'Inaktiv'}</div>
              </div>
              <button onClick={()=>addMonitoredUser(u)} className="add-service-btn" disabled={!u.is_active}><span>+</span> Lägg till</button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default ServiceConfiguration;
