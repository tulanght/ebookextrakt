import React, { useState, useEffect } from 'react';
import { Search, Book, Trash2, Edit3, LibraryBig } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export const LibraryView = () => {
  const [books, setBooks] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const navigate = useNavigate();

  const fetchBooks = async (query = '') => {
    setLoading(true);
    try {
      const url = query ? `http://127.0.0.1:8000/api/books?q=${encodeURIComponent(query)}` : 'http://127.0.0.1:8000/api/books';
      const res = await fetch(url);
      const data = await res.json();
      setBooks(data);
    } catch (err) {
      console.error("Failed to fetch books", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Debounce search slightly
    const timer = setTimeout(() => {
      fetchBooks(search);
    }, 300);
    return () => clearTimeout(timer);
  }, [search]);

  const handleDelete = async (e: React.MouseEvent, bookId: number) => {
    e.stopPropagation();
    if (!window.confirm("Are you sure you want to delete this book?")) return;
    try {
      await fetch(`http://127.0.0.1:8000/api/books/${bookId}`, { method: 'DELETE' });
      fetchBooks(search);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', gap: '24px' }}>
      {/* Top Bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1 style={{ fontSize: '28px', margin: 0, fontWeight: 700, display: 'flex', alignItems: 'center', gap: '12px' }}>
          <LibraryBig color="var(--accent-primary)" />
          My Library
        </h1>
        
        <div style={{ position: 'relative', width: '300px' }}>
          <Search size={18} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
          <input 
            type="text" 
            placeholder="Search titles, authors..." 
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{ width: '100%', paddingLeft: '40px', borderRadius: '20px' }}
          />
        </div>
      </div>

      {/* Grid */}
      {loading ? (
        <div style={{ color: 'var(--text-muted)' }}>Loading catalog...</div>
      ) : books.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '60px 20px', backgroundColor: 'var(--bg-surface)', borderRadius: '12px', border: '1px dashed var(--border-color)' }}>
          <Book size={48} color="var(--text-muted)" style={{ marginBottom: '16px', opacity: 0.5 }} />
          <h3 style={{ fontSize: '18px', color: 'var(--text-main)', marginBottom: '8px' }}>No books found</h3>
          <p style={{ color: 'var(--text-muted)', marginBottom: '24px' }}>Your library is empty or no books match your search.</p>
          <button className="btn-primary" onClick={() => navigate('/ingest')}>Import a Book</button>
        </div>
      ) : (
        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))', 
          gap: '24px',
          alignItems: 'start'
        }}>
          {books.map((book) => (
            <div 
              key={book.id} 
              style={{
                backgroundColor: 'var(--bg-surface)',
                borderRadius: '12px',
                border: '1px solid var(--border-color)',
                overflow: 'hidden',
                transition: 'var(--transition)',
                cursor: 'pointer',
                display: 'flex',
                flexDirection: 'column'
              }}
              onClick={() => {
                console.log("Navigating to book detail:", book.id);
                // navigate(`/editor?book=${book.id}`) 
                // Will implement later
              }}
              onMouseEnter={(e) => e.currentTarget.style.transform = 'translateY(-4px)'}
              onMouseLeave={(e) => e.currentTarget.style.transform = 'none'}
            >
              {/* Cover Placeholder */}
              <div style={{
                height: '160px',
                background: 'linear-gradient(135deg, var(--accent-primary) 0%, var(--accent-hover) 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                padding: '20px',
                textAlign: 'center'
              }}>
                <h3 style={{ color: '#fff', fontSize: '18px', fontWeight: 600, textShadow: '0 2px 4px rgba(0,0,0,0.3)' }}>
                  {book.title}
                </h3>
              </div>
              
              {/* Details */}
              <div style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '12px', flex: 1 }}>
                <div>
                  <div style={{ fontSize: '16px', fontWeight: 600, color: 'var(--text-main)', marginBottom: '4px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {book.title}
                  </div>
                  <div style={{ fontSize: '14px', color: 'var(--text-muted)' }}>
                    {book.author || 'Unknown Author'}
                  </div>
                </div>

                {/* Stats */}
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: 'var(--text-muted)', backgroundColor: 'var(--bg-base)', padding: '8px', borderRadius: '6px' }}>
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                    <span style={{ fontWeight: 600, color: 'var(--text-main)' }}>{book.total_leaf || 0}</span>
                    <span>Articles</span>
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                    <span style={{ fontWeight: 600, color: 'var(--success)' }}>{book.translated_count || 0}</span>
                    <span>Translated</span>
                  </div>
                </div>

                {/* Actions */}
                <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', marginTop: 'auto', paddingTop: '12px', borderTop: '1px solid var(--border-color)' }}>
                  <button 
                    onClick={(e) => { e.stopPropagation(); navigate(`/editor?book=${book.id}`); }}
                    style={{ padding: '6px', borderRadius: '6px', backgroundColor: 'var(--accent-bg)', color: 'var(--accent-primary)' }}
                    title="Open in Editor"
                  >
                    <Edit3 size={16} />
                  </button>
                  <button 
                    onClick={(e) => handleDelete(e, book.id)}
                    style={{ padding: '6px', borderRadius: '6px', backgroundColor: 'rgba(239, 68, 68, 0.1)', color: 'var(--danger)' }}
                    title="Delete Book"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
