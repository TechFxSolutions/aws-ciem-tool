/**
 * Main App Component
 * Routes and navigation for AWS CIEM Tool
 */

import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import Dashboard from './components/Dashboard';
import GraphView from './components/GraphView';
import ScanForm from './components/ScanForm';
import './App.css';

function App() {
  return (
    <Router>
      <div className="app">
        <nav className="navbar">
          <div className="nav-brand">
            <h2>AWS CIEM Tool</h2>
          </div>
          <div className="nav-links">
            <Link to="/" className="nav-link">Dashboard</Link>
            <Link to="/scan" className="nav-link">New Scan</Link>
            <Link to="/graph" className="nav-link">Graph View</Link>
            <a 
              href="http://localhost:8000/docs" 
              className="nav-link" 
              target="_blank" 
              rel="noopener noreferrer"
            >
              API Docs
            </a>
          </div>
        </nav>

        <main className="main-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/scan" element={<ScanForm />} />
            <Route path="/graph" element={<GraphView />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

function NotFound() {
  return (
    <div className="not-found">
      <h1>404 - Page Not Found</h1>
      <p>The page you're looking for doesn't exist.</p>
      <Link to="/" className="btn-primary">Go to Dashboard</Link>
    </div>
  );
}

export default App;
