import React, { useState, useRef } from 'react';
import { UploadCloud, FileText, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export const IngestionView = () => {
  const [dragActive, setDragActive] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [status, setStatus] = useState<'idle' | 'uploading' | 'success' | 'error'>('idle');
  const [message, setMessage] = useState('');
  const [bookId, setBookId] = useState<number | null>(null);
  
  const inputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const validateFile = (selectedFile: File) => {
    const ext = selectedFile.name.split('.').pop()?.toLowerCase();
    if (ext === 'pdf' || ext === 'epub') {
      setFile(selectedFile);
      setStatus('idle');
      setMessage('');
    } else {
      setStatus('error');
      setMessage('Invalid file type. Please upload a PDF or EPUB.');
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateFile(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      validateFile(e.target.files[0]);
    }
  };

  const onButtonClick = () => {
    inputRef.current?.click();
  };

  const handleUpload = async () => {
    if (!file) return;
    
    setUploading(true);
    setStatus('uploading');
    setMessage('Parsing document... this may take a few moments depending on the size.');
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      const res = await fetch('http://127.0.0.1:8000/api/ingest/upload', {
        method: 'POST',
        body: formData,
      });
      
      const data = await res.json();
      
      if (res.ok) {
        setStatus('success');
        setMessage(data.message || 'Book imported successfully!');
        setBookId(data.book_id);
      } else {
        setStatus('error');
        setMessage(data.detail || 'Failed to process file.');
      }
    } catch (err) {
      console.error(err);
      setStatus('error');
      setMessage('Network error occurred during upload.');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto' }}>
      <h1 style={{ fontSize: '28px', margin: '0 0 8px 0', fontWeight: 700 }}>Import Book</h1>
      <p style={{ color: 'var(--text-muted)', marginBottom: '32px' }}>
        Upload a PDF or EPUB file to extract text and add it to your library.
      </p>

      {/* Drag & Drop Zone */}
      {!file || status === 'success' ? (
        <div 
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          style={{
            border: `2px dashed ${dragActive ? 'var(--accent-primary)' : 'var(--border-color)'}`,
            borderRadius: '16px',
            padding: '64px 32px',
            textAlign: 'center',
            backgroundColor: dragActive ? 'var(--accent-bg)' : 'var(--bg-surface)',
            transition: 'var(--transition)',
            cursor: 'pointer'
          }}
          onClick={onButtonClick}
        >
          <input 
            ref={inputRef} 
            type="file" 
            accept=".pdf,.epub" 
            onChange={handleChange} 
            style={{ display: 'none' }} 
          />
          <UploadCloud size={64} color={dragActive ? 'var(--accent-primary)' : 'var(--text-muted)'} style={{ margin: '0 auto 16px', transition: 'var(--transition)' }} />
          <h3 style={{ fontSize: '20px', marginBottom: '8px', color: 'var(--text-main)' }}>
            Drag and drop your file here
          </h3>
          <p style={{ color: 'var(--text-muted)' }}>
            or click to browse from your computer (Supported: .pdf, .epub)
          </p>
        </div>
      ) : (
        /* File Preview Zone */
        <div style={{ 
          border: '1px solid var(--border-color)', 
          borderRadius: '16px', 
          padding: '24px', 
          backgroundColor: 'var(--bg-surface)' 
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '24px' }}>
            <div style={{ padding: '16px', backgroundColor: 'var(--accent-bg)', borderRadius: '12px', color: 'var(--accent-primary)' }}>
              <FileText size={32} />
            </div>
            <div style={{ flex: 1 }}>
              <h4 style={{ margin: 0, fontSize: '18px', color: 'var(--text-main)' }}>{file.name}</h4>
              <p style={{ margin: '4px 0 0 0', color: 'var(--text-muted)' }}>{(file.size / 1024 / 1024).toFixed(2)} MB</p>
            </div>
            {status === 'idle' && (
              <button 
                onClick={() => setFile(null)} 
                style={{ color: 'var(--text-muted)', backgroundColor: 'transparent', padding: '8px' }}
              >
                Clear
              </button>
            )}
          </div>

          {/* Action Area */}
          {status === 'idle' && (
            <button 
              className="btn-primary" 
              style={{ width: '100%', padding: '12px' }}
              onClick={handleUpload}
            >
              Start Import & Extraction
            </button>
          )}

          {status === 'uploading' && (
            <div style={{ textAlign: 'center', padding: '16px', color: 'var(--accent-primary)' }}>
              <Loader2 size={32} className="animate-spin" style={{ margin: '0 auto 12px' }} />
              <div>{message}</div>
            </div>
          )}

          {status === 'error' && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '16px', backgroundColor: 'rgba(239, 68, 68, 0.1)', color: 'var(--danger)', borderRadius: '8px' }}>
              <AlertCircle size={20} />
              {message}
            </div>
          )}
        </div>
      )}

      {/* Success State outside the drop zone if needed, or keep it inside */}
      {status === 'success' && (
        <div style={{ 
          marginTop: '24px',
          padding: '24px', 
          backgroundColor: 'rgba(52, 211, 153, 0.1)', 
          border: '1px solid var(--success)',
          borderRadius: '12px',
          textAlign: 'center'
        }}>
          <CheckCircle size={48} color="var(--success)" style={{ margin: '0 auto 16px' }} />
          <h3 style={{ fontSize: '20px', color: 'var(--success)', margin: '0 0 8px 0' }}>Success!</h3>
          <p style={{ color: 'var(--text-main)', marginBottom: '24px' }}>{message}</p>
          <div style={{ display: 'flex', gap: '16px', justifyContent: 'center' }}>
            <button 
              className="btn-primary" 
              onClick={() => navigate('/')}
            >
              Go to Library
            </button>
            {bookId && (
              <button 
                style={{ 
                  padding: '8px 16px', 
                  backgroundColor: 'var(--bg-surface)', 
                  border: '1px solid var(--border-color)', 
                  color: 'var(--text-main)', 
                  borderRadius: '8px' 
                }}
                onClick={() => navigate(`/editor?book=${bookId}`)}
              >
                Open in Editor
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
