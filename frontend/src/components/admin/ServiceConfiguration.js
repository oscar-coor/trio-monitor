/**
 * Service Configuration Component - Manage monitored services and SLA settings
 */

import React, { useState, useEffect } from 'react';
import { adminApi } from '../../services/adminApi';
import './ServiceConfiguration.css';

const ServiceConfiguration = () => {
  const [monitoredServices, setMonitoredServices] = useState([]);
  const [availableServices, setAvailableServices] = useState([]);
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
      const [monitored, available] = await Promise.all([
        adminApi.getMonitoredServices(),
        adminApi.getAvailableServices()
      ]);
      setMonitoredServices(monitored);
      setAvailableServices(available);
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
    </div>
  );
};

export default ServiceConfiguration;
