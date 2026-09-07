import { Outlet, NavLink } from 'react-router-dom';
import { BookOpen, FileUp, Settings, Edit3, Activity } from 'lucide-react';
import React from 'react';

const SidebarItem = ({ to, icon: Icon, label }: { to: string, icon: any, label: string }) => {
  return (
    <NavLink
      to={to}
      style={({ isActive }) => ({
        display: 'flex',
        alignItems: 'center',
        padding: '12px 16px',
        margin: '4px 12px',
        borderRadius: '8px',
        textDecoration: 'none',
        color: isActive ? '#fff' : 'var(--text-muted)',
        backgroundColor: isActive ? 'var(--accent-primary)' : 'transparent',
        transition: 'all 0.2s ease',
        fontWeight: isActive ? 600 : 500,
      })}
    >
      <Icon size={20} style={{ marginRight: '12px' }} />
      {label}
    </NavLink>
  );
};

export const Layout = () => {
  return (
    <div style={{ display: 'flex', width: '100vw', height: '100vh', backgroundColor: 'var(--bg-base)' }}>
      {/* Sidebar */}
      <div
        style={{
          width: '260px',
          backgroundColor: 'var(--bg-surface)',
          borderRight: '1px solid var(--border-color)',
          display: 'flex',
          flexDirection: 'column',
          paddingTop: '20px'
        }}
      >
        <div style={{ padding: '0 24px', marginBottom: '32px' }}>
          <h2 style={{ color: 'var(--text-main)', fontSize: '18px', fontWeight: 700, display: 'flex', alignItems: 'center' }}>
            <Activity size={24} color="var(--accent-primary)" style={{ marginRight: '10px' }} />
            Extract<span style={{ color: 'var(--accent-primary)' }}>AI</span>
          </h2>
        </div>

        <nav style={{ flex: 1 }}>
          <SidebarItem to="/" icon={BookOpen} label="Library" />
          <SidebarItem to="/ingest" icon={FileUp} label="Import" />
          <SidebarItem to="/editor" icon={Edit3} label="Editor" />
          <SidebarItem to="/settings" icon={Settings} label="Settings" />
        </nav>
      </div>

      {/* Main Content Area */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        {/* Header */}
        <header
          style={{
            height: '64px',
            backgroundColor: 'var(--bg-surface)',
            borderBottom: '1px solid var(--border-color)',
            display: 'flex',
            alignItems: 'center',
            padding: '0 24px',
            justifyContent: 'space-between'
          }}
        >
          <div style={{ fontWeight: 600, color: 'var(--text-main)' }}>
            Workspace
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '14px', color: 'var(--text-muted)' }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: 'var(--success)' }}></span>
            API Connected
          </div>
        </header>

        {/* Scrollable Content */}
        <main style={{ flex: 1, overflowY: 'auto', padding: '32px' }}>
          <Outlet />
        </main>
      </div>
    </div>
  );
};
