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
  const [stats, setStats] = useState(null);
  
  // Drill-down state
  const [drillLevel, setDrillLevel] = useState(0);
  const [filters, setFilters] = useState({});
  const [breadcrumb, setBreadcrumb] = useState(['Total Issues']);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_URL}/api/warranty/data`);
      setData(response.data.data);
      
      const statsResponse = await axios.get(`${API_URL}/api/analytics/stats`);
      setStats(statsResponse.data);
      
      setLoading(false);
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  };

  // Filter data based on current filters
  const filteredData = useMemo(() => {
    let filtered = [...data];
    Object.entries(filters).forEach(([key, value]) => {
      filtered = filtered.filter(item => String(item[key]) === String(value));
    });
    return filtered;
  }, [data, filters]);

  const generateSankeyData = () => {
    if (!filteredData.length) return { nodes: [], links: [], nodeColors: [], linkColors: [] };

    const currentLevel = HIERARCHY[drillLevel];
    const { source, target } = currentLevel;

    let nodes = [];
    let links = [];
    let nodeColors = [];
    let linkColors = [];

    if (drillLevel === 0) {
      // Level 0: Total → Assignment Status
      const counts = {};
      filteredData.forEach(item => {
        const val = item[target] || 'Unknown';
        counts[val] = (counts[val] || 0) + 1;
      });

      nodes = [`Total Issues (${filteredData.length})`, ...Object.keys(counts).map(k => `${k} (${counts[k]})`)];
      nodeColors = ['#95a5a6', ...Object.keys(counts).map((_, idx) => COLORS[idx % COLORS.length])];
      
      links = Object.entries(counts).map(([key, count], idx) => ({
        source: 0,
        target: idx + 1,
        value: count,
        label: key
      }));
      
      linkColors = links.map((_, idx) => COLORS[idx % COLORS.length].replace(')', ', 0.3)').replace('rgb', 'rgba'));
    } else {
      // Levels 1-5: Source → Target
      const sourceField = source;
      const targetField = target;
      
      // Group by source and target
      const flowCounts = {};
      filteredData.forEach(item => {
        const srcVal = String(item[sourceField] || 'Unknown');
        const tgtVal = String(item[targetField] || 'Unknown');
        const key = `${srcVal}|||${tgtVal}`;
        flowCounts[key] = (flowCounts[key] || 0) + 1;
      });

      // Get unique sources and targets
      const sources = [...new Set(filteredData.map(item => String(item[sourceField] || 'Unknown')))];
      const targets = [...new Set(filteredData.map(item => String(item[targetField] || 'Unknown')))];
      
      // Create node labels with counts
      const sourceCounts = {};
      const targetCounts = {};
      filteredData.forEach(item => {
        const srcVal = String(item[sourceField] || 'Unknown');
        const tgtVal = String(item[targetField] || 'Unknown');
        sourceCounts[srcVal] = (sourceCounts[srcVal] || 0) + 1;
        targetCounts[tgtVal] = (targetCounts[tgtVal] || 0) + 1;
      });

      // Format labels - use formatClusterLabel for final level
      const isClusterLevel = targetField === 'rca_cluster_label_final';
      nodes = [
        ...sources.map(s => `${s} (${sourceCounts[s]})`),
        ...targets.map(t => {
          const displayLabel = isClusterLevel ? formatClusterLabel(t) : t;
          return `${displayLabel} (${targetCounts[t]})`;
        })
      ];

      // Assign colors
      nodeColors = [
        ...sources.map((_, idx) => COLORS[idx % COLORS.length]),
        ...targets.map((_, idx) => COLORS[(idx + sources.length) % COLORS.length])
      ];

      // Create links
      Object.entries(flowCounts).forEach(([key, count]) => {
        const [srcVal, tgtVal] = key.split('|||');
        const sourceIdx = sources.indexOf(srcVal);
        const targetIdx = sources.length + targets.indexOf(tgtVal);
        
        links.push({
          source: sourceIdx,
          target: targetIdx,
          value: count,
          sourceLabel: srcVal,
          targetLabel: tgtVal
        });
      });

      linkColors = links.map(link => {
        const color = nodeColors[link.source];
        return color.replace(')', ', 0.3)').replace('rgb', 'rgba').replace('#', 'rgba(');
      });
    }

    return { nodes, links, nodeColors, linkColors };
  };

  const sankeyData = generateSankeyData();

  const handleNodeClick = (event) => {
    if (!event.points || event.points.length === 0) return;
    
    const point = event.points[0];
    const pointIndex = point.pointNumber;
    const nodeLabel = sankeyData.nodes[pointIndex];
    
    // Extract value from label (remove count in parentheses at the end)
    const clickedValue = nodeLabel.replace(/\s*\(\d+\)\s*$/, '').trim();
    
    console.log('Clicked:', { 
      level: drillLevel, 
      nodeLabel, 
      clickedValue, 
      pointIndex,
      currentHierarchy: HIERARCHY[drillLevel]
    });

    if (drillLevel === 0) {
      // Level 0: Clicked on Total or Assignment Status
      if (pointIndex === 0) {
        // Clicked on "Total Issues" - reset
        handleReset();
        return;
      }
      
      // Clicked on assignment status (Assigned or Unassigned)
      const targetField = HIERARCHY[0].target;
      const newFilters = { [targetField]: clickedValue };
      setFilters(newFilters);
      setDrillLevel(1);
      setBreadcrumb(['Total Issues', clickedValue]);
    } else if (drillLevel < HIERARCHY.length - 1) {
      // Levels 1-5: Drill down further
      const currentLevel = HIERARCHY[drillLevel];
      const targetField = currentLevel.target;
      
      // Determine if clicked on source or target node
      const sourceCount = [...new Set(filteredData.map(item => String(item[currentLevel.source] || 'Unknown')))].length;
      
      if (pointIndex < sourceCount) {
        // Clicked on source node - don't drill down
        console.log('Clicked on source node, ignoring');
        return;
      }
      
      // Clicked on target node - drill down
      const newFilters = { ...filters, [targetField]: clickedValue };
      setFilters(newFilters);
      setDrillLevel(drillLevel + 1);
      setBreadcrumb([...breadcrumb, clickedValue]);
    }
  };

  const handleReset = () => {
    setDrillLevel(0);
    setFilters({});
    setBreadcrumb(['Total Issues']);
  };

  const handleBreadcrumbClick = (index) => {
    if (index === 0) {
      handleReset();
    } else {
      // Go back to specific level
      const newLevel = index;
      const newFilters = {};
      const newBreadcrumb = breadcrumb.slice(0, index + 1);
      
      // Rebuild filters up to that level
      for (let i = 0; i < newLevel; i++) {
        const field = HIERARCHY[i].target;
        newFilters[field] = breadcrumb[i + 1].split(' (')[0];
      }
      
      setDrillLevel(newLevel);
      setFilters(newFilters);
      setBreadcrumb(newBreadcrumb);
    }
  };

  if (loading) {
    return (
      <div className="loading-screen">
        <h1>⚙️ Loading Warranty Data...</h1>
        <div className="loading-spinner"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="error-screen">
        <h1>❌ Connection Error</h1>
        <p>{error}</p>
        <p>Make sure the backend is running at {API_URL}</p>
        <p style={{ marginTop: '1rem', fontSize: '0.9rem' }}>
          Run: <code style={{ background: 'rgba(0,0,0,0.2)', padding: '0.25rem 0.5rem', borderRadius: '4px' }}>
            uvicorn api.main:app --reload
          </code>
        </p>
      </div>
    );
  }

  return (
    <div className="App">
      <header className="app-header">
        <h1>Warranty Analytics Dashboard</h1>
        <p className="subtitle">Interactive Drill-Down Analysis</p>
        {stats && (
          <div className="stats-grid">
            <div className="stat-card">
              <h3>{stats.total_issues?.toLocaleString()}</h3>
              <p>Total Issues</p>
            </div>
            <div className="stat-card">
              <h3>{stats.assigned?.toLocaleString()}</h3>
              <p>Assigned</p>
            </div>
            <div className="stat-card">
              <h3>{stats.resolved?.toLocaleString()}</h3>
              <p>Resolved</p>
            </div>
            <div className="stat-card">
              <h3>{stats.unique_models}</h3>
              <p>Vehicle Models</p>
            </div>
          </div>
        )}
      </header>
      
      <main className="main-content">
        {/* Breadcrumb Navigation */}
        <div className="breadcrumb-nav">
          <strong>Navigation</strong>
          {breadcrumb.map((crumb, index) => (
            <React.Fragment key={index}>
              <button
                onClick={() => handleBreadcrumbClick(index)}
                className={`breadcrumb-btn ${index === breadcrumb.length - 1 ? 'active' : 'inactive'}`}
              >
                {crumb}
              </button>
              {index < breadcrumb.length - 1 && <span className="breadcrumb-arrow">→</span>}
            </React.Fragment>
          ))}
          {drillLevel > 0 && (
            <button onClick={handleReset} className="reset-btn">
              Reset
            </button>
          )}
        </div>

        {/* Current Level Info */}
        <div className="level-info">
          <h2>{HIERARCHY[drillLevel].title}</h2>
          <p>
            Level {drillLevel + 1} of {HIERARCHY.length} • 
            {filteredData.length.toLocaleString()} issues • 
            Click any node to drill down
          </p>
        </div>

        {/* Sankey Diagram */}
        <div className="sankey-container">
          <Plot
            data={[{
              type: 'sankey',
              node: {
                label: sankeyData.nodes,
                color: sankeyData.nodeColors,
                pad: 20,
                thickness: 30,
                line: {
                  color: '#34495e',
                  width: 1
                }
              },
              link: {
                source: sankeyData.links.map(l => l.source),
                target: sankeyData.links.map(l => l.target),
                value: sankeyData.links.map(l => l.value),
                color: sankeyData.linkColors
              }
            }]}
            layout={{
              title: {
                text: HIERARCHY[drillLevel].title,
                font: { size: 20, color: '#2c3e50' }
              },
              height: 700,
              font: { size: 14, family: 'Arial, sans-serif' },
              paper_bgcolor: 'white',
              plot_bgcolor: 'white'
            }}
            config={{ 
              responsive: true,
              displayModeBar: true,
              displaylogo: false
            }}
            style={{ width: '100%', height: '700px' }}
            onClick={handleNodeClick}
          />
        </div>
        
        {/* Data Summary */}
        <div className="data-summary">
          <h3>Summary</h3>
          <div className="summary-grid">
            <div className="summary-item">
              <strong>Total Records</strong>
              <span>{data.length.toLocaleString()}</span>
            </div>
            <div className="summary-item">
              <strong>Filtered Records</strong>
              <span>{filteredData.length.toLocaleString()}</span>
            </div>
            <div className="summary-item">
              <strong>Drill Level</strong>
              <span>{drillLevel + 1} / {HIERARCHY.length}</span>
            </div>
            <div className="summary-item">
              <strong>Active Filters</strong>
              <span>{Object.keys(filters).length}</span>
            </div>
          </div>
          {Object.keys(filters).length > 0 && (
            <div className="filters-box">
              <strong>Applied Filters</strong>
              <ul>
                {Object.entries(filters).map(([key, value]) => (
                  <li key={key}>
                    {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}: <strong>{value}</strong>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default App;
