/**
 * API Service for AWS CIEM Tool
 * Handles all backend API calls
 */

import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for logging
api.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

// AWS API
export const awsAPI = {
  testConnection: () => api.get('/api/v1/aws/test'),
};

// Scan API
export const scanAPI = {
  startScan: (config) => api.post('/api/v1/scan/start', config),
  getScanStatus: (scanId) => api.get(`/api/v1/scan/status/${scanId}`),
  getScanResults: (scanId) => api.get(`/api/v1/scan/results/${scanId}`),
  listScans: (limit = 10, offset = 0) => 
    api.get(`/api/v1/scan/list?limit=${limit}&offset=${offset}`),
  deleteScan: (scanId) => api.delete(`/api/v1/scan/${scanId}`),
};

// Risk API
export const riskAPI = {
  getSummary: (scanId = null) => {
    const url = scanId 
      ? `/api/v1/risks/summary?scan_id=${scanId}`
      : '/api/v1/risks/summary';
    return api.get(url);
  },
  listRisks: (params = {}) => {
    const queryParams = new URLSearchParams(params).toString();
    return api.get(`/api/v1/risks/list?${queryParams}`);
  },
  getRiskDetails: (riskId, scanId = null) => {
    const url = scanId
      ? `/api/v1/risks/${riskId}?scan_id=${scanId}`
      : `/api/v1/risks/${riskId}`;
    return api.get(url);
  },
  getBlastRadius: (identityArn, scanId) => 
    api.get(`/api/v1/risks/blast-radius/${encodeURIComponent(identityArn)}?scan_id=${scanId}`),
  getRisksByResource: (resourceId, scanId = null) => {
    const url = scanId
      ? `/api/v1/risks/by-resource/${resourceId}?scan_id=${scanId}`
      : `/api/v1/risks/by-resource/${resourceId}`;
    return api.get(url);
  },
  getStatistics: (scanId = null) => {
    const url = scanId
      ? `/api/v1/risks/statistics?scan_id=${scanId}`
      : '/api/v1/risks/statistics';
    return api.get(url);
  },
};

// Relationship API
export const relationshipAPI = {
  getGraphData: (scanId, includeOrphaned = false) =>
    api.get(`/api/v1/relationships/graph?scan_id=${scanId}&include_orphaned=${includeOrphaned}`),
  getConsolidatedView: (scanId) =>
    api.get(`/api/v1/relationships/consolidated?scan_id=${scanId}`),
  getRoleRelationships: (roleName, scanId) =>
    api.get(`/api/v1/relationships/role/${roleName}?scan_id=${scanId}`),
  getSecurityGroupRelationships: (groupId, scanId) =>
    api.get(`/api/v1/relationships/security-group/${groupId}?scan_id=${scanId}`),
  getResourceRelationships: (resourceId, scanId) =>
    api.get(`/api/v1/relationships/resource/${resourceId}?scan_id=${scanId}`),
  getInternetExposed: (scanId) =>
    api.get(`/api/v1/relationships/internet-exposed?scan_id=${scanId}`),
  getAccessPath: (source, target, scanId) =>
    api.get(`/api/v1/relationships/access-path?source=${source}&target=${target}&scan_id=${scanId}`),
  getSummary: (scanId) =>
    api.get(`/api/v1/relationships/summary?scan_id=${scanId}`),
};

// Health check
export const healthCheck = () => api.get('/health');

export default api;
