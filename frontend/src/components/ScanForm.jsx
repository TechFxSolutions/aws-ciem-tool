/**
 * ScanForm Component
 * Form for configuring and starting new AWS scans
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { scanAPI } from '../services/api';
import './ScanForm.css';

const ScanForm = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  const [scanId, setScanId] = useState(null);

  const [formData, setFormData] = useState({
    regions: ['us-east-1'],
    scan_iam: true,
    scan_ec2: true,
    scan_lambda: true,
    scan_s3: true,
    scan_rds: true,
    scan_security_groups: true,
  });

  const availableRegions = [
    'us-east-1',
    'us-east-2',
    'us-west-1',
    'us-west-2',
    'eu-west-1',
    'eu-west-2',
    'eu-central-1',
    'ap-south-1',
    'ap-southeast-1',
    'ap-southeast-2',
    'ap-northeast-1',
  ];

  const handleRegionToggle = (region) => {
    setFormData(prev => ({
      ...prev,
      regions: prev.regions.includes(region)
        ? prev.regions.filter(r => r !== region)
        : [...prev.regions, region]
    }));
  };

  const handleServiceToggle = (service) => {
    setFormData(prev => ({
      ...prev,
      [service]: !prev[service]
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (formData.regions.length === 0) {
      setError('Please select at least one region');
      return;
    }

    const hasAnyService = formData.scan_iam || formData.scan_ec2 || 
                          formData.scan_lambda || formData.scan_s3 || 
                          formData.scan_rds || formData.scan_security_groups;

    if (!hasAnyService) {
      setError('Please select at least one service to scan');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      setSuccess(false);

      const response = await scanAPI.startScan(formData);
      
      if (response.data && response.data.scan_id) {
        setScanId(response.data.scan_id);
        setSuccess(true);
        
        // Redirect to dashboard after 2 seconds
        setTimeout(() => {
          navigate('/');
        }, 2000);
      } else {
        throw new Error('Invalid response from server');
      }
    } catch (err) {
      console.error('Failed to start scan:', err);
      setError(err.response?.data?.detail || 'Failed to start scan. Please check your AWS credentials and try again.');
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="scan-form-container">
        <div className="success-message">
          <div className="success-icon">✓</div>
          <h2>Scan Started Successfully!</h2>
          <p>Scan ID: {scanId}</p>
          <p>Redirecting to dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="scan-form-container">
      <div className="scan-form-header">
        <h1>Start New AWS Scan</h1>
        <p>Configure and start a comprehensive security scan of your AWS infrastructure</p>
      </div>

      {error && (
        <div className="error-message">
          <strong>Error:</strong> {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="scan-form">
        {/* Regions Section */}
        <div className="form-section">
          <h3>Select Regions</h3>
          <p className="section-description">Choose which AWS regions to scan</p>
          <div className="checkbox-grid">
            {availableRegions.map(region => (
              <label key={region} className="checkbox-label">
                <input
                  type="checkbox"
                  checked={formData.regions.includes(region)}
                  onChange={() => handleRegionToggle(region)}
                  disabled={loading}
                />
                <span>{region}</span>
              </label>
            ))}
          </div>
        </div>

        {/* Services Section */}
        <div className="form-section">
          <h3>Select Services</h3>
          <p className="section-description">Choose which AWS services to scan</p>
          <div className="checkbox-list">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={formData.scan_iam}
                onChange={() => handleServiceToggle('scan_iam')}
                disabled={loading}
              />
              <div className="service-info">
                <strong>IAM (Identity and Access Management)</strong>
                <span>Scan users, roles, policies, and permissions</span>
              </div>
            </label>

            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={formData.scan_ec2}
                onChange={() => handleServiceToggle('scan_ec2')}
                disabled={loading}
              />
              <div className="service-info">
                <strong>EC2 (Elastic Compute Cloud)</strong>
                <span>Scan instances, AMIs, and compute resources</span>
              </div>
            </label>

            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={formData.scan_lambda}
                onChange={() => handleServiceToggle('scan_lambda')}
                disabled={loading}
              />
              <div className="service-info">
                <strong>Lambda</strong>
                <span>Scan serverless functions and execution roles</span>
              </div>
            </label>

            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={formData.scan_s3}
                onChange={() => handleServiceToggle('scan_s3')}
                disabled={loading}
              />
              <div className="service-info">
                <strong>S3 (Simple Storage Service)</strong>
                <span>Scan buckets, policies, and access controls</span>
              </div>
            </label>

            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={formData.scan_rds}
                onChange={() => handleServiceToggle('scan_rds')}
                disabled={loading}
              />
              <div className="service-info">
                <strong>RDS (Relational Database Service)</strong>
                <span>Scan database instances and security groups</span>
              </div>
            </label>

            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={formData.scan_security_groups}
                onChange={() => handleServiceToggle('scan_security_groups')}
                disabled={loading}
              />
              <div className="service-info">
                <strong>Security Groups</strong>
                <span>Scan firewall rules and network access controls</span>
              </div>
            </label>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="form-actions">
          <button
            type="button"
            className="btn-secondary"
            onClick={() => navigate('/')}
            disabled={loading}
          >
            Cancel
          </button>
          <button
            type="submit"
            className="btn-primary"
            disabled={loading}
          >
            {loading ? 'Starting Scan...' : 'Start Scan'}
          </button>
        </div>
      </form>

      {/* Info Box */}
      <div className="info-box">
        <h4>ℹ️ Important Information</h4>
        <ul>
          <li>Scans are read-only and do not modify your AWS resources</li>
          <li>Ensure your AWS credentials have appropriate read permissions</li>
          <li>Scan duration depends on the number of resources in your account</li>
          <li>You can monitor scan progress from the dashboard</li>
        </ul>
      </div>
    </div>
  );
};

export default ScanForm;
