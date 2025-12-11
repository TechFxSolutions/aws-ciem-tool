/**
 * Dashboard Component
 * Main overview dashboard showing risk summary and statistics
 */

import React, { useState, useEffect } from 'react';
import { riskAPI, scanAPI } from '../services/api';
import './Dashboard.css';

const Dashboard = () => {
  const [loading, setLoading] = useState(true);
  const [riskSummary, setRiskSummary] = useState(null);
  const [recentScans, setRecentScans] = useState([]);
  const [selectedScan, setSelectedScan] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Load recent scans
      const scansResponse = await scanAPI.listScans(5, 0);
      const scans = scansResponse.data.scans || [];
      setRecentScans(scans);

      // Load risk summary for the most recent completed scan
      const completedScan = scans.find(s => s.status === 'completed');
      if (completedScan) {
        setSelectedScan(completedScan.scan_id);
        const riskResponse = await riskAPI.getSummary(completedScan.scan_id);
        setRiskSummary(riskResponse.data);
      }

      setLoading(false);
    } catch (err) {
      console.error('Failed to load dashboard data:', err);
      setError('Failed to load dashboard data. Please try again.');
      setLoading(false);
    }
  };

  const getRiskColor = (severity) => {
    const colors = {
      critical: '#dc2626',
      high: '#ea580c',
      medium: '#f59e0b',
      low: '#10b981',
    };
    return colors[severity] || '#6b7280';
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleString();
  };

  if (loading) {
    return (
      <div className="dashboard-container">
        <div className="loading">Loading dashboard...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="dashboard-container">
        <div className="error">{error}</div>
        <button onClick={loadDashboardData} className="btn-retry">
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="dashboard-container">
      <header className="dashboard-header">
        <h1>AWS CIEM Dashboard</h1>
        <p>Cloud Infrastructure Entitlement Management</p>
      </header>

      {/* Risk Summary Cards */}
      {riskSummary && (
        <div className="risk-summary">
          <div className="summary-card critical">
            <div className="card-icon">🔴</div>
            <div className="card-content">
              <h3>{riskSummary.summary?.critical || 0}</h3>
              <p>Critical Risks</p>
            </div>
          </div>

          <div className="summary-card high">
            <div className="card-icon">🟠</div>
            <div className="card-content">
              <h3>{riskSummary.summary?.high || 0}</h3>
              <p>High Risks</p>
            </div>
          </div>

          <div className="summary-card medium">
            <div className="card-icon">🟡</div>
            <div className="card-content">
              <h3>{riskSummary.summary?.medium || 0}</h3>
              <p>Medium Risks</p>
            </div>
          </div>

          <div className="summary-card low">
            <div className="card-icon">🟢</div>
            <div className="card-content">
              <h3>{riskSummary.summary?.low || 0}</h3>
              <p>Low Risks</p>
            </div>
          </div>
        </div>
      )}

      {/* Top Risks */}
      {riskSummary && riskSummary.top_risks && riskSummary.top_risks.length > 0 && (
        <div className="top-risks-section">
          <h2>Top Risks</h2>
          <div className="risks-list">
            {riskSummary.top_risks.map((risk, index) => (
              <div key={index} className="risk-item">
                <div 
                  className="risk-severity-badge"
                  style={{ backgroundColor: getRiskColor(risk.severity) }}
                >
                  {risk.severity?.toUpperCase()}
                </div>
                <div className="risk-details">
                  <h4>{risk.title}</h4>
                  <p>{risk.description}</p>
                  <div className="risk-meta">
                    <span className="risk-type">{risk.risk_type}</span>
                    <span className="risk-score">Score: {risk.risk_score}</span>
                    {risk.resource_id && (
                      <span className="risk-resource">{risk.resource_id}</span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recent Scans */}
      <div className="recent-scans-section">
        <h2>Recent Scans</h2>
        {recentScans.length === 0 ? (
          <div className="no-scans">
            <p>No scans found. Start a new scan to begin.</p>
          </div>
        ) : (
          <div className="scans-list">
            {recentScans.map((scan) => (
              <div 
                key={scan.scan_id} 
                className={`scan-item ${scan.scan_id === selectedScan ? 'selected' : ''}`}
                onClick={() => setSelectedScan(scan.scan_id)}
              >
                <div className="scan-status">
                  <span className={`status-badge ${scan.status}`}>
                    {scan.status}
                  </span>
                </div>
                <div className="scan-details">
                  <p className="scan-id">Scan ID: {scan.scan_id.substring(0, 8)}...</p>
                  <p className="scan-time">Started: {formatDate(scan.started_at)}</p>
                  {scan.completed_at && (
                    <p className="scan-time">Completed: {formatDate(scan.completed_at)}</p>
                  )}
                  {scan.progress !== undefined && (
                    <div className="scan-progress">
                      <div className="progress-bar">
                        <div 
                          className="progress-fill"
                          style={{ width: `${scan.progress}%` }}
                        />
                      </div>
                      <span className="progress-text">{scan.progress}%</span>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Quick Actions */}
      <div className="quick-actions">
        <button 
          className="btn-primary"
          onClick={() => window.location.href = '/scan'}
        >
          Start New Scan
        </button>
        <button 
          className="btn-secondary"
          onClick={() => window.location.href = '/risks'}
        >
          View All Risks
        </button>
        <button 
          className="btn-secondary"
          onClick={() => window.location.href = '/graph'}
        >
          View Graph
        </button>
      </div>
    </div>
  );
};

export default Dashboard;
