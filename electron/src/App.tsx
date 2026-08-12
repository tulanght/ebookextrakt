import { HashRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from './components/Layout';
import { SettingsView } from './pages/SettingsView';
import { LibraryView } from './pages/LibraryView';
import { IngestionView } from './pages/IngestionView';
import { EditorView } from './pages/EditorView';
import './index.css';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<LibraryView />} />
          <Route path="ingest" element={<IngestionView />} />
          <Route path="editor" element={<EditorView />} />
          <Route path="settings" element={<SettingsView />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </Router>
  );
}

export default App;
