import React, { useState, useEffect, useMemo } from 'react';
import axios from 'axios';
import {
  BarChart, Bar, PieChart, Pie, LineChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, Cell
} from 'recharts';
import './App.css';

const API_URL = 'http://localhost:8000';

// Professional color palette
const COLORS = [
  '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
  '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf',
  '#aec7e8', '#ffbb78', '#98df8a', '#ff9896', '#c5b0d5'
];

function App() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_URL}/api/warranty/data`);
      setData(response.data.data);
      setLoading(false);
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  };

  // Calculate analytics
  const analytics = useMemo(() => {
    if (!data.length) return null;

    // Assignment distribution
    const assignmentDist = data.reduce((acc, item) => {
      const status = item.assigned_flag || 'Unknown';
      acc[status] = (acc[status] || 0) + 1;
      return acc;
    }, {});

    // Issue status distribution
    const statusDist = data.reduce((acc, item) => {
      const status = item.issue_color_status || 'Unknown';
      acc[status] = (acc[status] || 0) + 1;
      return acc;
    }, {});

    // Top 10 issue clusters
    const clusterDist = data.reduce((acc, item) => {
      const cluster = item.rca_cluster_label_final || 'Unknown';
      acc[cluster] = (acc[cluster] || 0) + 1;
      return acc;
    }, {});
    const topClusters = Object.entries(clusterDist)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 10);

    // Top 10 vehicle models
    const modelDist = data.reduce((acc, item) => {
      const model = item.affected_vehicleproject_model || 'Unknown';
      acc[model] = (acc[model] || 0) + 1;
      return acc;
    }, {});
    const topModels = Object.entries(modelDist)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 10);

    // Top 10 ECUs
    const ecuDist = data.reduce((acc, item) => {
      const ecu = item.ecu || 'Unknown';
      acc[ecu] = (acc[ecu] || 0) + 1;
      return acc;
    }, {});
    const topECUs = Object.entries(ecuDist)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 10);

    // Category distribution
    const categoryDist = data.reduce((acc, item) => {
      const cat = item.category_rule_based || 'Other';
      acc[cat] = (acc[cat] || 0) + 1;
      return acc;
    }, {});

    // Model year distribution
    const yearDist = data.reduce((acc, item) => {
      const year = item.model_year || 'Unknown';
      acc[year] = (acc[year] || 0) + 1;
      return acc;
    }, {});

    return {
      total: data.length,
      assigned: assignmentDist['Assigned'] || 0,
      unassigned: assignmentDist['Unassigned'] || 0,
      assignmentData: Object.entries(assignmentDist).map(([name, value]) => ({ name, value })),
      statusData: Object.entries(statusDist).map(([name, value]) => ({ name, value })),
      clusterData: topClusters.map(([name, value]) => ({ name, value })),
      modelData: topModels.map(([name, value]) => ({ name: name.substring(0, 30), value })),
      ecuData: topECUs.map(([name, value]) => ({ name: name.substring(0, 40), value })),
      categoryData: Object.entries(categoryDist).map(([name, value]) => ({ name, value })),
      yearData: Object.entries(yearDist)
        .filter(([year]) => year !== 'Unknown' && !year.includes(';'))
        .sort((a, b) => b[0] - a[0])
        .slice(0, 10)
        .map(([name, value]) => ({ name, value }))
    };
  }, [data]);

  if (loading) {
    return (
      <div className="loading-screen">
        <h1>Loading Warranty Data...</h1>
        <div className="loading-spinner"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="error-screen">
        <h1>Connection Error</h1>
        <p>{error}</p>
        <p>Make sure the backend is running at {API_URL}</p>
      </div>
    );
  }

  if (!analytics) return null;

  return (
    <div className="App">
      {/* Header */}
      <header className="app-header">
        <h1>Warranty Analytics Dashboard</h1>
        <p className="subtitle">Comprehensive Issue Analysis & Insights</p>
        
        {/* KPI Cards */}
        <div className="stats-grid">
          <div className="stat-card">
            <h3>{analytics.total.toLocaleString()}</h3>
            <p>Total Issues</p>
          </div>
          <div className="stat-card">
            <h3>{analytics.assigned.toLocaleString()}</h3>
            <p>Assigned</p>
          </div>
          <div className="stat-card">
            <h3>{analytics.unassigned.toLocaleString()}</h3>
            <p>Unassigned</p>
          </div>
          <div className="stat-card">
            <h3>{((analytics.assigned / analytics.total) * 100).toFixed(1)}%</h3>
            <p>Assignment Rate</p>
          </div>
        </div>
      </header>

      {/* Tab Navigation */}
      <div className="tab-nav">
        <button 
          className={activeTab === 'overview' ? 'active' : ''}
          onClick={() => setActiveTab('overview')}
        >
          Overview
        </button>
        <button 
          className={activeTab === 'issues' ? 'active' : ''}
          onClick={() => setActiveTab('issues')}
        >
          Issue Analysis
        </button>
        <button 
          className={activeTab === 'vehicles' ? 'active' : ''}
          onClick={() => setActiveTab('vehicles')}
        >
          Vehicle & ECU
        </button>
      </div>

      {/* Main Content */}
      <main className="main-content">
        {activeTab === 'overview' && (
          <div className="dashboard-grid">
            {/* Assignment Distribution */}
            <div className="chart-card">
              <h3>Assignment Distribution</h3>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={analytics.assignmentData}
                    dataKey="value"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    outerRadius={100}
                    label={(entry) => `${entry.name}: ${entry.value.toLocaleString()}`}
                  >
                    {analytics.assignmentData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>

            {/* Issue Status Distribution */}
            <div className="chart-card">
              <h3>Issue Status Distribution</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={analytics.statusData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="value" fill="#1f77b4" />
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Top Issue Categories */}
            <div className="chart-card full-width">
              <h3>Issue Categories</h3>
              <ResponsiveContainer width="100%" height={400}>
                <BarChart data={analytics.categoryData} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" />
                  <YAxis dataKey="name" type="category" width={200} />
                  <Tooltip />
                  <Bar dataKey="value" fill="#2ca02c" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {activeTab === 'issues' && (
          <div className="dashboard-grid">
            {/* Top 10 Issue Clusters */}
            <div className="chart-card full-width">
              <h3>Top 10 Issue Types</h3>
              <ResponsiveContainer width="100%" height={500}>
                <BarChart data={analytics.clusterData} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" />
                  <YAxis dataKey="name" type="category" width={250} />
                  <Tooltip />
                  <Bar dataKey="value">
                    {analytics.clusterData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Issue Distribution Table */}
            <div className="chart-card full-width">
              <h3>Issue Details</h3>
              <div className="data-table">
                <table>
                  <thead>
                    <tr>
                      <th>#</th>
                      <th>Issue Type</th>
                      <th>Count</th>
                      <th>Percentage</th>
                    </tr>
                  </thead>
                  <tbody>
                    {analytics.clusterData.map((item, idx) => (
                      <tr key={idx}>
                        <td>{idx + 1}</td>
                        <td>{item.name}</td>
                        <td>{item.value.toLocaleString()}</td>
                        <td>{((item.value / analytics.total) * 100).toFixed(2)}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'vehicles' && (
          <div className="dashboard-grid">
            {/* Top 10 Vehicle Models */}
            <div className="chart-card full-width">
              <h3>Top 10 Vehicle Models</h3>
              <ResponsiveContainer width="100%" height={400}>
                <BarChart data={analytics.modelData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" angle={-45} textAnchor="end" height={150} />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="value" fill="#ff7f0e" />
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Model Year Distribution */}
            <div className="chart-card">
              <h3>Model Year Distribution</h3>
              <ResponsiveContainer width="100%" height={350}>
                <BarChart data={analytics.yearData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="value" fill="#9467bd" />
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Top 10 ECUs */}
            <div className="chart-card full-width">
              <h3>Top 10 ECUs by Issue Count</h3>
              <ResponsiveContainer width="100%" height={400}>
                <BarChart data={analytics.ecuData} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" />
                  <YAxis dataKey="name" type="category" width={300} />
                  <Tooltip />
                  <Bar dataKey="value" fill="#d62728" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
