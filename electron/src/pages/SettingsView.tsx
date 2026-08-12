import React, { useState, useEffect } from 'react';
import { Save, RefreshCw } from 'lucide-react';

export const SettingsView = () => {
  const [settings, setSettings] = useState<any>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');

  const fetchSettings = async () => {
    setLoading(true);
    try {
      const res = await fetch('http://127.0.0.1:8000/api/settings');
      const data = await res.json();
      setSettings(data);
    } catch (err) {
      console.error(err);
      setMessage('Failed to load settings');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSettings();
  }, []);

  const handleSave = async () => {
    setSaving(true);
    setMessage('');
    try {
      const res = await fetch('http://127.0.0.1:8000/api/settings', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(settings),
      });
      if (res.ok) {
        setMessage('Settings saved successfully!');
      } else {
        setMessage('Error saving settings.');
      }
    } catch (err) {
      console.error(err);
      setMessage('Network error.');
    } finally {
      setSaving(false);
      setTimeout(() => setMessage(''), 3000);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setSettings((prev: any) => ({
      ...prev,
      [name]: value
    }));
  };

  if (loading) {
    return <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}><RefreshCw className="animate-spin" /> Loading Settings...</div>;
  }

  return (
    <div style={{ maxWidth: '800px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <h1 style={{ fontSize: '28px', margin: 0, fontWeight: 700 }}>Settings</h1>
        <button 
          className="btn-primary" 
          onClick={handleSave} 
          disabled={saving}
          style={{ display: 'flex', alignItems: 'center', gap: '8px', opacity: saving ? 0.7 : 1 }}
        >
          <Save size={18} />
          {saving ? 'Saving...' : 'Save Changes'}
        </button>
      </div>

      {message && (
        <div style={{ 
          padding: '12px', 
          marginBottom: '24px', 
          backgroundColor: message.includes('success') ? 'rgba(52, 211, 153, 0.1)' : 'rgba(239, 68, 68, 0.1)',
          color: message.includes('success') ? 'var(--success)' : 'var(--danger)',
          borderRadius: '8px',
          border: `1px solid ${message.includes('success') ? 'var(--success)' : 'var(--danger)'}`
        }}>
          {message}
        </div>
      )}

      <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
        {/* API Settings Section */}
        <div style={{ backgroundColor: 'var(--bg-surface)', padding: '24px', borderRadius: '12px', border: '1px solid var(--border-color)' }}>
          <h2 style={{ fontSize: '18px', marginBottom: '16px', color: 'var(--text-main)', borderBottom: '1px solid var(--border-color)', paddingBottom: '12px' }}>
            API Configuration
          </h2>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div>
              <label>Gemini API Key</label>
              <input 
                type="password" 
                name="gemini_api_key" 
                value={settings.gemini_api_key || ''} 
                onChange={handleChange}
                style={{ width: '100%', maxWidth: '400px' }}
                placeholder="AIzaSy..."
              />
            </div>

            <div>
              <label>Cloud Provider</label>
              <select 
                name="cloud_provider" 
                value={settings.cloud_provider || 'ai_studio'} 
                onChange={handleChange}
                style={{ width: '100%', maxWidth: '400px' }}
              >
                <option value="ai_studio">Google AI Studio</option>
                <option value="vertex_ai">Vertex AI</option>
              </select>
            </div>
          </div>
        </div>

        {/* Processing Settings Section */}
        <div style={{ backgroundColor: 'var(--bg-surface)', padding: '24px', borderRadius: '12px', border: '1px solid var(--border-color)' }}>
          <h2 style={{ fontSize: '18px', marginBottom: '16px', color: 'var(--text-main)', borderBottom: '1px solid var(--border-color)', paddingBottom: '12px' }}>
            Processing Options
          </h2>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div>
              <label>Chunk Size (Tokens)</label>
              <input 
                type="number" 
                name="chunk_size" 
                value={settings.chunk_size || 3000} 
                onChange={handleChange}
                style={{ width: '100%', maxWidth: '200px' }}
              />
            </div>

            <div>
              <label>Translation Engine</label>
              <select 
                name="translation_engine" 
                value={settings.translation_engine || 'cloud'} 
                onChange={handleChange}
                style={{ width: '100%', maxWidth: '200px' }}
              >
                <option value="cloud">Cloud (Gemini)</option>
                <option value="local">Local (LLaMA.cpp)</option>
              </select>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
};
