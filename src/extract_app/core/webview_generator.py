
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
    Generates a standalone HTML/JS webview for the book.
    """
    webview_dir = output_dir / "webview"
    webview_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Create Assets Structure
    css_dir = webview_dir / "css"
    js_dir = webview_dir / "js"
    css_dir.mkdir(exist_ok=True)
    js_dir.mkdir(exist_ok=True)
    
    # 2. Generate CSS
    _write_css(css_dir)
    
    # 3. Generate JS
    _write_js(js_dir, chapters)
    
    # 4. Generate HTML
    index_path = webview_dir / "index.html"
    _write_html(index_path, book_title, author)
    
    return index_path

def _write_css(css_dir: Path):
    css_content = """
    :root {
        --bg-color: #ffffff;
        --text-color: #2b2b2b;
        --accent-color: #1f6aa5;
        --sidebar-bg: #f5f5f5;
        --sidebar-border: #e0e0e0;
        --card-bg: #ffffff;
        --card-shadow: 0 2px 5px rgba(0,0,0,0.1);
        --header-height: 50px;
    }
    
    [data-theme="dark"] {
        --bg-color: #1e1e1e;
        --text-color: #e0e0e0;
        --accent-color: #4da6ff;
        --sidebar-bg: #252526;
        --sidebar-border: #333;
        --card-bg: #2d2d2d;
        --card-shadow: 0 2px 5px rgba(0,0,0,0.3);
    }

    body {
        margin: 0;
        padding: 0;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        background-color: var(--bg-color);
        color: var(--text-color);
        display: flex;
        height: 100vh;
        overflow: hidden;
    }

    /* Sidebar */
    .sidebar {
        width: 300px;
        background-color: var(--sidebar-bg);
        border-right: 1px solid var(--sidebar-border);
        display: flex;
        flex-direction: column;
        height: 100%;
        transition: transform 0.3s ease;
        position: relative;
        z-index: 100;
    }
    
    .sidebar.collapsed {
        transform: translateX(-300px);
        position: absolute;
    }
    
    .sidebar-header {
        padding: 15px;
        border-bottom: 1px solid var(--sidebar-border);
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .sidebar-header h1 {
        margin: 0;
        font-size: 1.1rem;
        color: var(--accent-color);
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    
    .close-btn {
        background: none;
        border: none;
        color: var(--text-color);
        cursor: pointer;
        font-size: 1.2rem;
        display: none; /* Only show on mobile */
    }

    .toc {
        flex: 1;
        overflow-y: auto;
        padding: 10px;
    }
    
    .toc-item {
        padding: 8px 15px;
        cursor: pointer;
        border-radius: 5px;
        margin-bottom: 2px;
        transition: background 0.2s;
        font-size: 0.9rem;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    
    .toc-item:hover {
        background-color: rgba(0,0,0,0.05);
    }
    
    [data-theme="dark"] .toc-item:hover {
        background-color: rgba(255,255,255,0.05);
    }
    
    .toc-item.active {
        background-color: var(--accent-color);
        color: white;
    }
    
    .toc-chapter {
        font-weight: bold;
        padding: 15px 10px 5px 10px;
        text-transform: uppercase;
        font-size: 0.8rem;
        color: gray;
        margin-top: 10px;
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
        padding: 0 20px;
        border-bottom: 1px solid var(--sidebar-border);
        display: flex;
        justify-content: space-between;
        align-items: center;
        background-color: var(--bg-color);
        z-index: 10;
    }
    
    .left-controls {
        display: flex;
        align-items: center;
        gap: 15px;
    }
    
    .menu-btn {
        background: none;
        border: none;
        font-size: 1.2rem;
        cursor: pointer;
        color: var(--text-color);
        padding: 5px;
    }
    
    .view-controls button {
        background: none;
        border: 1px solid var(--sidebar-border);
        color: var(--text-color);
        padding: 5px 10px;
        border-radius: 4px;
        cursor: pointer;
        font-size: 0.9rem;
        margin-left: 5px;
    }
    
    .view-controls button.active {
        background-color: var(--accent-color);
        color: white;
        border-color: var(--accent-color);
    }

    .reader-area {
        flex: 1;
        overflow-y: auto;
        padding: 20px;
        scroll-behavior: smooth;
    }
    
    .article-container {
        max-width: 900px;
        margin: 0 auto;
        padding-bottom: 50px;
    }
    
    .article-card {
        background-color: var(--card-bg);
        padding: 30px;
        margin-bottom: 30px;
        border-radius: 10px;
        box-shadow: var(--card-shadow);
    }
    
    .article-title {
        font-size: 1.5rem;
        margin-bottom: 20px;
        color: var(--accent-color);
        border-bottom: 2px solid var(--accent-color);
        padding-bottom: 10px;
    }
    
    .content-grid {
        display: grid;
        grid-template-columns: 1fr;
        gap: 20px;
    }
    
    .content-grid.dual-view {
        grid-template-columns: 1fr 1fr;
    }
    
    .text-block {
        line-height: 1.6;
        white-space: pre-wrap;
    }
    
    .translation-block {
        border-left: 3px solid var(--accent-color);
        padding-left: 15px;
    }
    
    .untranslated {
        color: gray;
        font-style: italic;
        background-color: rgba(0,0,0,0.03);
        padding: 10px;
        border-radius: 4px;
        text-align: center;
    }
    
    img {
        max-width: 100%;
        height: auto;
        display: block;
        margin: 20px auto;
        border-radius: 5px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    /* Headings */
    h1, h2, h3, h4, h5, h6 {
        color: var(--accent-color);
        margin-top: 20px;
        margin-bottom: 10px;
        line-height: 1.3;
    }
    h1 { font-size: 1.8rem; border-bottom: 1px solid var(--sidebar-border); padding-bottom: 5px; }
    h2 { font-size: 1.5rem; }
    h3 { font-size: 1.3rem; }
    h4 { font-size: 1.1rem; }
    h5, h6 { font-size: 1rem; font-weight: bold; }
    
    p {
        margin-bottom: 15px;
        text-align: justify;
    }
    
    ul, ol {
        margin-bottom: 15px;
        padding-left: 25px;
    }
    
    li {
        margin-bottom: 5px;
    }
    
    strong { font-weight: bold; color: var(--text-color); }
    em { font-style: italic; }

    /* Responsive */
    @media (max-width: 768px) {
        .sidebar {
            position: absolute;
            left: 0;
            top: 0;
            bottom: 0;
            transform: translateX(-100%);
        }
        
        .sidebar.open {
            transform: translateX(0);
        }
        
        .content-grid.dual-view {
            grid-template-columns: 1fr; /* Stack on mobile */
        }
        
        .close-btn {
            display: block;
        }
        
        .sidebar.collapsed {
            /* Reset for desktop logic override */
             transform: translateX(-100%);
        }
    }
    """
    with open(css_dir / "style.css", "w", encoding="utf-8") as f:
        f.write(css_content)

def _write_js(js_dir: Path, chapters: list):
    js_data = f"const bookData = {json.dumps(chapters)};"
    
    js_logic = r"""
    let currentViewMode = 'dual'; // 'original', 'translation', 'dual'
    let isSidebarOpen = true; // Desktop default

    document.addEventListener('DOMContentLoaded', () => {
        renderTOC();
        renderWelcome();
        checkResponsive();
        window.addEventListener('resize', checkResponsive);
    });
    
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
            // Mobile: use 'open' class
            if (isSidebarOpen) sidebar.classList.add('open');
            else sidebar.classList.remove('open');
        } else {
            // Desktop: use 'collapsed' class logic inverted
            // If open (true), remove collapsed. If closed (false), add collapsed.
            if (isSidebarOpen) sidebar.classList.remove('collapsed');
            else sidebar.classList.add('collapsed');
        }
    }

    function renderTOC() {
        const tocContainer = document.getElementById('toc-list');
        bookData.forEach((chapter, cIdx) => {
            const chapHeader = document.createElement('div');
            chapHeader.className = 'toc-chapter';
            chapHeader.textContent = chapter.title;
            tocContainer.appendChild(chapHeader);
            
            chapter.articles.forEach((article, aIdx) => {
                const item = document.createElement('div');
                item.className = 'toc-item';
                item.textContent = article.subtitle || 'Section ' + (aIdx + 1);
                item.onclick = () => { loadArticle(cIdx, aIdx, item); if(window.innerWidth<=768) toggleSidebar(); };
                tocContainer.appendChild(item);
            });
        });
    }
    
    function loadArticle(cIdx, aIdx, domItem) {
        document.querySelectorAll('.toc-item').forEach(el => el.classList.remove('active'));
        if(domItem) domItem.classList.add('active');
        
        const article = bookData[cIdx].articles[aIdx];
        const container = document.getElementById('content-display');
        container.innerHTML = '';
        
        const card = document.createElement('div');
        card.className = 'article-card';
        card.id = `art-${cIdx}-${aIdx}`;
        
        const title = document.createElement('div');
        title.className = 'article-title';
        title.textContent = article.subtitle;
        card.appendChild(title);
        
        const grid = document.createElement('div');
        grid.className = `content-grid ${currentViewMode === 'dual' ? 'dual-view' : ''}`;
        
        // Original
        const originalDiv = document.createElement('div');
        originalDiv.className = 'text-block';
        originalDiv.innerHTML = processContent(article.content_text);
        
        // Translation
        const transDiv = document.createElement('div');
        transDiv.className = 'text-block translation-block';
        if (article.translation_text && article.translation_text.trim()) {
            transDiv.innerHTML = processContent(article.translation_text);
        } else {
            transDiv.innerHTML = '<div class="untranslated">Chưa có bản dịch</div>';
        }
        
        if (currentViewMode !== 'translation') {
            grid.appendChild(originalDiv);
        }
        
        if (currentViewMode !== 'original') {
            grid.appendChild(transDiv);
        }
        
        card.appendChild(grid);
        container.appendChild(card);
        
        document.querySelector('.reader-area').scrollTop = 0;
    }
    
    function processContent(text) {
        if (!text) return '';
        
        let output = text;
        
        // 1. Sanitize (Basic)
        output = output.replace(/&/g, "&amp;")
             .replace(/</g, "&lt;")
             .replace(/>/g, "&gt;");
             
        // 2. Image replacement (Do this early to protect tags)
        // Format: [Image: filename.jpg - Caption: ...]
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
            return `__IMG__<figure><img src="../images/${file}" alt="${caption}"><figcaption>${caption}</figcaption></figure>__IMG__`;
        });

        // 3. Markdown Lines processing
        const lines = output.split('\n');
        let processed = [];
        let inList = false;
        
        lines.forEach(line => {
            let l = line.trimEnd(); // Keep leading indentation? Usually markdown ignores it unless code block.
            
            if (!l) {
                if (inList) { processed.push('</ul>'); inList = false; }
                processed.push(''); // Empty line for paragraph splitting
                return;
            }
            
            // Headings
            if (l.match(/^#{1,6}\s/)) {
                 if (inList) { processed.push('</ul>'); inList = false; }
                 l = l.replace(/^(#{1,6})\s+(.+)$/, (m, h, c) => `<h${h.length}>${c}</h${h.length}>`);
                 processed.push(l);
                 return;
            }
            
            // Lists (- item)
            if (l.match(/^-\s/)) {
                if (!inList) { processed.push('<ul>'); inList = true; }
                l = l.replace(/^-\s+(.+)$/, '<li>$1</li>');
                processed.push(l);
                return;
            }
            
            // End list if not empty and not list item
            if (inList) { processed.push('</ul>'); inList = false; }
            
            processed.push(l);
        });
        
        if (inList) processed.push('</ul>');
        
        output = processed.join('\n');
        
        // 4. Inline Formatting (Bold, Italic)
        output = output.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        output = output.replace(/\*(.*?)\*/g, '<em>$1</em>');
        
        // 5. Paragraphs (Split by double newline)
        // We preserved empty lines. Now we split by \n\n+ to make paragraphs
        // BUT we need to ignore HTML blocks we created (h1, ul, figure)
        
        const blocks = output.split(/\n\n+/);
        output = blocks.map(block => {
            block = block.trim();
            if (!block) return '';
            
            // Check if block is already an HTML element
            if (block.startsWith('<h') || block.startsWith('<ul>') || block.startsWith('__IMG__')) {
                return block.replace(/__IMG__/g, ''); // Remove placeholder
            }
            
            // Check for single newlines within paragraph -> <br>
            block = block.replace(/\n/g, '<br>');
            return `<p>${block}</p>`;
        }).join('\n');
        
        return output;
    }
    
    function setView(mode) {
        currentViewMode = mode;
        document.querySelectorAll('.view-controls button').forEach(b => b.classList.remove('active'));
        document.getElementById('btn-' + mode).classList.add('active');
        const active = document.querySelector('.toc-item.active');
        if (active) {
            // Re-render current article to apply view mode
            // We need to find cIdx/aIdx. For simplicity now, we rely on click simulation? 
            // Better: update classes. But here we re-render DOM for grid changes.
            active.click(); 
        }
    }
    
    function renderWelcome() {
        document.getElementById('content-display').innerHTML = '<div class="placeholder"><h2>Chào mừng!</h2><p>Chọn một mục lục bên trái để bắt đầu đọc.</p></div>';
    }

    window.setView = setView;
    window.toggleSidebar = toggleSidebar;
    """
    
    with open(js_dir / "app.js", "w", encoding="utf-8") as f:
        f.write(js_data + "\n" + js_logic)

def _write_html(path: Path, title: str, author: str):
    html = f"""
    <!DOCTYPE html>
    <html lang="vi">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title} - Reader</title>
        <link rel="stylesheet" href="css/style.css">
    </head>
    <body data-theme="light">
        <div class="sidebar">
            <div class="sidebar-header">
                <h1 title="{title}">{title}</h1>
                <button class="close-btn" onclick="toggleSidebar()">×</button>
            </div>
            <div class="toc" id="toc-list"></div>
        </div>
        
        <div class="main-content">
            <div class="toolbar">
                <div class="left-controls">
                    <button class="menu-btn" onclick="toggleSidebar()">☰</button>
                    <span>{author}</span>
                </div>
                <div class="view-controls">
                    <button id="btn-original" onclick="setView('original')">Gốc</button>
                    <button id="btn-dual" class="active" onclick="setView('dual')">Song Ngữ</button>
                    <button id="btn-translation" onclick="setView('translation')">Dịch</button>
                </div>
            </div>
            
            <div class="reader-area">
                <div class="article-container" id="content-display"></div>
            </div>
        </div>
        
        <script src="js/app.js"></script>
    </body>
    </html>
    """
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
