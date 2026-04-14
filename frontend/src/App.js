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
  const [drillDownData, setDrillDownData] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [modalFilters, setModalFilters] = useState({});

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

  // Drill-down handlers
  const handleChartClick = (field, value) => {
    let filtered;
    
    // Special handling for normalized_status
    if (field === 'normalized_status') {
      filtered = data.filter(item => {
        const status = item.normalized_status || 
                      (item.issue_color_status && ['Dark Green', 'Cancelled'].includes(item.issue_color_status) ? 'Closed' : 'Open');
        return status === value;
      });
    } else if (field === 'affected_vehicleproject_model') {
      // Check if value is in semicolon-separated list
      filtered = data.filter(item => {
        const modelStr = item.affected_vehicleproject_model || '';
        const models = modelStr.includes(';') 
          ? modelStr.split(';').map(m => m.trim()) 
          : [modelStr];
        return models.includes(value);
      });
    } else if (field === 'model_year') {
      // Check if value is in semicolon-separated list
      filtered = data.filter(item => {
        const yearStr = String(item.model_year || '');
        const years = yearStr.includes(';') 
          ? yearStr.split(';').map(y => y.trim()) 
          : [yearStr];
        return years.includes(String(value));
      });
    } else {
      filtered = data.filter(item => String(item[field]) === String(value));
    }
    
    // Extract unique values for filters
    const filterOptions = {
      normalizedStatus: [...new Set(filtered.map(item => {
        return item.normalized_status || 
               (item.issue_color_status && ['Dark Green', 'Cancelled'].includes(item.issue_color_status) ? 'Closed' : 'Open');
      }))].sort(),
      status: [...new Set(filtered.map(item => item.issue_color_status).filter(Boolean))].sort(),
      category: [...new Set(filtered.map(item => item.category_rule_based).filter(Boolean))].sort(),
      enhancedType: [...new Set(filtered.map(item => item.issue_type_enhanced).filter(v => v && v !== 'Unknown'))].sort().slice(0, 50),
      systemArea: [...new Set(filtered.map(item => item.system_area).filter(v => v && v !== 'Unknown' && v !== null))].sort(),
      component: [...new Set(filtered.map(item => item.affected_component).filter(v => v && v !== 'Unknown' && v !== null))].sort(),
      problemType: [...new Set(filtered.map(item => item.problem_type).filter(v => v && v !== 'Unknown'))].sort(),
      model: [...new Set(filtered.map(item => item.affected_vehicleproject_model).filter(Boolean))].sort(),
      year: [...new Set(filtered.map(item => item.model_year).filter(Boolean))].sort(),
      ecu: [...new Set(filtered.map(item => item.ecu).filter(Boolean))].sort()
    };
    
    setDrillDownData({
      title: `${value} - Detailed View`,
      field,
      value,
      allRecords: filtered,
      count: filtered.length,
      records: filtered.slice(0, 100),
      filterOptions
    });
    setModalFilters({});
    setShowModal(true);
  };

  const closeModal = () => {
    setShowModal(false);
    setDrillDownData(null);
    setModalFilters({});
  };

  const handleModalFilterChange = (filterType, value) => {
    const newFilters = { ...modalFilters };
    if (value === '') {
      delete newFilters[filterType];
    } else {
      newFilters[filterType] = value;
    }
    setModalFilters(newFilters);
  };

  // Apply modal filters
  const getFilteredModalRecords = () => {
    if (!drillDownData) return [];
    
    let filtered = drillDownData.allRecords;
    
    if (modalFilters.normalizedStatus) {
      filtered = filtered.filter(item => {
        const status = item.normalized_status || 
                      (item.issue_color_status && ['Dark Green', 'Cancelled'].includes(item.issue_color_status) ? 'Closed' : 'Open');
        return status === modalFilters.normalizedStatus;
      });
    }
    if (modalFilters.status) {
      filtered = filtered.filter(item => item.issue_color_status === modalFilters.status);
    }
    if (modalFilters.category) {
      filtered = filtered.filter(item => item.category_rule_based === modalFilters.category);
    }
    if (modalFilters.enhancedType) {
      filtered = filtered.filter(item => item.issue_type_enhanced === modalFilters.enhancedType);
    }
    if (modalFilters.systemArea) {
      filtered = filtered.filter(item => item.system_area === modalFilters.systemArea);
    }
    if (modalFilters.component) {
      filtered = filtered.filter(item => item.affected_component === modalFilters.component);
    }
    if (modalFilters.problemType) {
      filtered = filtered.filter(item => item.problem_type === modalFilters.problemType);
    }
    if (modalFilters.model) {
      filtered = filtered.filter(item => item.affected_vehicleproject_model === modalFilters.model);
    }
    if (modalFilters.year) {
      filtered = filtered.filter(item => String(item.model_year) === String(modalFilters.year));
    }
    if (modalFilters.ecu) {
      filtered = filtered.filter(item => item.ecu === modalFilters.ecu);
    }
    
    return filtered;
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

    // Issue status distribution (color status)
    const statusDist = data.reduce((acc, item) => {
      const status = item.issue_color_status || 'Unknown';
      acc[status] = (acc[status] || 0) + 1;
      return acc;
    }, {});

    // Normalized status distribution (Open/Closed)
    const normalizedStatusDist = data.reduce((acc, item) => {
      const status = item.normalized_status || 
                     (item.issue_color_status && ['Dark Green', 'Cancelled'].includes(item.issue_color_status) ? 'Closed' : 'Open');
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

    // Top 10 vehicle models (count each model in semicolon-separated list)
    const modelDist = data.reduce((acc, item) => {
      const modelStr = item.affected_vehicleproject_model || 'Unknown';
      // Split by semicolon and count each model
      const models = modelStr.includes(';') 
        ? modelStr.split(';').map(m => m.trim()) 
        : [modelStr];
      
      models.forEach(model => {
        acc[model] = (acc[model] || 0) + 1;
      });
      return acc;
    }, {});
    const topModels = Object.entries(modelDist)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 10);

    // Model year distribution (count each year in semicolon-separated list)
    const yearDist = data.reduce((acc, item) => {
      const yearStr = String(item.model_year || 'Unknown');
      // Split by semicolon and count each year
      const years = yearStr.includes(';') 
        ? yearStr.split(';').map(y => y.trim()) 
        : [yearStr];
      
      years.forEach(year => {
        acc[year] = (acc[year] || 0) + 1;
      });
      return acc;
    }, {});
    const topECUs = Object.entries(data.reduce((acc, item) => {
      const ecu = item.ecu || 'Unknown';
      acc[ecu] = (acc[ecu] || 0) + 1;
      return acc;
    }, {}))
      .sort((a, b) => b[1] - a[1])
      .slice(0, 10);

    // Category distribution
    const categoryDist = data.reduce((acc, item) => {
      const cat = item.category_rule_based || 'Other';
      acc[cat] = (acc[cat] || 0) + 1;
      return acc;
    }, {});

    // Enhanced issue type distribution (top 15)
    const enhancedTypeDist = data.reduce((acc, item) => {
      const type = item.issue_type_enhanced || 'Unknown';
      acc[type] = (acc[type] || 0) + 1;
      return acc;
    }, {});
    const topEnhancedTypes = Object.entries(enhancedTypeDist)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 15);

    // System area distribution
    const systemAreaDist = data.reduce((acc, item) => {
      const system = item.system_area || 'Unknown';
      if (system !== 'Unknown') {
        acc[system] = (acc[system] || 0) + 1;
      }
      return acc;
    }, {});

    // Affected component distribution (top 10)
    const componentDist = data.reduce((acc, item) => {
      const component = item.affected_component || 'Unknown';
      if (component !== 'Unknown') {
        acc[component] = (acc[component] || 0) + 1;
      }
      return acc;
    }, {});
    const topComponents = Object.entries(componentDist)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 10);

    // Problem type distribution
    const problemTypeDist = data.reduce((acc, item) => {
      const problem = item.problem_type || 'Unknown';
      if (problem !== 'Unknown') {
        acc[problem] = (acc[problem] || 0) + 1;
      }
      return acc;
    }, {});

    return {
      total: data.length,
      assigned: assignmentDist['Assigned'] || 0,
      unassigned: assignmentDist['Unassigned'] || 0,
      open: normalizedStatusDist['Open'] || 0,
      closed: normalizedStatusDist['Closed'] || 0,
      assignmentData: Object.entries(assignmentDist).map(([name, value]) => ({ name, value })),
      statusData: Object.entries(statusDist).map(([name, value]) => ({ name, value })),
      normalizedStatusData: Object.entries(normalizedStatusDist).map(([name, value]) => ({ name, value })),
      clusterData: topClusters.map(([name, value]) => ({ name, value })),
      modelData: topModels.map(([name, value]) => ({ name: name.substring(0, 30), value })),
      ecuData: topECUs.map(([name, value]) => ({ name: name.substring(0, 40), value })),
      categoryData: Object.entries(categoryDist).map(([name, value]) => ({ name, value })),
      enhancedTypeData: topEnhancedTypes.map(([name, value]) => ({ name, value })),
      systemAreaData: Object.entries(systemAreaDist).map(([name, value]) => ({ name, value })),
      componentData: topComponents.map(([name, value]) => ({ name, value })),
      problemTypeData: Object.entries(problemTypeDist).map(([name, value]) => ({ name, value })),
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
            <h3 style={{color: '#2ecc71'}}>{analytics.open.toLocaleString()}</h3>
            <p>Open Issues</p>
          </div>
          <div className="stat-card">
            <h3 style={{color: '#95a5a6'}}>{analytics.closed.toLocaleString()}</h3>
            <p>Closed Issues</p>
          </div>
          <div className="stat-card">
            <h3>{analytics.assigned.toLocaleString()}</h3>
            <p>Assigned</p>
          </div>
          <div className="stat-card">
            <h3>{((analytics.closed / analytics.total) * 100).toFixed(1)}%</h3>
            <p>Closure Rate</p>
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
          className={activeTab === 'nlp' ? 'active' : ''}
          onClick={() => setActiveTab('nlp')}
        >
          NLP Analysis
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
            <div className="chart-card clickable-chart">
              <h3>Assignment Distribution <span className="click-hint">Click to drill down</span></h3>
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
                    onClick={(data) => handleChartClick('assigned_flag', data.name)}
                    cursor="pointer"
                  >
                    {analytics.assignmentData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>

            {/* Normalized Status Distribution (Open/Closed) */}
            <div className="chart-card clickable-chart">
              <h3>Issue Status (Open/Closed) <span className="click-hint">Click bars</span></h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={analytics.normalizedStatusData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Bar 
                    dataKey="value"
                    onClick={(data) => {
                      // Filter by normalized_status or derive from issue_color_status
                      const filtered = data.filter(item => {
                        const status = item.normalized_status || 
                                     (item.issue_color_status && ['Dark Green', 'Cancelled'].includes(item.issue_color_status) ? 'Closed' : 'Open');
                        return status === data.name;
                      });
                      handleChartClick('normalized_status', data.name);
                    }}
                    cursor="pointer"
                  >
                    {analytics.normalizedStatusData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.name === 'Open' ? '#2ecc71' : '#95a5a6'} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Top Issue Categories */}
            <div className="chart-card full-width clickable-chart">
              <h3>Issue Categories <span className="click-hint">Click bars</span></h3>
              <ResponsiveContainer width="100%" height={400}>
                <BarChart data={analytics.categoryData} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" />
                  <YAxis dataKey="name" type="category" width={200} />
                  <Tooltip />
                  <Bar 
                    dataKey="value" 
                    fill="#2ca02c"
                    onClick={(data) => handleChartClick('category_rule_based', data.name)}
                    cursor="pointer"
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {activeTab === 'issues' && (
          <div className="dashboard-grid">
            {/* Top 10 Issue Clusters */}
            <div className="chart-card full-width clickable-chart">
              <h3>Top 10 Issue Types <span className="click-hint">Click bars</span></h3>
              <ResponsiveContainer width="100%" height={500}>
                <BarChart data={analytics.clusterData} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" />
                  <YAxis dataKey="name" type="category" width={250} />
                  <Tooltip />
                  <Bar 
                    dataKey="value"
                    onClick={(data) => handleChartClick('rca_cluster_label_final', data.name)}
                    cursor="pointer"
                  >
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

        {activeTab === 'nlp' && (
          <div className="dashboard-grid">
            {/* System Area Distribution */}
            <div className="chart-card clickable-chart">
              <h3>System Area Distribution <span className="click-hint">Click to drill down</span></h3>
              <ResponsiveContainer width="100%" height={350}>
                <PieChart>
                  <Pie
                    data={analytics.systemAreaData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({name, percent}) => `${name}: ${(percent * 100).toFixed(0)}%`}
                    outerRadius={100}
                    fill="#8884d8"
                    dataKey="value"
                    onClick={(data) => handleChartClick('system_area', data.name)}
                    cursor="pointer"
                  >
                    {analytics.systemAreaData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>

            {/* Problem Type Distribution */}
            <div className="chart-card clickable-chart">
              <h3>Problem Type Distribution <span className="click-hint">Click bars</span></h3>
              <ResponsiveContainer width="100%" height={350}>
                <BarChart data={analytics.problemTypeData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} />
                  <YAxis />
                  <Tooltip />
                  <Bar 
                    dataKey="value" 
                    fill="#e377c2"
                    onClick={(data) => handleChartClick('problem_type', data.name)}
                    cursor="pointer"
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Top 10 Affected Components */}
            <div className="chart-card full-width clickable-chart">
              <h3>Top 10 Affected Components <span className="click-hint">Click bars</span></h3>
              <ResponsiveContainer width="100%" height={400}>
                <BarChart data={analytics.componentData} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" />
                  <YAxis dataKey="name" type="category" width={150} />
                  <Tooltip />
                  <Bar 
                    dataKey="value" 
                    fill="#17becf"
                    onClick={(data) => handleChartClick('affected_component', data.name)}
                    cursor="pointer"
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Top 15 Enhanced Issue Types */}
            <div className="chart-card full-width clickable-chart">
              <h3>Top 15 Enhanced Issue Types (NLP-Generated) <span className="click-hint">Click bars</span></h3>
              <ResponsiveContainer width="100%" height={500}>
                <BarChart data={analytics.enhancedTypeData} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" />
                  <YAxis dataKey="name" type="category" width={350} />
                  <Tooltip />
                  <Bar 
                    dataKey="value" 
                    fill="#bcbd22"
                    onClick={(data) => handleChartClick('issue_type_enhanced', data.name)}
                    cursor="pointer"
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {activeTab === 'vehicles' && (
          <div className="dashboard-grid">
            {/* Top 10 Vehicle Models */}
            <div className="chart-card full-width clickable-chart">
              <h3>Top 10 Vehicle Models <span className="click-hint">Click bars</span></h3>
              <ResponsiveContainer width="100%" height={400}>
                <BarChart data={analytics.modelData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" angle={-45} textAnchor="end" height={150} />
                  <YAxis />
                  <Tooltip />
                  <Bar 
                    dataKey="value" 
                    fill="#ff7f0e"
                    onClick={(data) => handleChartClick('affected_vehicleproject_model', data.name)}
                    cursor="pointer"
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Model Year Distribution */}
            <div className="chart-card clickable-chart">
              <h3>Model Year Distribution <span className="click-hint">Click bars</span></h3>
              <ResponsiveContainer width="100%" height={350}>
                <BarChart data={analytics.yearData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Bar 
                    dataKey="value" 
                    fill="#9467bd"
                    onClick={(data) => handleChartClick('model_year', data.name)}
                    cursor="pointer"
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Top 10 ECUs */}
            <div className="chart-card full-width clickable-chart">
              <h3>Top 10 ECUs by Issue Count <span className="click-hint">Click bars</span></h3>
              <ResponsiveContainer width="100%" height={400}>
                <BarChart data={analytics.ecuData} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" />
                  <YAxis dataKey="name" type="category" width={300} />
                  <Tooltip />
                  <Bar 
                    dataKey="value" 
                    fill="#d62728"
                    onClick={(data) => handleChartClick('ecu', data.name)}
                    cursor="pointer"
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}
      </main>

      {/* Drill-Down Modal */}
      {showModal && drillDownData && (() => {
        const filteredRecords = getFilteredModalRecords();
        const displayRecords = filteredRecords.slice(0, 100);
        
        return (
          <div className="modal-overlay" onClick={closeModal}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
              <div className="modal-header">
                <h2>{drillDownData.title}</h2>
                <button className="close-btn" onClick={closeModal}>×</button>
              </div>
              <div className="modal-body">
                <div className="modal-stats">
                  <p><strong>Total Records:</strong> {drillDownData.count.toLocaleString()}</p>
                  <p><strong>Filtered:</strong> {filteredRecords.length.toLocaleString()}</p>
                  <p><strong>Showing:</strong> First {Math.min(100, filteredRecords.length)} records</p>
                </div>

                {/* Filter Controls */}
                <div className="modal-filters">
                  <h4>Filter Results</h4>
                  <div className="filter-grid">
                    {/* Normalized Status Filter (Open/Closed) */}
                    <div className="filter-item">
                      <label>Issue Status</label>
                      <select 
                        value={modalFilters.normalizedStatus || ''} 
                        onChange={(e) => handleModalFilterChange('normalizedStatus', e.target.value)}
                      >
                        <option value="">All (Open/Closed)</option>
                        {drillDownData.filterOptions.normalizedStatus.map(opt => (
                          <option key={opt} value={opt}>{opt}</option>
                        ))}
                      </select>
                    </div>

                    {/* Color Status Filter */}
                    <div className="filter-item">
                      <label>Color Status</label>
                      <select 
                        value={modalFilters.status || ''} 
                        onChange={(e) => handleModalFilterChange('status', e.target.value)}
                      >
                        <option value="">All Color Statuses</option>
                        {drillDownData.filterOptions.status.map(opt => (
                          <option key={opt} value={opt}>{opt}</option>
                        ))}
                      </select>
                    </div>

                    {/* Category Filter */}
                    <div className="filter-item">
                      <label>Category</label>
                      <select 
                        value={modalFilters.category || ''} 
                        onChange={(e) => handleModalFilterChange('category', e.target.value)}
                      >
                        <option value="">All Categories</option>
                        {drillDownData.filterOptions.category.map(opt => (
                          <option key={opt} value={opt}>{opt}</option>
                        ))}
                      </select>
                    </div>

                    {/* System Area Filter */}
                    <div className="filter-item">
                      <label>System Area</label>
                      <select 
                        value={modalFilters.systemArea || ''} 
                        onChange={(e) => handleModalFilterChange('systemArea', e.target.value)}
                      >
                        <option value="">All Systems</option>
                        {drillDownData.filterOptions.systemArea && drillDownData.filterOptions.systemArea.map(opt => (
                          <option key={opt} value={opt}>{opt}</option>
                        ))}
                      </select>
                    </div>

                    {/* Component Filter */}
                    <div className="filter-item">
                      <label>Component</label>
                      <select 
                        value={modalFilters.component || ''} 
                        onChange={(e) => handleModalFilterChange('component', e.target.value)}
                      >
                        <option value="">All Components</option>
                        {drillDownData.filterOptions.component && drillDownData.filterOptions.component.map(opt => (
                          <option key={opt} value={opt}>{opt}</option>
                        ))}
                      </select>
                    </div>

                    {/* Problem Type Filter */}
                    <div className="filter-item">
                      <label>Problem Type</label>
                      <select 
                        value={modalFilters.problemType || ''} 
                        onChange={(e) => handleModalFilterChange('problemType', e.target.value)}
                      >
                        <option value="">All Problem Types</option>
                        {drillDownData.filterOptions.problemType && drillDownData.filterOptions.problemType.map(opt => (
                          <option key={opt} value={opt}>{opt}</option>
                        ))}
                      </select>
                    </div>

                    {/* Enhanced Issue Type Filter */}
                    <div className="filter-item">
                      <label>Enhanced Type</label>
                      <select 
                        value={modalFilters.enhancedType || ''} 
                        onChange={(e) => handleModalFilterChange('enhancedType', e.target.value)}
                      >
                        <option value="">All Enhanced Types</option>
                        {drillDownData.filterOptions.enhancedType && drillDownData.filterOptions.enhancedType.map(opt => (
                          <option key={opt} value={opt}>{opt.substring(0, 50)}</option>
                        ))}
                      </select>
                    </div>

                    {/* Model Filter */}
                    <div className="filter-item">
                      <label>Vehicle Model</label>
                      <select 
                        value={modalFilters.model || ''} 
                        onChange={(e) => handleModalFilterChange('model', e.target.value)}
                      >
                        <option value="">All Models</option>
                        {drillDownData.filterOptions.model.slice(0, 50).map(opt => (
                          <option key={opt} value={opt}>{opt.substring(0, 40)}</option>
                        ))}
                      </select>
                    </div>

                    {/* Year Filter */}
                    <div className="filter-item">
                      <label>Model Year</label>
                      <select 
                        value={modalFilters.year || ''} 
                        onChange={(e) => handleModalFilterChange('year', e.target.value)}
                      >
                        <option value="">All Years</option>
                        {drillDownData.filterOptions.year.map(opt => (
                          <option key={opt} value={opt}>{opt}</option>
                        ))}
                      </select>
                    </div>

                    {/* ECU Filter */}
                    <div className="filter-item">
                      <label>ECU</label>
                      <select 
                        value={modalFilters.ecu || ''} 
                        onChange={(e) => handleModalFilterChange('ecu', e.target.value)}
                      >
                        <option value="">All ECUs</option>
                        {drillDownData.filterOptions.ecu.slice(0, 50).map(opt => (
                          <option key={opt} value={opt}>{opt.substring(0, 40)}</option>
                        ))}
                      </select>
                    </div>

                    {/* Clear Filters Button */}
                    {Object.keys(modalFilters).length > 0 && (
                      <div className="filter-item">
                        <label>&nbsp;</label>
                        <button 
                          className="clear-filters-btn"
                          onClick={() => setModalFilters({})}
                        >
                          Clear All Filters
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              
              <div className="modal-table-container">
                <table className="modal-table">
                  <thead>
                    <tr>
                      <th>#</th>
                      <th>Issue Number</th>
                      <th>Issue Type</th>
                      <th>Category</th>
                      <th>Status</th>
                      <th>Vehicle Model</th>
                      <th>Year</th>
                      <th>ECU</th>
                      <th>Assigned</th>
                    </tr>
                  </thead>
                  <tbody>
                    {displayRecords.map((record, idx) => (
                      <tr key={idx}>
                        <td>{idx + 1}</td>
                        <td title={record.issue_number || 'No Issue Number'}>
                          {record.issue_number ? record.issue_number.substring(0, 20) : '-'}
                        </td>
                        <td title={record.rca_cluster_label_final || 'Unknown'}>
                          {(record.rca_cluster_label_final || 'Unknown').substring(0, 35)}
                        </td>
                        <td title={record.category_rule_based || 'Other'}>
                          <span style={{fontSize: '0.85rem', color: '#667eea'}}>
                            {(record.category_rule_based || 'Other').substring(0, 25)}
                          </span>
                        </td>
                        <td>
                          <span className={`status-badge status-${(record.issue_color_status || '').toLowerCase().replace(/\s+/g, '-')}`}>
                            {record.issue_color_status || '-'}
                          </span>
                        </td>
                        <td title={record.affected_vehicleproject_model || 'Unknown'}>
                          {(record.affected_vehicleproject_model || 'Unknown').substring(0, 25)}
                        </td>
                        <td>{record.model_year || '-'}</td>
                        <td title={record.ecu || 'No ECU Assigned'}>
                          {record.ecu ? record.ecu.substring(0, 25) : <span style={{color: '#999', fontStyle: 'italic'}}>No ECU</span>}
                        </td>
                        <td>
                          <span className={`assignment-badge ${(record.assigned_flag || '').toLowerCase()}`}>
                            {record.assigned_flag || '-'}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
        );
      })()}
    </div>
  );
}

export default App;
