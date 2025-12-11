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
      renderGraph();
    }
  }, [graphData]);

  const loadScans = async () => {
    try {
      const response = await scanAPI.listScans(10, 0);
      const completedScans = response.data.scans.filter(s => s.status === 'completed');
      setScans(completedScans);
      
      if (completedScans.length > 0) {
        setSelectedScan(completedScans[0].scan_id);
      }
    } catch (err) {
      console.error('Failed to load scans:', err);
      setError('Failed to load scans');
    }
  };

  const loadGraphData = async (scanId) => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await relationshipAPI.getGraphData(scanId, false);
      setGraphData(response.data);
      setLoading(false);
    } catch (err) {
      console.error('Failed to load graph data:', err);
      setError('Failed to load graph data');
      setLoading(false);
    }
  };

  const renderGraph = () => {
    if (!graphData || !containerRef.current) return;

    // Destroy existing graph
    if (cyRef.current) {
      cyRef.current.destroy();
    }

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
      ...graphData.edges.map(edge => ({
        data: {
          source: edge.source,
          target: edge.target,
          type: edge.type
        }
      }))
    ];

    // Create Cytoscape instance
    const cy = cytoscape({
      container: containerRef.current,
      elements: elements,
      style: [
        {
          selector: 'node',
          style: {
            'label': 'data(label)',
            'text-valign': 'center',
            'text-halign': 'center',
            'font-size': '12px',
            'width': '60px',
            'height': '60px',
            'background-color': '#3b82f6',
            'color': '#fff',
            'text-wrap': 'wrap',
            'text-max-width': '80px'
          }
        },
        {
          selector: 'node[type="iam_role"]',
          style: {
            'background-color': '#8b5cf6',
            'shape': 'roundrectangle'
          }
        },
        {
          selector: 'node[type="security_group"]',
          style: {
            'background-color': '#f59e0b',
            'shape': 'diamond'
          }
        },
        {
          selector: 'node[type="ec2_instance"]',
          style: {
            'background-color': '#10b981',
            'shape': 'rectangle'
          }
        },
        {
          selector: 'node[type="lambda_function"]',
          style: {
            'background-color': '#06b6d4',
            'shape': 'ellipse'
          }
        },
        {
          selector: 'node[type="internet"]',
          style: {
            'background-color': '#dc2626',
            'shape': 'star',
            'width': '80px',
            'height': '80px'
          }
        },
        {
          selector: 'node[is_public=true]',
          style: {
            'border-width': '3px',
            'border-color': '#dc2626'
          }
        },
        {
          selector: 'node[has_internet_access=true]',
          style: {
            'border-width': '3px',
            'border-color': '#ea580c'
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
          selector: 'edge[type="allows_traffic_from"]',
          style: {
            'line-color': '#dc2626',
            'target-arrow-color': '#dc2626',
            'line-style': 'dashed'
          }
        },
        {
          selector: ':selected',
          style: {
            'border-width': '4px',
            'border-color': '#1e40af',
            'background-color': '#2563eb'
          }
        }
      ],
      layout: {
        name: 'dagre',
        rankDir: 'TB',
        nodeSep: 50,
        rankSep: 100,
        padding: 30
      }
    });

    // Node click handler
    cy.on('tap', 'node', (event) => {
      const node = event.target;
      setSelectedNode(node.data());
    });

    // Double click to focus
    cy.on('dbltap', 'node', (event) => {
      const node = event.target;
      cy.animate({
        fit: {
          eles: node.neighborhood().add(node),
          padding: 50
        },
        duration: 500
      });
    });

    cyRef.current = cy;
  };

  const resetView = () => {
    if (cyRef.current) {
      cyRef.current.fit();
    }
  };

  const exportImage = () => {
    if (cyRef.current) {
      const png = cyRef.current.png({ scale: 2 });
      const link = document.createElement('a');
      link.download = `ciem-graph-${selectedScan}.png`;
      link.href = png;
      link.click();
    }
  };

  if (loading) {
    return (
      <div className="graph-container">
        <div className="loading">Loading graph...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="graph-container">
        <div className="error">{error}</div>
      </div>
    );
  }

  return (
    <div className="graph-container">
      <div className="graph-header">
        <h1>Relationship Graph</h1>
        <div className="graph-controls">
          <select 
            value={selectedScan || ''} 
            onChange={(e) => setSelectedScan(e.target.value)}
            className="scan-selector"
          >
            {scans.map(scan => (
              <option key={scan.scan_id} value={scan.scan_id}>
                Scan: {scan.scan_id.substring(0, 8)}... ({new Date(scan.started_at).toLocaleDateString()})
              </option>
            ))}
          </select>
          <button onClick={resetView} className="btn-control">
            Reset View
          </button>
          <button onClick={exportImage} className="btn-control">
            Export PNG
          </button>
        </div>
      </div>

      <div className="graph-content">
        <div className="graph-canvas" ref={containerRef} />
        
        {selectedNode && (
          <div className="node-details">
            <h3>Node Details</h3>
            <button 
              className="close-btn"
              onClick={() => setSelectedNode(null)}
            >
              ×
            </button>
            <div className="detail-item">
              <strong>ID:</strong> {selectedNode.id}
            </div>
            <div className="detail-item">
              <strong>Label:</strong> {selectedNode.label}
            </div>
            <div className="detail-item">
              <strong>Type:</strong> {selectedNode.type}
            </div>
            {selectedNode.is_public !== undefined && (
              <div className="detail-item">
                <strong>Public:</strong> {selectedNode.is_public ? 'Yes' : 'No'}
              </div>
            )}
            {selectedNode.has_internet_access !== undefined && (
              <div className="detail-item">
                <strong>Internet Access:</strong> {selectedNode.has_internet_access ? 'Yes' : 'No'}
              </div>
            )}
            {selectedNode.resource_count !== undefined && (
              <div className="detail-item">
                <strong>Resources:</strong> {selectedNode.resource_count}
              </div>
            )}
          </div>
        )}
      </div>

      <div className="graph-legend">
        <h4>Legend</h4>
        <div className="legend-items">
          <div className="legend-item">
            <div className="legend-icon iam-role"></div>
            <span>IAM Role</span>
          </div>
          <div className="legend-item">
            <div className="legend-icon security-group"></div>
            <span>Security Group</span>
          </div>
          <div className="legend-item">
            <div className="legend-icon ec2"></div>
            <span>EC2 Instance</span>
          </div>
          <div className="legend-item">
            <div className="legend-icon lambda"></div>
            <span>Lambda Function</span>
          </div>
          <div className="legend-item">
            <div className="legend-icon internet"></div>
            <span>Internet</span>
          </div>
          <div className="legend-item">
            <div className="legend-icon risky"></div>
            <span>Risky (Red Border)</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default GraphView;
