
import os
import shutil
from pathlib import Path
from typing import Dict, Any
import json

def generate_webview(
    book_title: str,
    author: str,
    chapters: list[dict],
    output_dir: Path,
    theme: str = "light"
) -> Path:
    """
    Generates a standalone self-contained HTML file for the book.
    All CSS and JS are inlined so it works on mobile (no CORS issues).
    Images are referenced as relative paths from the images/ subfolder.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Single self-contained file
    index_path = output_dir / "index.html"
    _write_html(index_path, book_title, author, chapters, output_dir.name)
    
    return index_path

def _get_css() -> str:
    css_content = """
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    :root {
        --bg-body: #f8fafc;
        --bg-card: #ffffff;
        --bg-sidebar: #ffffff;
        --bg-toolbar: rgba(255, 255, 255, 0.85);
        --text-primary: #1e293b;
        --text-secondary: #64748b;
        --border-color: #e2e8f0;
        --accent-primary: #3b82f6;
        --accent-hover: #2563eb;
        --shadow-sm: 0 1px 3px rgba(0,0,0,0.05);
        --shadow-md: 0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06);
        --shadow-lg: 0 10px 15px -3px rgba(0,0,0,0.1), 0 4px 6px -2px rgba(0,0,0,0.05);
        --radius-md: 8px;
        --radius-lg: 12px;
        --radius-full: 9999px;
        --header-height: 60px;
    }
    
    [data-theme="dark"] {
        --bg-body: #0f172a;
        --bg-card: #1e293b;
        --bg-sidebar: #1e293b;
        --bg-toolbar: rgba(30, 41, 59, 0.85);
        --text-primary: #f8fafc;
        --text-secondary: #94a3b8;
        --border-color: #334155;
        --accent-primary: #60a5fa;
        --accent-hover: #93c5fd;
        --shadow-sm: 0 1px 3px rgba(0,0,0,0.3);
        --shadow-md: 0 4px 6px -1px rgba(0,0,0,0.4);
        --shadow-lg: 0 10px 15px -3px rgba(0,0,0,0.5);
    }

    * { margin: 0; padding: 0; box-sizing: border-box; }

    body {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        background-color: var(--bg-body);
        color: var(--text-primary);
        display: flex;
        height: 100vh;
        overflow: hidden;
        transition: background-color 0.3s ease, color 0.3s ease;
    }

    /* Sidebar */
    .sidebar {
        width: 320px;
        background-color: var(--bg-sidebar);
        border-right: 1px solid var(--border-color);
        display: flex;
        flex-direction: column;
        height: 100%;
        transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        z-index: 100;
        box-shadow: var(--shadow-md);
    }
    
    .sidebar.collapsed {
        transform: translateX(-320px);
        position: absolute;
    }
    
    .sidebar-header {
        padding: 20px;
        border-bottom: 1px solid var(--border-color);
        display: flex;
        flex-direction: column;
        gap: 15px;
    }
    
    .sidebar-title-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .sidebar-header h1 {
        font-size: 1.25rem;
        font-weight: 700;
        color: var(--accent-primary);
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        letter-spacing: -0.025em;
    }
    
    .search-box {
        position: relative;
        width: 100%;
    }
    
    .search-input {
        width: 100%;
        padding: 10px 12px 10px 36px;
        border: 1px solid var(--border-color);
        border-radius: var(--radius-md);
        background-color: var(--bg-body);
        color: var(--text-primary);
        font-family: 'Inter', sans-serif;
        font-size: 0.9rem;
        transition: border-color 0.2s, box-shadow 0.2s;
    }
    
    .search-input:focus {
        outline: none;
        border-color: var(--accent-primary);
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
    }
    
    .search-icon {
        position: absolute;
        left: 12px;
        top: 50%;
        transform: translateY(-50%);
        color: var(--text-secondary);
        font-size: 0.9rem;
    }

    .close-btn {
        background: none;
        border: none;
        color: var(--text-secondary);
        cursor: pointer;
        font-size: 1.5rem;
        display: none;
        transition: color 0.2s;
    }
    
    .close-btn:hover { color: var(--accent-primary); }

    .toc {
        flex: 1;
        overflow-y: auto;
        padding: 15px 10px;
    }
    
    .toc::-webkit-scrollbar { width: 6px; }
    .toc::-webkit-scrollbar-thumb { background-color: var(--border-color); border-radius: 10px; }
    
    .toc-chapter {
        font-weight: 600;
        padding: 15px 15px 5px 15px;
        text-transform: uppercase;
        font-size: 0.75rem;
        letter-spacing: 0.05em;
        color: var(--text-secondary);
        margin-top: 10px;
    }
    
    .toc-item {
        padding: 10px 15px;
        cursor: pointer;
        border-radius: var(--radius-md);
        margin-bottom: 4px;
        transition: all 0.2s ease;
        font-size: 0.95rem;
        line-height: 1.4;
        color: var(--text-primary);
    }
    
    .toc-item:hover {
        background-color: var(--bg-body);
        color: var(--accent-primary);
    }
    
    .toc-item.active {
        background-color: var(--accent-primary);
        color: white;
        font-weight: 500;
        box-shadow: var(--shadow-sm);
    }

    /* Search Results styling inside TOC */
    .search-result-snippet {
        font-size: 0.8rem;
        color: var(--text-secondary);
        margin-top: 4px;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }
    
    .toc-item.active .search-result-snippet {
        color: rgba(255,255,255,0.8);
    }

    mark {
        background-color: rgba(250, 204, 21, 0.5);
        color: inherit;
        border-radius: 2px;
        padding: 0 2px;
    }

    /* Main Content */
    .main-content {
        flex: 1;
        display: flex;
        flex-direction: column;
        height: 100%;
        overflow: hidden;
        position: relative;
    }
    
    .toolbar {
        height: var(--header-height);
        padding: 0 24px;
        border-bottom: 1px solid var(--border-color);
        display: flex;
        justify-content: space-between;
        align-items: center;
        background-color: var(--bg-toolbar);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        z-index: 10;
        transition: background-color 0.3s;
    }
    
    .left-controls {
        display: flex;
        align-items: center;
        gap: 20px;
    }
    
    .menu-btn {
        background: none;
        border: none;
        font-size: 1.25rem;
        cursor: pointer;
        color: var(--text-primary);
        padding: 8px;
        border-radius: var(--radius-md);
        display: flex;
        align-items: center;
        justify-content: center;
        transition: background-color 0.2s;
    }
    
    .menu-btn:hover { background-color: var(--border-color); }
    
    .author-name {
        font-size: 0.9rem;
        font-weight: 500;
        color: var(--text-secondary);
    }

    .right-controls {
        display: flex;
        flex-direction: column;
        align-items: flex-end;
        justify-content: center;
        gap: 4px;
    }
    
    .right-top-row {
        display: flex;
        align-items: center;
        gap: 15px;
    }
    
    .meta-info {
        font-size: 0.7rem;
        color: var(--text-secondary);
        opacity: 0.7;
        margin-right: 4px;
    }

    .theme-toggle, .copy-btn {
        background: none;
        border: none;
        cursor: pointer;
        color: var(--text-secondary);
        font-size: 1.2rem;
        padding: 8px;
        border-radius: var(--radius-full);
        transition: all 0.2s;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    .theme-toggle:hover, .copy-btn:hover {
        background-color: var(--border-color);
        color: var(--accent-primary);
    }
    
    @media (min-width: 1024px) {
        .mobile-only { display: none !important; }
    }
    
    .view-controls {
        display: flex;
        background-color: var(--border-color);
        padding: 4px;
        border-radius: var(--radius-lg);
    }
    
    .view-controls button {
        background: none;
        border: none;
        color: var(--text-secondary);
        padding: 6px 16px;
        border-radius: var(--radius-md);
        cursor: pointer;
        font-size: 0.85rem;
        font-weight: 500;
        font-family: 'Inter', sans-serif;
        transition: all 0.2s ease;
    }
    
    .view-controls button:hover {
        color: var(--text-primary);
    }
    
    .view-controls button.active {
        background-color: var(--bg-card);
        color: var(--accent-primary);
        box-shadow: var(--shadow-sm);
    }

    .reader-area {
        flex: 1;
        overflow-y: auto;
        padding: 40px 20px;
        scroll-behavior: smooth;
    }
    
    .reader-area::-webkit-scrollbar { width: 8px; }
    .reader-area::-webkit-scrollbar-thumb { background-color: var(--border-color); border-radius: 10px; }

    .article-container {
        max-width: 900px;
        margin: 0 auto;
        padding-bottom: 80px;
    }
    
    .article-card {
        background-color: var(--bg-card);
        padding: 40px 50px;
        margin-bottom: 40px;
        border-radius: var(--radius-lg);
        box-shadow: var(--shadow-lg);
        border: 1px solid var(--border-color);
        transition: background-color 0.3s, border-color 0.3s;
    }
    
    .article-title {
        font-size: 2rem;
        font-weight: 700;
        margin-bottom: 30px;
        color: var(--text-primary);
        letter-spacing: -0.025em;
        line-height: 1.2;
    }
    
    .content-grid {
        display: grid;
        grid-template-columns: 1fr;
        gap: 30px;
    }
    
    .content-grid.dual-view {
        grid-template-columns: 1fr 1fr;
        gap: 40px;
    }
    
    .text-block {
        line-height: 1.7;
        font-size: 1.05rem;
        color: var(--text-primary);
    }
    
    .translation-block {
        position: relative;
    }
    
    .dual-view .translation-block {
        padding-left: 30px;
        border-left: 2px solid var(--border-color);
    }
    
    .untranslated {
        color: var(--text-secondary);
        font-style: italic;
        background-color: var(--bg-body);
        padding: 15px;
        border-radius: var(--radius-md);
        text-align: center;
        border: 1px dashed var(--border-color);
    }
    
    img {
        max-width: 100%;
        height: auto;
        display: block;
        margin: 30px auto;
        border-radius: var(--radius-md);
        box-shadow: var(--shadow-md);
    }
    
    figure { margin: 0; }
    figcaption {
        text-align: center;
        font-size: 0.85rem;
        color: var(--text-secondary);
        margin-top: 10px;
        font-style: italic;
    }

    h1, h2, h3, h4, h5, h6 {
        color: var(--text-primary);
        margin-top: 2em;
        margin-bottom: 0.75em;
        font-weight: 600;
        line-height: 1.3;
        letter-spacing: -0.015em;
    }
    h1 { font-size: 1.8rem; }
    h2 { font-size: 1.5rem; }
    h3 { font-size: 1.25rem; }
    
    p { margin-bottom: 1.5em; text-align: justify; }
    
    ul, ol { margin-bottom: 1.5em; padding-left: 1.5em; }
    li { margin-bottom: 0.5em; }
    
    strong { font-weight: 600; color: var(--accent-primary); }
    em { font-style: italic; }

    /* Responsive */
    @media (max-width: 1024px) {
        .content-grid.dual-view { gap: 20px; }
        .dual-view .translation-block { padding-left: 20px; }
    }

    @media (max-width: 768px) {
        .sidebar {
            position: absolute;
            left: 0;
            top: 0;
            bottom: 0;
            transform: translateX(-100%);
            width: 85%;
            max-width: 320px;
        }
        
        .sidebar.open { transform: translateX(0); }
        
        .content-grid.dual-view { grid-template-columns: 1fr; }
        .dual-view .translation-block {
            padding-left: 0;
            border-left: none;
            padding-top: 30px;
            margin-top: 30px;
            border-top: 2px dashed var(--border-color);
        }
        
        .close-btn { display: block; }
        .sidebar.collapsed { transform: translateX(-100%); }
        
        .article-card { padding: 25px 20px; margin-bottom: 20px; }
        .reader-area { padding: 20px 10px; }
        .toolbar { padding: 0 15px; }
        .view-controls button { padding: 6px 10px; font-size: 0.75rem; }
        .author-name { display: none; }
    }
    """
    return css_content

def _get_js(chapters: list, folder_name: str) -> str:
    js_data = f"const bookData = {json.dumps(chapters, ensure_ascii=False)};\nconst bookFolderName = {json.dumps(folder_name, ensure_ascii=False)};"
    
    js_logic = r"""
    let currentViewMode = 'dual'; // 'original', 'translation', 'dual'
    let isSidebarOpen = true; // Desktop default

    document.addEventListener('DOMContentLoaded', () => {
        initTheme();
        renderTOC();
        renderWelcome();
        checkResponsive();
        window.addEventListener('resize', checkResponsive);
        
        // Setup Search
        const searchInput = document.getElementById('search-input');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                const query = e.target.value.trim();
                if (query.length > 1) {
                    performSearch(query);
                } else {
                    renderTOC(); // Reset to normal TOC
                }
            });
        }
    });
    
    function initTheme() {
        const savedTheme = localStorage.getItem('theme') || 'light';
        document.body.setAttribute('data-theme', savedTheme);
        updateThemeIcon(savedTheme);
    }
    
    function toggleTheme() {
        const currentTheme = document.body.getAttribute('data-theme');
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        document.body.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        updateThemeIcon(newTheme);
    }
    
    function updateThemeIcon(theme) {
        const btn = document.querySelector('.theme-toggle');
        if (!btn) return;
        if (theme === 'dark') {
            btn.innerHTML = '☀️'; // Show sun to switch to light
            btn.title = 'Chuyển sang Giao diện Sáng';
        } else {
            btn.innerHTML = '🌙'; // Show moon to switch to dark
            btn.title = 'Chuyển sang Giao diện Tối';
        }
    }
    
    function checkResponsive() {
        if (window.innerWidth <= 768) {
            isSidebarOpen = false;
            updateSidebar();
        } else {
            isSidebarOpen = true;
            updateSidebar();
        }
    }
    
    function toggleSidebar() {
        isSidebarOpen = !isSidebarOpen;
        updateSidebar();
    }
    
    function updateSidebar() {
        const sidebar = document.querySelector('.sidebar');
        if (window.innerWidth <= 768) {
            if (isSidebarOpen) sidebar.classList.add('open');
            else sidebar.classList.remove('open');
        } else {
            if (isSidebarOpen) sidebar.classList.remove('collapsed');
            else sidebar.classList.add('collapsed');
        }
    }

    function renderTOC() {
        const tocContainer = document.getElementById('toc-list');
        tocContainer.innerHTML = '';
        bookData.forEach((chapter, cIdx) => {
            const chapHeader = document.createElement('div');
            chapHeader.className = 'toc-chapter';
            chapHeader.textContent = chapter.title;
            tocContainer.appendChild(chapHeader);
            
            chapter.articles.forEach((article, aIdx) => {
                const item = document.createElement('div');
                item.className = 'toc-item';
                item.id = `toc-${cIdx}-${aIdx}`;
                item.textContent = article.subtitle || 'Section ' + (aIdx + 1);
                item.onclick = () => { loadArticle(cIdx, aIdx, item); if(window.innerWidth<=768) toggleSidebar(); };
                tocContainer.appendChild(item);
            });
        });
    }
    
    function performSearch(query) {
        const tocContainer = document.getElementById('toc-list');
        tocContainer.innerHTML = '';
        const lowerQuery = query.toLowerCase();
        
        let foundCount = 0;
        
        bookData.forEach((chapter, cIdx) => {
            let chapterAdded = false;
            
            chapter.articles.forEach((article, aIdx) => {
                const title = (article.subtitle || '').toLowerCase();
                const content = (article.content_text || '').toLowerCase();
                const trans = (article.translation_text || '').toLowerCase();
                
                if (title.includes(lowerQuery) || content.includes(lowerQuery) || trans.includes(lowerQuery)) {
                    if (!chapterAdded) {
                        const chapHeader = document.createElement('div');
                        chapHeader.className = 'toc-chapter';
                        chapHeader.textContent = chapter.title;
                        tocContainer.appendChild(chapHeader);
                        chapterAdded = true;
                    }
                    
                    const item = document.createElement('div');
                    item.className = 'toc-item';
                    item.id = `toc-${cIdx}-${aIdx}`;
                    
                    // Highlight title if matched
                    let displayTitle = article.subtitle || 'Section ' + (aIdx + 1);
                    if (title.includes(lowerQuery)) {
                        const regex = new RegExp(`(${query})`, 'gi');
                        displayTitle = displayTitle.replace(regex, '<mark>$1</mark>');
                    }
                    item.innerHTML = `<div>${displayTitle}</div>`;
                    
                    // Extract snippet if content matched
                    if (!title.includes(lowerQuery)) {
                        let snippet = '';
                        let textToSearch = '';
                        if (content.includes(lowerQuery)) textToSearch = article.content_text;
                        else if (trans.includes(lowerQuery)) textToSearch = article.translation_text;
                        
                        if (textToSearch) {
                            const idx = textToSearch.toLowerCase().indexOf(lowerQuery);
                            const start = Math.max(0, idx - 40);
                            const end = Math.min(textToSearch.length, idx + query.length + 40);
                            snippet = textToSearch.substring(start, end);
                            if (start > 0) snippet = '...' + snippet;
                            if (end < textToSearch.length) snippet += '...';
                            
                            const regex = new RegExp(`(${query})`, 'gi');
                            snippet = snippet.replace(regex, '<mark>$1</mark>');
                            
                            const snippetDiv = document.createElement('div');
                            snippetDiv.className = 'search-result-snippet';
                            snippetDiv.innerHTML = snippet;
                            item.appendChild(snippetDiv);
                        }
                    }
                    
                    item.onclick = () => { loadArticle(cIdx, aIdx, item); if(window.innerWidth<=768) toggleSidebar(); };
                    tocContainer.appendChild(item);
                    foundCount++;
                }
            });
        });
        
        if (foundCount === 0) {
            tocContainer.innerHTML = '<div style="padding: 20px; text-align: center; color: var(--text-secondary); font-size: 0.9rem;">Không tìm thấy kết quả nào</div>';
        }
    }
    
    function loadArticle(cIdx, aIdx, domItem) {
        document.querySelectorAll('.toc-item').forEach(el => el.classList.remove('active'));
        if(domItem) domItem.classList.add('active');
        else {
            const el = document.getElementById(`toc-${cIdx}-${aIdx}`);
            if (el) el.classList.add('active');
        }
        
        const article = bookData[cIdx].articles[aIdx];
        const container = document.getElementById('content-display');
        container.innerHTML = '';
        
        // Calculate word count and read time
        const textToCount = article.translation_text || article.content_text || '';
        const wordCount = textToCount.trim().split(/\s+/).filter(w => w.length > 0).length;
        const readTime = Math.max(1, Math.ceil(wordCount / 200));
        const metaDiv = document.getElementById('article-meta-info');
        if (metaDiv) {
            metaDiv.textContent = `${wordCount.toLocaleString('vi-VN')} từ • ~${readTime} phút đọc`;
        }
        
        const card = document.createElement('div');
        card.className = 'article-card';
        card.id = `art-${cIdx}-${aIdx}`;
        
        const title = document.createElement('div');
        title.className = 'article-title';
        title.textContent = article.subtitle;
        card.appendChild(title);
        
        const grid = document.createElement('div');
        grid.className = `content-grid ${currentViewMode === 'dual' ? 'dual-view' : ''}`;
        
        const originalDiv = document.createElement('div');
        originalDiv.className = 'text-block';
        originalDiv.innerHTML = processContent(article.content_text);
        
        const transDiv = document.createElement('div');
        transDiv.className = 'text-block translation-block';
        if (article.translation_text && article.translation_text.trim()) {
            transDiv.innerHTML = processContent(article.translation_text);
        } else {
            transDiv.innerHTML = '<div class="untranslated">Bản dịch đang được cập nhật...</div>';
        }
        
        if (currentViewMode !== 'translation') grid.appendChild(originalDiv);
        if (currentViewMode !== 'original') grid.appendChild(transDiv);
        
        card.appendChild(grid);
        container.appendChild(card);
        
        // Highlight search terms inside article if searching
        const searchInput = document.getElementById('search-input');
        if (searchInput && searchInput.value.trim().length > 1) {
            const query = searchInput.value.trim();
            highlightTextInElement(originalDiv, query);
            highlightTextInElement(transDiv, query);
        }
        
        document.querySelector('.reader-area').scrollTop = 0;
    }
    
    function highlightTextInElement(element, query) {
        // Simple highlight, not perfect for nested HTML but works for our paragraphs
        const regex = new RegExp(`(${query})`, 'gi');
        const paragraphs = element.querySelectorAll('p');
        paragraphs.forEach(p => {
            // Only replace text nodes to avoid breaking HTML
            p.innerHTML = p.innerHTML.replace(regex, '<mark>$1</mark>');
        });
    }
    
    function processContent(text) {
        if (!text) return '';
        
        let output = text;
        output = output.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
             
        output = output.replace(/\[Image: ([^\]]+)\]/g, (match, filename) => {
            let file = filename;
            let caption = '';
            if (filename.includes(' - Caption: ')) {
                const parts = filename.split(' - Caption: ');
                file = parts[0].trim();
                caption = parts[1].trim();
            } else {
                file = filename.trim();
            }
            let figcaption = caption ? `<figcaption>${caption}</figcaption>` : '';
            return `__IMG__<figure><img src="images/${file}" alt="${caption}">${figcaption}</figure>__IMG__`;
        });

        // Support Markdown images: ![alt](filename)
        output = output.replace(/!\[(.*?)\]\((.*?)\)/g, (match, alt, src) => {
            // Extract just the filename in case src contains paths
            const filename = src.split('/').pop().split('\\').pop();
            // If alt is empty or just the image name, don't show a caption
            const caption = (alt && alt !== filename && !alt.startsWith('image_')) ? alt : '';
            let figcaption = caption ? `<figcaption>${caption}</figcaption>` : '';
            return `__IMG__<figure><img src="images/${filename}" alt="${caption}">${figcaption}</figure>__IMG__`;
        });

        const lines = output.split('\n');
        let processed = [];
        let inList = false;
        
        lines.forEach(line => {
            let l = line.trimEnd();
            
            if (!l) {
                if (inList) { processed.push('</ul>'); inList = false; }
                processed.push(''); 
                return;
            }
            
            if (l.match(/^#{1,6}\s/)) {
                 if (inList) { processed.push('</ul>'); inList = false; }
                 l = l.replace(/^(#{1,6})\s+(.+)$/, (m, h, c) => `<h${h.length}>${c}</h${h.length}>`);
                 processed.push(l);
                 return;
            }
            
            if (l.match(/^-\s/)) {
                if (!inList) { processed.push('<ul>'); inList = true; }
                l = l.replace(/^-\s+(.+)$/, '<li>$1</li>');
                processed.push(l);
                return;
            }
            
            if (inList) { processed.push('</ul>'); inList = false; }
            processed.push(l);
        });
        
        if (inList) processed.push('</ul>');
        output = processed.join('\n');
        
        output = output.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        output = output.replace(/\*(.*?)\*/g, '<em>$1</em>');
        
        const blocks = output.split(/\n\n+/);
        output = blocks.map(block => {
            block = block.trim();
            if (!block) return '';
            
            // If the entire block is just an image/heading/list, return it
            if (block.startsWith('<h') || block.startsWith('<ul>') || (block.startsWith('__IMG__') && block.endsWith('__IMG__'))) {
                return block.replace(/__IMG__/g, '');
            }
            
            // Otherwise, it's a paragraph block. Convert newlines to breaks.
            block = block.replace(/\n/g, '<br>');
            
            // If the block contains inline images, the __IMG__ tags are still there.
            // We just strip the __IMG__ markers globally.
            block = block.replace(/__IMG__/g, '');
            
            return `<p>${block}</p>`;
        }).join('\n');
        
        return output;
    }
    
    function setView(mode) {
        currentViewMode = mode;
        document.querySelectorAll('.view-controls button').forEach(b => b.classList.remove('active'));
        document.getElementById('btn-' + mode).classList.add('active');
        
        const container = document.getElementById('content-display');
        if (container.children.length > 0) {
            // Find which article is active
            const activeToc = document.querySelector('.toc-item.active');
            if (activeToc) {
                const parts = activeToc.id.split('-');
                if (parts.length === 3) {
                    loadArticle(parseInt(parts[1]), parseInt(parts[2]));
                }
            }
        }
    }
    
    function renderWelcome() {
        document.getElementById('content-display').innerHTML = `
            <div style="text-align: center; padding: 100px 20px; color: var(--text-secondary);">
                <div style="font-size: 3rem; margin-bottom: 20px;">📖</div>
                <h2 style="font-size: 1.5rem; margin-bottom: 10px; color: var(--text-primary);">Sách đã sẵn sàng</h2>
                <p>Hãy chọn một chương bên danh mục bên trái để bắt đầu đọc.</p>
                <div class="mobile-only" style="margin-top: 30px; padding: 15px; background: var(--bg-body); border-radius: 8px; border: 1px dashed var(--border-color); font-size: 0.9rem; text-align: left;">
                    <strong>⚠️ Mẹo đọc Offline trên Mobile:</strong><br>
                    Do bảo mật của Android 11+, Chrome <b>không thể</b> đọc ảnh từ thư mục thông thường. Để xem được ảnh, bạn có 2 cách:<br>
                    1. <b>Cách tốt nhất:</b> Cài app <i>Simple HTTP Server</i> (hoặc tương tự), chọn thư mục chứa file HTML này và bấm Start. Sau đó mở link do app cung cấp.<br>
                    2. <b>Cách thủ công:</b> Chép toàn bộ thư mục sách vào đúng đường dẫn: <br><code style="background: var(--bg-card); padding: 2px 4px; border-radius: 4px; word-break: break-all;">/Android/data/com.android.chrome/files/Download/</code><br>Sau đó dùng nút 🔗 ở trên để lấy link.
                </div>
            </div>
        `;
    }

    function copyFilePath() {
        let currentUrl = window.location.href;
        if (currentUrl.startsWith('content://')) {
            currentUrl = `file:///storage/emulated/0/Android/data/com.android.chrome/files/Download/${bookFolderName}/index.html`;
            prompt("Nếu bạn đã chép sách vào thư mục của Chrome (Cách 2), hãy copy đường dẫn này và dán vào Chrome:", currentUrl);
        } else {
            prompt("Copy đường dẫn bên dưới và dán vào thanh địa chỉ của Chrome:", currentUrl);
        }
    }

    window.setView = setView;
    window.toggleSidebar = toggleSidebar;
    window.toggleTheme = toggleTheme;
    """
    
    return js_data + "\n" + js_logic

def _write_html(path: Path, title: str, author: str, chapters: list, folder_name: str):
    css = _get_css()
    js = _get_js(chapters, folder_name)
    
    # Escape title for safe HTML embedding
    safe_title = title.replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')
    safe_author = author.replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')
    
    html = f"""<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0">
    <title>{safe_title}</title>
    <style>{css}</style>
</head>
<body data-theme="light">
    <div class="sidebar">
        <div class="sidebar-header">
            <div class="sidebar-title-row">
                <h1 title="{safe_title}">{safe_title}</h1>
                <button class="close-btn" onclick="toggleSidebar()">&times;</button>
            </div>
            <div class="search-box">
                <span class="search-icon">&#128269;</span>
                <input type="text" id="search-input" class="search-input" placeholder="T&#236;m ki&#7871;m trong s&#225;ch...">
            </div>
        </div>
        <div class="toc" id="toc-list"></div>
    </div>
    
    <div class="main-content">
        <div class="toolbar">
            <div class="left-controls">
                <button class="menu-btn" onclick="toggleSidebar()">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="3" y1="12" x2="21" y2="12"></line><line x1="3" y1="6" x2="21" y2="6"></line><line x1="3" y1="18" x2="21" y2="18"></line></svg>
                </button>
                <span class="author-name">{safe_author}</span>
            </div>
            <div class="right-controls">
                <div class="right-top-row">
                    <div class="view-controls">
                        <button id="btn-original" onclick="setView('original')">G&#7889;c</button>
                        <button id="btn-dual" class="active" onclick="setView('dual')">Song Ng&#7919;</button>
                        <button id="btn-translation" onclick="setView('translation')">B&#7843;n D&#7883;ch</button>
                    </div>
                    <button class="copy-btn mobile-only" onclick="copyFilePath()" title="Copy đ&#432;&#7901;ng d&#7851;n &#273;&#7875; d&#225;n v&#224;o Chrome Mobile">&#128279;</button>
                    <button class="theme-toggle" onclick="toggleTheme()" title="Chuy&#7875;n giao di&#7879;n">&#127769;</button>
                </div>
                <div id="article-meta-info" class="meta-info"></div>
            </div>
        </div>
        
        <div class="reader-area">
            <div class="article-container" id="content-display"></div>
        </div>
    </div>
    
    <script>{js}</script>
</body>
</html>"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)

