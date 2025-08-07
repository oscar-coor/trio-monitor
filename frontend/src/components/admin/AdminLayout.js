/**
 * Admin Layout Component - Main layout for administrative interface
 */

import React, { useState } from 'react';
import ServiceConfiguration from './ServiceConfiguration';
import UserConfiguration from './UserConfiguration';
import './AdminLayout.css';

const AdminLayout = ({ children, onTabChange }) => {
  const [activeTab, setActiveTab] = useState('services');

  const tabs = [
    { id: 'services', label: 'Tjänster & Köer', icon: '📋' },
    { id: 'users', label: 'Användare', icon: '👥' },
    { id: 'timeSettings', label: 'Tidsinställningar', icon: '⏰' },
    { id: 'themes', label: 'Tema', icon: '🌓' },
    { id: 'reports', label: 'SLA Rapporter', icon: '📊' }
  ];

  const renderTabContent = () => {
    switch (activeTab) {
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
              className={`nav-tab ${activeTab === tab.id ? 'active' : ''}`}
              onClick={() => {
                setActiveTab(tab.id);
                if (onTabChange) {
                  onTabChange(tab.id);
                }
              }}
            >
              <span className="tab-icon">{tab.icon}</span>
              <span className="tab-label">{tab.label}</span>
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
