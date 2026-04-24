import React, { useState, useEffect } from 'react';
import axios from 'axios';
import Dashboard from './components/Dashboard';
import './index.css';

function App() {
  const [leads, setLeads] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Load historical leads on startup
  useEffect(() => {
    const fetchLeads = async () => {
      try {
        const response = await axios.get('/leads');
        setLeads(response.data);
      } catch (err) {
        console.error("Failed to fetch leads", err);
      }
    };
    fetchLeads();
  }, []);

  const runAI = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get('/run');
      // Prepend new leads to the existing list and remove duplicates
      setLeads(prev => {
        const newLeads = response.data.filter(rl => !prev.some(pl => pl.lead.url === rl.lead.url));
        return [...newLeads, ...prev];
      });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen">
      <Dashboard leads={leads} loading={loading} error={error} onRunAI={runAI} />
    </div>
  );
}

export default App;
