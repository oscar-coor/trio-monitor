/**
 * User Configuration Component - Manage monitored users/agents
 */

import React, { useState, useEffect } from 'react';
import { adminApi } from '../../services/adminApi';
import './UserConfiguration.css';

const UserConfiguration = () => {
  const [monitoredUsers, setMonitoredUsers] = useState([]);
  const [availableUsers, setAvailableUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showAddUser, setShowAddUser] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [confirmRemoveUserId, setConfirmRemoveUserId] = useState(null);

  // Form state for adding/editing users
  const [userForm, setUserForm] = useState({
    trio_user_id: '',
    user_name: '',
    display_name: '',
    is_active: true
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [monitored, available] = await Promise.all([
        adminApi.getMonitoredUsers(),
        adminApi.getAvailableUsers()
      ]);
      setMonitoredUsers(monitored);
      setAvailableUsers(available);
    } catch (err) {
      setError('Kunde inte ladda användardata: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleAddUser = (user) => {
    setUserForm({
      trio_user_id: user.id,
      user_name: user.name,
      display_name: user.display_name || user.name,
      is_active: true
    });
    setShowAddUser(true);
  };

  const handleEditUser = (user) => {
    setUserForm({
      trio_user_id: user.trio_user_id,
      user_name: user.user_name,
      display_name: user.display_name,
      is_active: user.is_active
    });
    setEditingUser(user);
    setShowAddUser(true);
  };

  const handleSubmitUser = async (e) => {
    e.preventDefault();
    try {
      if (editingUser) {
        await adminApi.updateMonitoredUser(editingUser.id, userForm);
      } else {
        await adminApi.addMonitoredUser(userForm);
      }
      setShowAddUser(false);
      setEditingUser(null);
      loadData();
    } catch (err) {
      setError('Kunde inte spara användare: ' + err.message);
    }
  };

  const handleRemoveUser = async (userId) => {
    try {
      await adminApi.removeMonitoredUser(userId);
      setConfirmRemoveUserId(null);
      loadData();
    } catch (err) {
      setError('Kunde inte ta bort användare: ' + err.message);
    }
  };

  const handleToggleActive = async (user) => {
    try {
      await adminApi.updateMonitoredUser(user.id, {
        ...user,
        is_active: !user.is_active
      });
      loadData();
    } catch (err) {
      setError('Kunde inte uppdatera användare: ' + err.message);
    }
  };

  const resetForm = () => {
    setUserForm({
      trio_user_id: '',
      user_name: '',
      display_name: '',
      is_active: true
    });
    setShowAddUser(false);
    setEditingUser(null);
  };

  const getStatusIcon = (isActive) => isActive ? '✓' : '✗';
  const getStatusClass = (isActive) => isActive ? 'active' : 'inactive';

  if (loading) {
    return (
      <div className="user-config">
        <div className="loading-container">
          <div className="spinner"></div>
          <p>Laddar användardata...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="user-config">
      <div className="section-header">
        <h2>
          <span className="icon">👥</span>
          Övervakade Användare & Agenter
        </h2>
        <p className="description">
          Konfigurera vilka TrioID/användare som ska inkluderas i övervakning
        </p>
      </div>

      {error && (
        <div className="error-message">
          <span className="error-icon">⚠️</span>
          {error}
          <button onClick={() => setError(null)} className="error-close">×</button>
        </div>
      )}

      {/* Monitored Users List */}
      <div className="monitored-users">
        <div className="section-title">
          <h3>Aktiva Övervakningar</h3>
          <span className="count">({monitoredUsers.length} användare)</span>
        </div>

        {monitoredUsers.length === 0 ? (
          <div className="empty-state">
            <span className="empty-icon">👥</span>
            <h4>Inga användare konfigurerade</h4>
            <p>Lägg till användare från listan nedan för att börja övervaka</p>
          </div>
        ) : (
          <div className="users-grid">
            {monitoredUsers.map(user => (
              <div key={user.id} className={`user-card ${getStatusClass(user.is_active)}`}>
                <div className="user-header">
                  <div className="user-info">
                    <div className="user-avatar">
                      <span className={`status-indicator ${getStatusClass(user.is_active)}`}>
                        {getStatusIcon(user.is_active)}
                      </span>
                      <div className="avatar-circle">
                        {(user.display_name || user.user_name).charAt(0).toUpperCase()}
                      </div>
                    </div>
                    <div className="user-details">
                      <h4>{user.display_name || user.user_name}</h4>
                      <p className="username">@{user.user_name}</p>
                    </div>
                  </div>
                  <div className="user-actions">
                    <button 
                      onClick={() => handleToggleActive(user)}
                      className={`toggle-btn ${getStatusClass(user.is_active)}`}
                      title={user.is_active ? 'Inaktivera' : 'Aktivera'}
                    >
                      {user.is_active ? '👁️' : '🚫'}
                    </button>
                    <button 
                      onClick={() => handleEditUser(user)}
                      className="edit-btn"
                      title="Redigera"
                    >
                      ✏️
                    </button>
                    <button 
                      onClick={() => setConfirmRemoveUserId(user.id)}
                      className="remove-btn"
                      title="Ta bort"
                    >
                      🗑️
                    </button>
                  </div>
                </div>
                {confirmRemoveUserId === user.id && (
                  <div className="confirm-bar">
                    <span>Ta bort denna användare?</span>
                    <div className="confirm-actions">
                      <button className="confirm-btn" onClick={() => handleRemoveUser(user.id)}>Bekräfta</button>
                      <button className="cancel-btn" onClick={() => setConfirmRemoveUserId(null)}>Avbryt</button>
                    </div>
                  </div>
                )}
                <div className="user-meta">
                  <div className="meta-item">
                    <span className="meta-label">Trio ID:</span>
                    <span className="meta-value">{user.trio_user_id}</span>
                  </div>
                  <div className="meta-item">
                    <span className="meta-label">Status:</span>
                    <span className={`status-badge ${getStatusClass(user.is_active)}`}>
                      {user.is_active ? 'Aktiv' : 'Inaktiv'}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Available Users */}
      <div className="available-users">
        <div className="section-title">
          <h3>Tillgängliga Användare från Trio</h3>
          <span className="count">({availableUsers.length} tillgängliga)</span>
        </div>

        {availableUsers.length === 0 ? (
          <div className="empty-state">
            <span className="empty-icon">🔌</span>
            <h4>Inga användare tillgängliga</h4>
            <p>Kontrollera anslutningen till Trio API</p>
          </div>
        ) : (
          <div className="available-grid">
            {availableUsers
              .filter(user => !monitoredUsers.some(m => m.trio_user_id === user.id))
              .map(user => (
                <div key={user.id} className="available-card">
                  <div className="available-user-info">
                    <div className="available-avatar">
                      {(user.display_name || user.name).charAt(0).toUpperCase()}
                    </div>
                    <div className="available-details">
                      <h4>{user.display_name || user.name}</h4>
                      <p className="available-username">@{user.name}</p>
                      {user.email && (
                        <p className="available-email">{user.email}</p>
                      )}
                      <div className="user-meta">
                        ID: {user.id} | Status: {user.is_active ? 'Aktiv' : 'Inaktiv'}
                      </div>
                    </div>
                  </div>
                  <button 
                    onClick={() => handleAddUser(user)}
                    className="add-user-btn"
                    disabled={!user.is_active}
                  >
                    <span>+</span> Lägg till
                  </button>
                </div>
              ))}
          </div>
        )}
      </div>

      {/* Add/Edit User Modal */}
      {showAddUser && (
        <div className="modal-overlay" onClick={resetForm}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>
                {editingUser ? 'Redigera Användare' : 'Lägg till Användare'}
              </h3>
              <button onClick={resetForm} className="modal-close">×</button>
            </div>

            <form onSubmit={handleSubmitUser} className="user-form">
              <div className="form-group">
                <label>Användarnamn:</label>
                <input
                  type="text"
                  value={userForm.user_name}
                  onChange={(e) => setUserForm({...userForm, user_name: e.target.value})}
                  required
                />
              </div>

              <div className="form-group">
                <label>Visningsnamn:</label>
                <input
                  type="text"
                  value={userForm.display_name}
                  onChange={(e) => setUserForm({...userForm, display_name: e.target.value})}
                  placeholder="Lämna tom för att använda användarnamn"
                />
              </div>

              <div className="form-group">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={userForm.is_active}
                    onChange={(e) => setUserForm({...userForm, is_active: e.target.checked})}
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
                  {editingUser ? 'Uppdatera' : 'Lägg till'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default UserConfiguration;
