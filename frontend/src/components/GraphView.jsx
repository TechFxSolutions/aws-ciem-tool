/**
 * GraphView Component
 * Interactive graph visualization of IAM roles, resources, and security groups
 */

import React, { useState, useEffect, useRef } from 'react';
import cytoscape from 'cytoscape';
import dagre from 'cytoscape-dagre';
import { relationshipAPI, scanAPI } from '../services/api';
import './GraphView.css';

// Register dagre layout
cytoscape.use(dagre);

const GraphView = () => {
  const [loading, setLoading] = useState(true);
  const [scans, setScans] = useState([]);
  const [selectedScan, setSelectedScan] = useState(null);
  const [graphData, setGraphData] = useState(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const [error, setError] = useState(null);
  const [stats, setStats] = useState(null);
  const cyRef = useRef(null);
  const containerRef = useRef(null);

  useEffect(() => {
    loadScans();
  }, []);

  useEffect(() => {
    if (selectedScan) {
      loadGraphData(selectedScan);
    }
  }, [selectedScan]);

  useEffect(() => {
    if (graphData && containerRef.current) {
      // Small delay to ensure container is rendered
      setTimeout(() => {
        renderGraph();
      }, 100);
    }
  }, [graphData]);

  const loadScans = async () => {
    try {
      const response = await scanAPI.listScans(10, 0);
      const completedScans = response.data.scans.filter(s => s.status === 'completed');
      setScans(completedScans);
      
      if (completedScans.length > 0) {
        setSelectedScan(completedScans[0].scan_id);
      } else {
        setLoading(false);
      }
    } catch (err) {
      console.error('Failed to load scans:', err);
      setError('Failed to load scans');
      setLoading(false);
    }
  };

  const loadGraphData = async (scanId) => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await relationshipAPI.getGraphData(scanId, false);
      console.log('Graph data loaded:', response.data);
      setGraphData(response.data);
      setLoading(false);
    } catch (err) {
      console.error('Failed to load graph data:', err);
      setError('Failed to load graph data');
      setLoading(false);
    }
  };

  const renderGraph = () => {
    if (!graphData || !containerRef.current) {
      console.warn('Cannot render graph: missing data or container');
      return;
    }

    console.log('Rendering graph with data:', {
      nodes: graphData.nodes?.length,
      edges: graphData.edges?.length
    });

    // Destroy existing graph
    if (cyRef.current) {
      cyRef.current.destroy();
    }

    // Create a Set of valid node IDs for fast lookup
    const validNodeIds = new Set(graphData.nodes.map(node => node.id));

    // Filter edges to only include those with valid source and target nodes
    const validEdges = graphData.edges.filter(edge => {
      const hasValidSource = validNodeIds.has(edge.source);
      const hasValidTarget = validNodeIds.has(edge.target);
      
      if (!hasValidSource || !hasValidTarget) {
        console.warn(`Skipping invalid edge: ${edge.source} -> ${edge.target}`, {
          hasValidSource,
          hasValidTarget,
          edgeType: edge.type
        });
        return false;
      }
      
      return true;
    });

    // Calculate statistics
    const edgeStats = {
      total: graphData.edges.length,
      valid: validEdges.length,
      invalid: graphData.edges.length - validEdges.length
    };

    if (edgeStats.invalid > 0) {
      console.warn(`Filtered out ${edgeStats.invalid} invalid edges out of ${edgeStats.total} total edges`);
    }

    setStats({
      nodes: graphData.nodes.length,
      edges: validEdges.length,
      invalidEdges: edgeStats.invalid
    });

    // Transform data for Cytoscape
    const elements = [
      ...graphData.nodes.map(node => ({
        data: {
          id: node.id,
          label: node.label,
          type: node.type,
          group: node.group,
          ...node
        }
      })),
      ...validEdges.map((edge, index) => ({
        data: {
          id: `edge-${index}-${edge.source}-${edge.target}`,
          source: edge.source,
          target: edge.target,
          type: edge.type,
          label: edge.type
        }
      }))
    ];

    console.log('Creating Cytoscape with elements:', elements.length);

    // Create Cytoscape instance
    const cy = cytoscape({
      container: containerRef.current,
      elements: elements,
      style: [
        {
          selector: 'node',
          style: {
            'background-color': '#3b82f6',
            'label': 'data(label)',
            'color': '#1f2937',
            'text-valign': 'center',
            'text-halign': 'center',
            'font-size': '10px',
            'width': '40px',
            'height': '40px',
            'text-wrap': 'wrap',
            'text-max-width': '80px'
          }
        },
        {
          selector: 'node[type="iam_role"]',
          style: {
            'background-color': '#8b5cf6',
            'shape': 'round-rectangle'
          }
        },
        {
          selector: 'node[type="iam_user"]',
          style: {
            'background-color': '#ec4899',
            'shape': 'ellipse'
          }
        },
        {
          selector: 'node[type="ec2_instance"]',
          style: {
            'background-color': '#f59e0b',
            'shape': 'rectangle'
          }
        },
        {
          selector: 'node[type="lambda_function"]',
          style: {
            'background-color': '#10b981',
            'shape': 'diamond'
          }
        },
        {
          selector: 'node[type="s3_bucket"]',
          style: {
            'background-color': '#06b6d4',
            'shape': 'barrel'
          }
        },
        {
          selector: 'node[type="rds_instance"]',
          style: {
            'background-color': '#a855f7',
            'shape': 'ellipse'
          }
        },
        {
          selector: 'node[type="security_group"]',
          style: {
            'background-color': '#ef4444',
            'shape': 'hexagon'
          }
        },
        {
          selector: 'node[type="internet"]',
          style: {
            'background-color': '#dc2626',
            'shape': 'star',
            'width': '50px',
            'height': '50px'
          }
        },
        {
          selector: 'edge',
          style: {
            'width': 2,
            'line-color': '#9ca3af',
            'target-arrow-color': '#9ca3af',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
            'arrow-scale': 1.5
          }
        },
        {
          selector: 'edge[type="assumes"]',
          style: {
            'line-color': '#8b5cf6',
            'target-arrow-color': '#8b5cf6',
            'line-style': 'dashed'
          }
        },
        {
          selector: 'edge[type="attached_to"]',
          style: {
            'line-color': '#3b82f6',
            'target-arrow-color': '#3b82f6'
          }
        },
        {
          selector: 'edge[type="protected_by"]',
          style: {
            'line-color': '#10b981',
            'target-arrow-color': '#10b981'
          }
        },
        {
          selector: 'edge[type="allows_traffic_from"]',
          style: {
            'line-color': '#ef4444',
            'target-arrow-color': '#ef4444',
            'line-style': 'dotted',
            'width': 3
          }
        },
        {
          selector: ':selected',
          style: {
            'background-color': '#fbbf24',
            'line-color': '#fbbf24',
            'target-arrow-color': '#fbbf24',
            'border-width': 3,
            'border-color': '#f59e0b'
          }
        }
      ],
      layout: {
        name: 'dagre',
        rankDir: 'TB',
        nodeSep: 50,
        rankSep: 100,
        padding: 30,
        animate: false
      },
      minZoom: 0.3,
      maxZoom: 3,
      wheelSensitivity: 0.2
    });

    console.log('Cytoscape instance created');

    // Event handlers
    cy.on('tap', 'node', (evt) => {
      const node = evt.target;
      setSelectedNode(node.data());
    });

    cy.on('tap', (evt) => {
      if (evt.target === cy) {
        setSelectedNode(null);
      }
    });

    // Fit graph to viewport after layout completes
    cy.ready(() => {
      console.log('Cytoscape ready, fitting to viewport');
      cy.fit(null, 50);
      cy.center();
    });

    cyRef.current = cy;
  };

  const handleScanChange = (e) => {
    setSelectedScan(e.target.value);
    setSelectedNode(null);
  };

  const handleZoomIn = () => {
    if (cyRef.current) {
      cyRef.current.zoom(cyRef.current.zoom() * 1.2);
      cyRef.current.center();
    }
  };

  const handleZoomOut = () => {
    if (cyRef.current) {
      cyRef.current.zoom(cyRef.current.zoom() * 0.8);
      cyRef.current.center();
    }
  };

  const handleFit = () => {
    if (cyRef.current) {
      cyRef.current.fit(null, 50);
    }
  };

  const handleReset = () => {
    if (cyRef.current) {
      cyRef.current.zoom(1);
      cyRef.current.center();
    }
  };

  if (loading) {
    return (
      <div className="graph-view-container">
        <div className="loading">Loading graph data...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="graph-view-container">
        <div className="error">{error}</div>
      </div>
    );
  }

  if (scans.length === 0) {
    return (
      <div className="graph-view-container">
        <div className="no-data">
          <h2>No Completed Scans</h2>
          <p>Complete a scan first to view the graph visualization.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="graph-view-container">
      <div className="graph-header">
        <div className="header-left">
          <h1>Infrastructure Graph</h1>
          <select 
            value={selectedScan || ''} 
            onChange={handleScanChange}
            className="scan-selector"
          >
            {scans.map(scan => (
              <option key={scan.scan_id} value={scan.scan_id}>
                Scan: {new Date(scan.started_at).toLocaleString()}
              </option>
            ))}
          </select>
        </div>
        
        <div className="graph-controls">
          <button onClick={handleZoomIn} className="control-btn" title="Zoom In">
            🔍+
          </button>
          <button onClick={handleZoomOut} className="control-btn" title="Zoom Out">
            🔍-
          </button>
          <button onClick={handleFit} className="control-btn" title="Fit to Screen">
            ⛶
          </button>
          <button onClick={handleReset} className="control-btn" title="Reset View">
            ↻
          </button>
        </div>
      </div>

      {stats && (
        <div className="graph-stats">
          <span className="stat-item">Nodes: {stats.nodes}</span>
          <span className="stat-item">Edges: {stats.edges}</span>
          {stats.invalidEdges > 0 && (
            <span className="stat-item warning">
              ⚠ {stats.invalidEdges} invalid edge{stats.invalidEdges !== 1 ? 's' : ''} filtered
            </span>
          )}
        </div>
      )}

      <div className="graph-content">
        <div ref={containerRef} className="graph-canvas" />
        
        {selectedNode && (
          <div className="node-details">
            <h3>Node Details</h3>
            <div className="detail-row">
              <strong>Type:</strong>
              <span>{selectedNode.type}</span>
            </div>
            <div className="detail-row">
              <strong>Label:</strong>
              <span>{selectedNode.label}</span>
            </div>
            <div className="detail-row">
              <strong>ID:</strong>
              <span className="id-text">{selectedNode.id}</span>
            </div>
            {selectedNode.group && (
              <div className="detail-row">
                <strong>Group:</strong>
                <span>{selectedNode.group}</span>
              </div>
            )}
            {selectedNode.is_admin !== undefined && (
              <div className="detail-row">
                <strong>Admin:</strong>
                <span>{selectedNode.is_admin ? 'Yes' : 'No'}</span>
              </div>
            )}
            {selectedNode.is_public !== undefined && (
              <div className="detail-row">
                <strong>Public:</strong>
                <span>{selectedNode.is_public ? 'Yes' : 'No'}</span>
              </div>
            )}
            {selectedNode.has_internet_access !== undefined && (
              <div className="detail-row">
                <strong>Internet Access:</strong>
                <span>{selectedNode.has_internet_access ? 'Yes' : 'No'}</span>
              </div>
            )}
            <button 
              onClick={() => setSelectedNode(null)}
              className="close-btn"
            >
              Close
            </button>
          </div>
        )}
      </div>

      <div className="graph-legend">
        <h4>Legend</h4>
        <div className="legend-items">
          <div className="legend-item">
            <span className="legend-icon iam-role"></span>
            <span>IAM Role</span>
          </div>
          <div className="legend-item">
            <span className="legend-icon iam-user"></span>
            <span>IAM User</span>
          </div>
          <div className="legend-item">
            <span className="legend-icon ec2"></span>
            <span>EC2 Instance</span>
          </div>
          <div className="legend-item">
            <span className="legend-icon lambda"></span>
            <span>Lambda Function</span>
          </div>
          <div className="legend-item">
            <span className="legend-icon s3"></span>
            <span>S3 Bucket</span>
          </div>
          <div className="legend-item">
            <span className="legend-icon security-group"></span>
            <span>Security Group</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default GraphView;
