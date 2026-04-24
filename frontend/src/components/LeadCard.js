import React from 'react';
import { MapPin, Target, Send } from 'lucide-react';

const LeadCard = ({ leadData, message }) => {
  // Determine score color
  const getScoreColor = (score) => {
    if (score >= 0.8) return '#10b981'; // Green
    if (score >= 0.6) return '#f59e0b'; // Yellow
    return '#ef4444'; // Red
  };

  const handleSend = () => {
    const subject = encodeURIComponent("Elevate Your Events with Glambot 360 Booth");
    const body = encodeURIComponent(message);
    window.location.href = `mailto:?subject=${subject}&body=${body}`;
  };

  const scoreColor = getScoreColor(leadData.score);

  return (
    <div className="glass-panel" style={{ 
      padding: '1.5rem', 
      display: 'flex', 
      flexDirection: 'column', 
      gap: '1.25rem',
      height: '100%',
      transition: 'transform 0.2s ease, box-shadow 0.2s ease',
      cursor: 'default'
    }}
    onMouseEnter={(e) => {
      e.currentTarget.style.transform = 'translateY(-4px)';
      e.currentTarget.style.boxShadow = '0 10px 40px -10px rgba(0,0,0,0.5)';
      e.currentTarget.style.borderColor = 'rgba(255,255,255,0.15)';
    }}
    onMouseLeave={(e) => {
      e.currentTarget.style.transform = 'none';
      e.currentTarget.style.boxShadow = 'none';
      e.currentTarget.style.borderColor = 'var(--card-border)';
    }}>
      
      {/* Card Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h3 style={{ fontSize: '1.25rem', fontWeight: 600, marginBottom: '0.25rem' }}>{leadData.name}</h3>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
            <MapPin size={14} />
            <span>{leadData.location || 'Unknown Location'}</span>
          </div>
        </div>
        
        {/* Score Badge */}
        <div style={{ 
          display: 'flex', 
          alignItems: 'center', 
          gap: '0.35rem', 
          background: `${scoreColor}15`, 
          color: scoreColor, 
          padding: '0.35rem 0.75rem', 
          borderRadius: '20px',
          fontWeight: 600,
          fontSize: '0.9rem',
          border: `1px solid ${scoreColor}30`
        }}>
          <Target size={16} />
          <span>{(leadData.score * 100).toFixed(0)}%</span>
        </div>
      </div>

      {/* Divider */}
      <div style={{ height: '1px', background: 'var(--card-border)', margin: '0.5rem 0' }}></div>

      {/* AI Generated Message */}
      <div style={{ flex: 1 }}>
        <div style={{ fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-secondary)', marginBottom: '0.5rem', fontWeight: 500 }}>
          AI Generated Pitch
        </div>
        <p style={{ fontSize: '0.95rem', lineHeight: 1.5, color: '#E2E8F0', fontStyle: 'italic', background: 'rgba(0,0,0,0.2)', padding: '1rem', borderRadius: '8px', borderLeft: '3px solid var(--accent-secondary)' }}>
          "{message}"
        </p>
      </div>

      {/* Action Button */}
      <button 
        onClick={handleSend}
        style={{
          marginTop: 'auto',
          background: 'linear-gradient(135deg, var(--accent-secondary), #6d28d9)',
          color: 'white',
          border: 'none',
          padding: '0.75rem',
          borderRadius: '8px',
          fontWeight: 600,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '0.5rem',
          cursor: 'pointer',
          transition: 'opacity 0.2s',
          fontFamily: 'inherit'
        }}
        onMouseEnter={(e) => e.currentTarget.style.opacity = 0.9}
        onMouseLeave={(e) => e.currentTarget.style.opacity = 1}>
        <Send size={16} />
        Send Outreach
      </button>

    </div>
  );
};

export default LeadCard;
