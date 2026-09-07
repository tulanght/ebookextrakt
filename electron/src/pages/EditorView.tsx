import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Save, ChevronRight, FileText, CheckCircle, RefreshCw } from 'lucide-react';
import { marked } from 'marked';
import DOMPurify from 'dompurify';

export const EditorView = () => {
  const [searchParams] = useSearchParams();
  const bookId = searchParams.get('book');
  
  const [book, setBook] = useState<any>(null);
  const [loadingBook, setLoadingBook] = useState(false);
  
  const [selectedArticleId, setSelectedArticleId] = useState<number | null>(null);
  const [articleData, setArticleData] = useState<any>(null);
  const [loadingArticle, setLoadingArticle] = useState(false);
  
  const [translationText, setTranslationText] = useState('');
  const [saving, setSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState('');
  
  const [previewMode, setPreviewMode] = useState(false);

  // Fetch Book TOC
  useEffect(() => {
    if (!bookId) return;
    const fetchBook = async () => {
      setLoadingBook(true);
      try {
        const res = await fetch(`http://127.0.0.1:8000/api/books/${bookId}`);
        const data = await res.json();
        setBook(data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoadingBook(false);
      }
    };
    fetchBook();
  }, [bookId]);

  // Fetch Article Content
  useEffect(() => {
    if (!selectedArticleId) return;
    const fetchArticle = async () => {
      setLoadingArticle(true);
      setSaveMessage('');
      try {
        const res = await fetch(`http://127.0.0.1:8000/api/editor/articles/${selectedArticleId}`);
        const data = await res.json();
        setArticleData(data);
        setTranslationText(data.translation_text || '');
      } catch (err) {
        console.error(err);
      } finally {
        setLoadingArticle(false);
      }
    };
    fetchArticle();
  }, [selectedArticleId]);

  const handleSave = async () => {
    if (!selectedArticleId) return;
    setSaving(true);
    setSaveMessage('');
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/editor/articles/${selectedArticleId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          translation_text: translationText,
          status: 'translated', // Mark as translated on save
          note: 'Manual edit via UI'
        })
      });
      if (res.ok) {
        setSaveMessage('Saved successfully!');
      } else {
        setSaveMessage('Error saving.');
      }
    } catch (err) {
      console.error(err);
      setSaveMessage('Network error.');
    } finally {
      setSaving(false);
      setTimeout(() => setSaveMessage(''), 3000);
    }
  };

  const createMarkup = (markdownText: string) => {
    const rawMarkup = marked.parse(markdownText || '') as string;
    const cleanMarkup = DOMPurify.sanitize(rawMarkup);
    return { __html: cleanMarkup };
  };

  if (!bookId) {
    return <div style={{ padding: '24px', color: 'var(--text-muted)' }}>No book selected. Please open a book from the Library.</div>;
  }

  return (
    <div style={{ display: 'flex', height: '100%', gap: '24px', overflow: 'hidden' }}>
      
      {/* Left Sidebar: TOC */}
      <div style={{ 
        width: '300px', 
        backgroundColor: 'var(--bg-surface)', 
        border: '1px solid var(--border-color)', 
        borderRadius: '12px',
        display: 'flex', 
        flexDirection: 'column',
        overflow: 'hidden'
      }}>
        <div style={{ padding: '16px', borderBottom: '1px solid var(--border-color)', backgroundColor: 'var(--bg-base)' }}>
          <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 600, color: 'var(--text-main)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
            {book?.title || 'Loading...'}
          </h3>
        </div>
        
        <div style={{ flex: 1, overflowY: 'auto', padding: '12px' }}>
          {loadingBook ? (
            <div style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '20px' }}><RefreshCw className="animate-spin" /></div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {book?.chapters?.map((ch: any) => (
                <div key={ch.id}>
                  <div style={{ fontWeight: 600, fontSize: '14px', padding: '8px', color: 'var(--text-main)' }}>
                    {ch.title}
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', paddingLeft: '12px' }}>
                    {ch.articles?.map((art: any) => {
                      const isSelected = selectedArticleId === art.id;
                      const isTranslated = art.status === 'translated' || art.publish_status === 'translated';
                      
                      return (
                        <div 
                          key={art.id}
                          onClick={() => setSelectedArticleId(art.id)}
                          style={{
                            padding: '8px 12px',
                            borderRadius: '8px',
                            cursor: 'pointer',
                            backgroundColor: isSelected ? 'var(--accent-bg)' : 'transparent',
                            color: isSelected ? 'var(--accent-primary)' : 'var(--text-muted)',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '8px',
                            fontSize: '13px',
                            transition: 'var(--transition)'
                          }}
                        >
                          {isTranslated ? (
                            <CheckCircle size={14} color="var(--success)" />
                          ) : (
                            <FileText size={14} />
                          )}
                          <span style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', flex: 1 }}>
                            {art.subtitle || 'Untitled Section'}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Main Editor Area */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '16px', overflow: 'hidden' }}>
        
        {/* Editor Toolbar */}
        <div style={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center',
          backgroundColor: 'var(--bg-surface)', 
          padding: '12px 24px', 
          borderRadius: '12px',
          border: '1px solid var(--border-color)'
        }}>
          <h2 style={{ fontSize: '18px', margin: 0, fontWeight: 600, color: 'var(--text-main)', display: 'flex', alignItems: 'center', gap: '8px' }}>
            {articleData?.subtitle || 'Select an article to edit'}
            {saveMessage && (
              <span style={{ fontSize: '14px', color: 'var(--success)', fontWeight: 400, marginLeft: '12px', display: 'flex', alignItems: 'center' }}>
                <CheckCircle size={14} style={{ marginRight: '4px' }}/> {saveMessage}
              </span>
            )}
          </h2>
          
          <div style={{ display: 'flex', gap: '12px' }}>
            <button 
              onClick={() => setPreviewMode(!previewMode)}
              style={{ 
                padding: '8px 16px', 
                backgroundColor: 'transparent', 
                border: '1px solid var(--border-color)', 
                color: 'var(--text-main)', 
                borderRadius: '8px' 
              }}
              disabled={!selectedArticleId}
            >
              {previewMode ? 'Edit Translation' : 'Preview Output'}
            </button>
            <button 
              className="btn-primary" 
              onClick={handleSave} 
              disabled={saving || !selectedArticleId}
              style={{ display: 'flex', alignItems: 'center', gap: '8px', opacity: (saving || !selectedArticleId) ? 0.6 : 1 }}
            >
              <Save size={16} />
              {saving ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </div>

        {/* Dual Pane Layout */}
        {loadingArticle ? (
          <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>
            <Loader2 size={32} className="animate-spin" />
          </div>
        ) : selectedArticleId ? (
          <div style={{ display: 'flex', gap: '16px', flex: 1, overflow: 'hidden' }}>
            
            {/* Original Text Pane */}
            <div style={{ 
              flex: 1, 
              backgroundColor: 'var(--bg-surface)', 
              border: '1px solid var(--border-color)', 
              borderRadius: '12px',
              display: 'flex',
              flexDirection: 'column',
              overflow: 'hidden'
            }}>
              <div style={{ padding: '8px 16px', borderBottom: '1px solid var(--border-color)', fontSize: '12px', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Original Content
              </div>
              <div 
                style={{ flex: 1, overflowY: 'auto', padding: '24px', lineHeight: '1.6', color: 'var(--text-main)', fontSize: '15px' }}
                dangerouslySetInnerHTML={createMarkup(articleData?.content_text)}
              />
            </div>

            {/* Translation Pane */}
            <div style={{ 
              flex: 1, 
              backgroundColor: 'var(--bg-surface)', 
              border: '1px solid var(--border-color)', 
              borderRadius: '12px',
              display: 'flex',
              flexDirection: 'column',
              overflow: 'hidden'
            }}>
              <div style={{ padding: '8px 16px', borderBottom: '1px solid var(--border-color)', fontSize: '12px', fontWeight: 600, color: 'var(--accent-primary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Translation {previewMode ? '(Preview)' : '(Editor)'}
              </div>
              
              {previewMode ? (
                <div 
                  style={{ flex: 1, overflowY: 'auto', padding: '24px', lineHeight: '1.6', color: 'var(--text-main)', fontSize: '15px' }}
                  dangerouslySetInnerHTML={createMarkup(translationText)}
                />
              ) : (
                <textarea
                  value={translationText}
                  onChange={(e) => setTranslationText(e.target.value)}
                  style={{
                    flex: 1,
                    border: 'none',
                    resize: 'none',
                    padding: '24px',
                    backgroundColor: 'transparent',
                    color: 'var(--text-main)',
                    fontSize: '15px',
                    lineHeight: '1.6',
                    fontFamily: 'var(--font-sans)',
                    outline: 'none'
                  }}
                  placeholder="Enter translation here... (Markdown supported)"
                />
              )}
            </div>
            
          </div>
        ) : (
          <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>
            Select an article from the left sidebar to start editing.
          </div>
        )}
        
      </div>
    </div>
  );
};
