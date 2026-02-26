const bookData = [{"title": "Chapter 1", "articles": [{"subtitle": "Test Article", "content_text": "# Heading 1\nThis is a paragraph.\n\n## Heading 2\n- Item 1\n- Item 2\n\n**Bold text** and *italic text*.\n\n[Image: test.jpg]", "translation_text": "# Ti\u00eau \u0111\u1ec1 1\n\u0110\u00e2y l\u00e0 \u0111o\u1ea1n v\u0103n.\n\n## Ti\u00eau \u0111\u1ec1 2\n- M\u1ee5c 1\n- M\u1ee5c 2\n\n**In \u0111\u1eadm** v\u00e0 *in nghi\u00eang*."}]}];

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
    