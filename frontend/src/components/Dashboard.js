import React from 'react';
import { Activity, Users, Zap, Bot, Play } from 'lucide-react';
import LeadCard from './LeadCard';

const Dashboard = ({ leads, loading, error, onRunAI }) => {
  const averageScore = leads.length 
    ? (leads.reduce((acc, curr) => acc + curr.lead.score, 0) / leads.length).toFixed(2) 
    : 0;

  return (
    <div style={{ padding: '2rem', maxWidth: '1200px', margin: '0 auto' }}>
      {/* Header */}
      <header className="animate-fade-up" style={{ marginBottom: '3rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ fontSize: '2.5rem', fontWeight: 700, marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <Bot color="var(--accent-primary)" size={40} />
            Glambot & 360 Booth Sales AI
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '1.1rem' }}>Autonomous lead generation & outreach.</p>
        </div>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          {loading && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--accent-primary)' }} className="animate-pulse">
              <Zap size={20} /> <span style={{ fontWeight: 500 }}>AI is processing...</span>
            </div>
          )}
          <button 
            onClick={onRunAI}
            disabled={loading}
            style={{
              background: 'linear-gradient(135deg, var(--accent-primary), #0284c7)',
              color: '#000',
              border: 'none',
              padding: '0.75rem 1.5rem',
              borderRadius: '8px',
              fontWeight: 700,
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              cursor: loading ? 'not-allowed' : 'pointer',
              opacity: loading ? 0.7 : 1,
              transition: 'transform 0.2s, box-shadow 0.2s',
              boxShadow: '0 4px 14px 0 rgba(0, 240, 255, 0.39)',
              fontFamily: 'inherit'
            }}
            onMouseEnter={(e) => !loading && (e.currentTarget.style.transform = 'translateY(-2px)')}
            onMouseLeave={(e) => !loading && (e.currentTarget.style.transform = 'translateY(0)')}
          >
            <Play size={18} />
            Generate Leads & Messages
          </button>
        </div>
      </header>

      {/* Error State */}
      {error && (
        <div className="glass-panel animate-fade-up" style={{ padding: '1.5rem', borderColor: 'rgba(239, 68, 68, 0.3)', backgroundColor: 'rgba(239, 68, 68, 0.05)', color: '#ef4444', marginBottom: '2rem' }}>
          <strong>System Error:</strong> {error}
        </div>
      )}

      {/* Stats Row */}
      <div className="animate-fade-up" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1.5rem', marginBottom: '3rem', animationDelay: '0.1s' }}>
        <div className="glass-panel" style={{ padding: '1.5rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{ background: 'rgba(0, 240, 255, 0.1)', padding: '1rem', borderRadius: '12px' }}>
            <Users color="var(--accent-primary)" size={24} />
          </div>
          <div>
            <div style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '0.25rem' }}>Total Leads Processed</div>
            <div style={{ fontSize: '1.8rem', fontWeight: 600 }}>{leads.length || (loading ? '-' : 0)}</div>
          </div>
        </div>
        
        <div className="glass-panel" style={{ padding: '1.5rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{ background: 'rgba(139, 92, 246, 0.1)', padding: '1rem', borderRadius: '12px' }}>
            <Activity color="var(--accent-secondary)" size={24} />
          </div>
          <div>
            <div style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '0.25rem' }}>Average Lead Score</div>
            <div style={{ fontSize: '1.8rem', fontWeight: 600 }}>{averageScore}</div>
          </div>
        </div>
      </div>

      {/* Leads Grid */}
      <h2 className="animate-fade-up" style={{ fontSize: '1.5rem', marginBottom: '1.5rem', fontWeight: 600, animationDelay: '0.2s' }}>Hot AI Leads</h2>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))', gap: '1.5rem' }}>
        {leads.map((item, idx) => (
          <div key={idx} className="animate-fade-up" style={{ animationDelay: `${0.3 + (idx * 0.1)}s` }}>
            <LeadCard leadData={item.lead} message={item.message} />
          </div>
        ))}
        {!loading && leads.length === 0 && !error && (
          <div style={{ color: 'var(--text-secondary)', gridColumn: '1 / -1', textAlign: 'center', padding: '3rem', border: '1px dashed var(--card-border)', borderRadius: '12px' }}>
            Click "Generate Leads & Messages" to run the AI system and fetch your hot leads.
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;
