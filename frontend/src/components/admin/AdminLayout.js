/**
 * Admin Layout Component - Main layout for administrative interface
 */

import React, { useEffect, useState } from 'react';
import ServiceConfiguration from './ServiceConfiguration';
import UserConfiguration from './UserConfiguration';
import ConnectionSettings from './ConnectionSettings';
import './AdminLayout.css';
import { adminApi } from '../../services/adminApi';

const AdminLayout = ({ children, onTabChange }) => {
  const [activeTab, setActiveTab] = useState('services');

  const [connValid, setConnValid] = useState(true);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const cfg = await adminApi.getConnectionSettings();
        const baseOk = Boolean((cfg.base_url || '').trim());
        const ccOk = Boolean((cfg.contact_center_id || '').trim());
        const hasToken = Boolean(cfg.has_token);
        const hasUser = Boolean((cfg.username || '').trim());
        const valid = baseOk && ccOk && (hasToken || hasUser);
        if (!cancelled) setConnValid(valid);
      } catch {
        if (!cancelled) setConnValid(false);
      }
    };
    load();
    return () => { cancelled = true; };
  }, []);

  const tabs = [
    { id: 'connection', label: 'Anslutning', icon: '🔗' },
    { id: 'services', label: 'Tjänster & Köer', icon: '📋' },
    { id: 'users', label: 'Användare', icon: '👥' },
    { id: 'timeSettings', label: 'Tidsinställningar', icon: '⏰' },
    { id: 'themes', label: 'Tema', icon: '🌓' },
    { id: 'reports', label: 'SLA Rapporter', icon: '📊' }
  ];

  const renderTabContent = () => {
    switch (activeTab) {
      case 'connection':
        return <ConnectionSettings />;
      case 'services':
        return <ServiceConfiguration />;
      case 'users':
        return <UserConfiguration />;
      case 'timeSettings':
        return (
          <div className="tab-content">
            <h3>Tidsinställningar</h3>
            <p>Här kommer funktionalitet för att konfigurera tidsfönster för SLA-mätningar.</p>
          </div>
        );
      case 'themes':
        return (
          <div className="tab-content">
            <h3>Tema Inställningar</h3>
            <p>Här kommer funktionalitet för att konfigurera automatisk tema-växling.</p>
          </div>
        );
      case 'reports':
        return (
          <div className="tab-content">
            <h3>SLA Rapporter</h3>
            <p>Här kommer SLA-rapporter och historiska data.</p>
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div className="admin-layout">
      {/* Admin Header */}
      <div className="admin-header">
        <h1>
          <span className="admin-icon">⚙️</span>
          Administration - Trio Monitor
        </h1>
        <div className="admin-subtitle">
          Konfigurera övervakning, användare och systeminställningar
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="admin-nav">
        <div className="nav-tabs">
          {tabs.map(tab => (
            <button
              key={tab.id}
              className={`tab-button ${activeTab === tab.id ? 'active' : ''}`}
              onClick={() => handleTabChange(tab.id)}
            >
              <span className="tab-icon">{tab.icon}</span> {tab.label}
              {tab.id === 'connection' && !connValid && (
                <span title="Konfiguration krävs" style={{ marginLeft: 6, width: 8, height: 8, background: '#c62828', borderRadius: '50%', display: 'inline-block' }} />
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Content Area */}
      <div className="admin-content">
        <div className="content-wrapper">
          {renderTabContent()}
          {children}
        </div>
      </div>
    </div>
  );
};

export default AdminLayout;
