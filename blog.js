// Simple markdown parser with custom frontmatter support
const Blog = {
    posts: [],
    pages: {},
    
    async init() {
        await this.loadPosts();
        await this.loadPages();
        this.route();
        window.addEventListener('popstate', () => this.route());
    },
    
    async loadPages() {
        try {
            // Fetch the list of markdown files from the content directory
            // We'll use a known endpoint or discover files via fetch
            // Since we can't directly list directory in browser, we'll fetch a manifest
            // For now, let's try to fetch files and handle 404s gracefully
            
            // Try to fetch a pages.json manifest first
            let pageFiles = [];
            try {
                const manifestResponse = await fetch('/content/pages.json');
                if (manifestResponse.ok) {
                    pageFiles = await manifestResponse.json();
                }
            } catch (e) {
                // If manifest doesn't exist, fall back to trying common page names
                const commonPages = ['about.md', 'now.md', 'uses.md', 'contact.md', 'projects.md'];
                pageFiles = commonPages;
            }
            
            // Attempt to load each page file
            for (const file of pageFiles) {
                try {
                    const response = await fetch(`/content/${file}`);
                    if (!response.ok) continue; // Skip if file doesn't exist
                    
                    const content = await response.text();
                    const page = this.parseMarkdown(content, file);
                    const pageName = file.replace('.md', '');
                    this.pages[pageName] = page;
                } catch (error) {
                    // Silently skip files that don't exist
                    console.debug(`Skipping ${file}:`, error);
                }
            }
        } catch (error) {
            console.error('Error loading pages:', error);
        }
    },
    
    async loadPosts() {
        const contentFiles = [
            'journals/2023-01-29.md',
            'journals/2023-02-03.md',
            'journals/2023-02-20.md',
            'journals/2023-03-12.md',
            'journals/2023-04-24.md',
            'journals/2023-08-24.md',
            'journals/2023-09-23.md',
            'journals/2024-01-05.md',
            'journals/2024-02-02.md',
            'journals/2024-02-08.md',
            'journals/2024-02-17.md',
            'journals/2024-02-21.md',
            'journals/2024-03-12.md',
            'journals/2024-03-30.md',
            'journals/2024-04-28.md',
            'journals/2024-06-17.md',
            'journals/2024-07-06.md',
            'journals/2024-07-27.md',
            'journals/2025-02-10.md',
            'journals/2025-02-26.md',
            'journals/2025-06-05.md',
            'journals/2025-07-14.md'
        ];
        
        for (const file of contentFiles) {
            try {
                const response = await fetch(`/content/${file}`);
                const content = await response.text();
                const post = this.parseMarkdown(content, file);
                this.posts.push(post);
            } catch (error) {
                console.error(`Error loading ${file}:`, error);
            }
        }
        
        this.posts.sort((a, b) => new Date(b.dateObj) - new Date(a.dateObj));
    },
    
    parseMarkdown(content, filename) {
        const lines = content.split('\n');
        const meta = {};
        let contentStart = 0;
        
        // Parse custom frontmatter (+++...+++)
        if (lines[0] === '+++') {
            for (let i = 1; i < lines.length; i++) {
                if (lines[i] === '+++') {
                    contentStart = i + 1;
                    break;
                }
                const match = lines[i].match(/^(\w+)\s*=\s*"(.+)"$/);
                if (match) {
                    meta[match[1]] = match[2];
                }
            }
        }
        
        const markdownContent = lines.slice(contentStart).join('\n').trim();
        const result = this.markdownToHtml(markdownContent);
        
        // Generate slug from filename and title
        const dateSlug = filename.replace('.md', '').replace('journals/', '');
        const titleSlug = this.slugify(meta.title || 'untitled');
        
        return {
            title: meta.title || 'Untitled',
            description: meta.description || '',
            date: meta.date || '',
            dateObj: this.parseDate(meta.date || filename),
            dateSlug: dateSlug,
            titleSlug: titleSlug,
            slug: `${dateSlug}/${titleSlug}`,
            path: filename.replace('.md', ''),
            content: result.html,
            footnotes: result.footnotes
        };
    },
    
    slugify(text) {
        return text
            .toLowerCase()
            .replace(/[^a-z0-9]+/g, '-')
            .replace(/^-+|-+$/g, '');
    },
    
    parseDate(dateStr) {
        // Try to parse "DD Mon YYYY" format or extract from filename
        const monthMap = {
            'Jan': 0, 'Feb': 1, 'Mar': 2, 'Apr': 3, 'May': 4, 'Jun': 5,
            'Jul': 6, 'Aug': 7, 'Sep': 8, 'Oct': 9, 'Nov': 10, 'Dec': 11
        };
        
        const match = dateStr.match(/(\d+)\s+(\w+)\s+(\d+)/);
        if (match) {
            const day = parseInt(match[1]);
            const month = monthMap[match[2]];
            const year = parseInt(match[3]);
            return new Date(year, month, day);
        }
        
        // Fallback: extract from YYYY-MM-DD format
        const fileMatch = dateStr.match(/(\d{4})-(\d{2})-(\d{2})/);
        if (fileMatch) {
            return new Date(fileMatch[1], parseInt(fileMatch[2]) - 1, fileMatch[3]);
        }
        
        return new Date();
    },
    
    markdownToHtml(markdown) {
        // Extract footnote definitions
        const footnotes = {};
        let html = markdown.replace(/^\[\^(\d+)\]:\s*(.+)$/gm, (match, num, content) => {
            footnotes[num] = content.trim();
            return ''; // Remove footnote definitions from content
        });
        
        // First, protect code blocks by replacing them with placeholders
        const codeBlocks = [];
        html = html.replace(/```(\w*)\n([\s\S]*?)```/g, (match, lang, code) => {
            const placeholder = `<!--CODEBLOCK${codeBlocks.length}-->`;
            const langClass = lang ? ` class="language-${lang}"` : '';
            codeBlocks.push(`<pre><code${langClass}>${this.escapeHtml(code.trim())}</code></pre>`);
            return placeholder;
        });
        
        // Process tables
        const lines = html.split('\n');
        let result = [];
        let inTable = false;
        let tableRows = [];
        
        for (let i = 0; i < lines.length; i++) {
            const line = lines[i];
            
            // Skip code block placeholders
            if (line.includes('<!--CODEBLOCK')) {
                if (inTable) {
                    result.push(this.renderTable(tableRows));
                    tableRows = [];
                    inTable = false;
                }
                result.push(line);
                continue;
            }
            
            // Detect table rows (contains |)
            if (line.trim().match(/^\|(.+)\|$/)) {
                // Check if it's a separator row (|---|---|)
                if (line.match(/^\|[\s:-]+\|$/)) {
                    continue; // Skip separator
                }
                
                if (!inTable) {
                    inTable = true;
                    tableRows = [];
                }
                
                const cells = line.split('|').slice(1, -1).map(c => c.trim());
                tableRows.push(cells);
            } else {
                if (inTable) {
                    // End of table, render it
                    result.push(this.renderTable(tableRows));
                    tableRows = [];
                    inTable = false;
                }
                result.push(line);
            }
        }
        
        if (inTable) {
            result.push(this.renderTable(tableRows));
        }
        
        html = result.join('\n');
        
        // Process blockquotes (multi-line support)
        const blockquoteLines = html.split('\n');
        let processedLines = [];
        let inBlockquote = false;
        let blockquoteContent = [];
        
        for (let i = 0; i < blockquoteLines.length; i++) {
            const line = blockquoteLines[i];
            
            if (line.trim().startsWith('> ')) {
                if (!inBlockquote) {
                    inBlockquote = true;
                    blockquoteContent = [];
                }
                blockquoteContent.push(line.trim().substring(2)); // Remove "> "
            } else if (line.trim() === '>') {
                if (!inBlockquote) {
                    inBlockquote = true;
                    blockquoteContent = [];
                }
                blockquoteContent.push('');
            } else {
                if (inBlockquote) {
                    // End blockquote
                    processedLines.push(`<blockquote>${blockquoteContent.join('<br>')}</blockquote>`);
                    blockquoteContent = [];
                    inBlockquote = false;
                }
                processedLines.push(line);
            }
        }
        
        if (inBlockquote) {
            processedLines.push(`<blockquote>${blockquoteContent.join('<br>')}</blockquote>`);
        }
        
        html = processedLines.join('\n');
        
        // Process lists (bullet and numbered)
        const listLines = html.split('\n');
        let listResult = [];
        let inUl = false;
        let inOl = false;
        
        for (let i = 0; i < listLines.length; i++) {
            const line = listLines[i];
            const trimmedLine = line.trim();
            
            // Check for unordered list item (- or *)
            const ulMatch = trimmedLine.match(/^[-*]\s+(.+)$/);
            // Check for ordered list item (1. or 2. etc)
            const olMatch = trimmedLine.match(/^(\d+)\.\s+(.+)$/);
            
            if (ulMatch) {
                if (inOl) {
                    listResult.push('</ol>');
                    inOl = false;
                }
                if (!inUl) {
                    listResult.push('<ul>');
                    inUl = true;
                }
                listResult.push(`<li>${ulMatch[1]}</li>`);
            } else if (olMatch) {
                if (inUl) {
                    listResult.push('</ul>');
                    inUl = false;
                }
                if (!inOl) {
                    listResult.push('<ol>');
                    inOl = true;
                }
                listResult.push(`<li>${olMatch[2]}</li>`);
            } else {
                // Not a list item
                if (inUl) {
                    listResult.push('</ul>');
                    inUl = false;
                }
                if (inOl) {
                    listResult.push('</ol>');
                    inOl = false;
                }
                listResult.push(line);
            }
        }
        
        // Close any open lists
        if (inUl) listResult.push('</ul>');
        if (inOl) listResult.push('</ol>');
        
        html = listResult.join('\n');
        
        // Horizontal rules (---, ***, ___)
        html = html.replace(/^---+$/gm, '<hr>');
        html = html.replace(/^\*\*\*+$/gm, '<hr>');
        html = html.replace(/^___+$/gm, '<hr>');
        
        // Headers with IDs for anchor links
        html = html.replace(/^### (.+)$/gm, (match, text) => {
            const id = this.slugify(text);
            return `<h3 id="${id}">${text} <a href="#${id}" class="header-link">#</a></h3>`;
        });
        html = html.replace(/^## (.+)$/gm, (match, text) => {
            const id = this.slugify(text);
            return `<h2 id="${id}">${text} <a href="#${id}" class="header-link">#</a></h2>`;
        });
        html = html.replace(/^# (.+)$/gm, (match, text) => {
            const id = this.slugify(text);
            return `<h1 id="${id}">${text} <a href="#${id}" class="header-link">#</a></h1>`;
        });
        
        // Images (must come before links)
        html = html.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, '<img src="$2" alt="$1">');
        
        // Links
        html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2">$1</a>');
        
        // Bold (before italic to handle ** before *)
        html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
        
        // Italic (underscore syntax for better control)
        html = html.replace(/_([^_]+)_/g, '<em>$1</em>');
        
        // Italic (asterisk syntax - but avoid matching already processed **)
        html = html.replace(/(?<!\*)\*(?!\*)([^*]+)\*(?!\*)/g, '<em>$1</em>');
        
        // Inline code
        html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
        
        // Footnote references - replace with simple superscript links
        html = html.replace(/\[\^(\d+)\]/g, (match, num) => {
            return `<span class="footnote-ref"><sup><a href="#fn${num}" id="fnref${num}">${num}</a></sup></span>`;
        });
        
        // Paragraphs
        const pLines = html.split('\n');
        let inParagraph = false;
        let pResult = [];
        
        for (let i = 0; i < pLines.length; i++) {
            const line = pLines[i].trim();
            
            if (line === '') {
                if (inParagraph) {
                    pResult.push('</p>');
                    inParagraph = false;
                }
                continue;
            }
            
            // Check if line is a block element or code placeholder
            if (line.startsWith('<h') || line.startsWith('<blockquote>') || 
                line.startsWith('<pre>') || line.startsWith('<table>') ||
                line.startsWith('<img') || line.includes('<!--CODEBLOCK') ||
                line.startsWith('<ul>') || line.startsWith('</ul>') ||
                line.startsWith('<ol>') || line.startsWith('</ol>') ||
                line.startsWith('<li>') || line === '<hr>') {
                if (inParagraph) {
                    pResult.push('</p>');
                    inParagraph = false;
                }
                pResult.push(line);
            } else {
                if (!inParagraph) {
                    pResult.push('<p>');
                    inParagraph = true;
                }
                pResult.push(line + ' ');
            }
        }
        
        if (inParagraph) {
            pResult.push('</p>');
        }
        
        html = pResult.join('\n');
        
        // Restore code blocks
        codeBlocks.forEach((block, i) => {
            html = html.replace(`<!--CODEBLOCK${i}-->`, block);
        });
        
        // Process footnote content for sidebar
        const processedFootnotes = {};
        for (const [num, content] of Object.entries(footnotes)) {
            processedFootnotes[num] = content
                .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2">$1</a>')
                .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
                .replace(/\*(.+?)\*/g, '<em>$1</em>')
                .replace(/`([^`]+)`/g, '<code>$1</code>');
        }
        
        return {
            html: html,
            footnotes: processedFootnotes
        };
    },
    
    escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, m => map[m]);
    },
    
    renderTable(rows) {
        if (rows.length === 0) return '';
        
        let html = '<table>\n';
        
        // First row is header
        html += '<tr>';
        for (const cell of rows[0]) {
            html += `<th>${cell}</th>`;
        }
        html += '</tr>\n';
        
        // Remaining rows are body
        for (let i = 1; i < rows.length; i++) {
            html += '<tr>';
            for (const cell of rows[i]) {
                html += `<td>${cell}</td>`;
            }
            html += '</tr>\n';
        }
        
        html += '</table>';
        return html;
    },
    
    route() {
        const path = window.location.pathname.replace(/\/$/, '');
        
        if (!path || path === '' || path === '/index.html') {
            this.renderHome();
            return;
        }
        
        // Remove leading slash
        const cleanPath = path.replace(/^\//, '');
        
        // Handle static pages dynamically
        // Check if the cleanPath matches any loaded page
        if (this.pages[cleanPath]) {
            this.renderPage(this.pages[cleanPath], cleanPath);
            return;
        }
        
        // Handle redirects: /essay/, /essays/, /journal/ -> /journals/
        let normalizedPath = cleanPath;
        if (cleanPath.startsWith('essay/') || cleanPath.startsWith('essays/')) {
            normalizedPath = cleanPath.replace(/^essays?\//, 'journals/');
            const post = this.findPost(normalizedPath);
            if (post) {
                window.history.replaceState(null, '', `/journals/${post.slug}`);
                this.renderPost(post);
                return;
            }
        }
        if (cleanPath.startsWith('journal/')) {
            normalizedPath = cleanPath.replace(/^journal\//, 'journals/');
            const post = this.findPost(normalizedPath);
            if (post) {
                window.history.replaceState(null, '', `/journals/${post.slug}`);
                this.renderPost(post);
                return;
            }
        }
        
        // Find post
        const post = this.findPost(normalizedPath);
        
        if (post) {
            this.renderPost(post);
        } else {
            this.render404();
        }
    },
    
    render404() {
        this.updateMeta('404 - Page Not Found', 'Page not found', window.location.pathname);
        
        const html = `404: Page not found`;
        
        document.getElementById('app').innerHTML = html;
    },
    
    findPost(pathOrSlug) {
        const cleanPath = pathOrSlug.replace(/^journals\//, '');
        
        // Extract date part (YYYY-MM-DD) from the path
        // Matches patterns like "2023-09-23" or "2023-09-23/anything-here"
        const dateMatch = cleanPath.match(/^(\d{4}-\d{2}-\d{2})/);
        
        if (dateMatch) {
            const dateOnly = dateMatch[1];
            // Find post by date slug
            const post = this.posts.find(p => p.dateSlug === dateOnly);
            if (post) return post;
        }
        
        // Fallback: try exact slug match
        let post = this.posts.find(p => p.slug === cleanPath);
        if (post) return post;
        
        // Try with 'journals/' prefix
        post = this.posts.find(p => p.slug === `journals/${cleanPath}` || p.dateSlug === cleanPath);
        return post;
    },
    
    updateMeta(title, description, url) {
        document.title = title;
        document.getElementById('page-title').textContent = title;
        document.getElementById('page-description').content = description;
        document.getElementById('og-title').content = title;
        document.getElementById('og-description').content = description;
        
        const canonicalUrl = window.location.origin + url;
        document.getElementById('canonical-url').href = canonicalUrl;
    },
    
    renderHome() {
        this.updateMeta('Hisam\'s Journal', 'Personal blog and writing', '/');
        
        const html = `
            ${this.posts.map(post => `
                <a href="/journals/${post.slug}">${post.title}</a><br>
            `).join('\n')}
        `;
        
        document.getElementById('app').innerHTML = html;
    },
    
    renderPage(page, pageName) {
        this.updateMeta(page.title, page.description, `/${pageName}`);
        
        // Build footnotes sidebar
        let footnotesSidebar = '';
        if (page.footnotes && Object.keys(page.footnotes).length > 0) {
            const footnoteItems = Object.entries(page.footnotes)
                .sort((a, b) => parseInt(a[0]) - parseInt(b[0]))
                .map(([num, content]) => `
                    <div class="footnote-item" id="fn${num}">
                        <sup>${num}</sup> ${content}
                    </div>
                `).join('');
            
            footnotesSidebar = `<div class="footnotes-sidebar">${footnoteItems}</div>`;
        }
        
        const html = `
            <div class="article-container">
                <div class="article-content">
                    ${page.content}
                </div>
                ${footnotesSidebar}
            </div>
        `;
        
        document.getElementById('app').innerHTML = html;
        
        // Handle internal links
        this.handleInternalLinks();
        
        // Scroll to hash if present
        this.scrollToHash();
    },
    
    renderPost(post) {
        this.updateMeta(post.title, post.description, `/journals/${post.slug}`);
        
        // Build footnotes sidebar
        let footnotesSidebar = '';
        if (post.footnotes && Object.keys(post.footnotes).length > 0) {
            const footnoteItems = Object.entries(post.footnotes)
                .sort((a, b) => parseInt(a[0]) - parseInt(b[0]))
                .map(([num, content]) => `
                    <div class="footnote-item" id="fn${num}">
                        <sup>${num}</sup> ${content}
                    </div>
                `).join('');
            
            footnotesSidebar = `<div class="footnotes-sidebar">${footnoteItems}</div>`;
        }
        
        const html = `
            <div class="article-container">
                <div class="article-content">
                    <a href="/">← Back</a>
                    <br><br>
                    <b>${post.title}</b>
                    <br>
                    ${post.date}
                    <br><br>
                    ${post.content}
                </div>
                ${footnotesSidebar}
            </div>
        `;
        
        document.getElementById('app').innerHTML = html;
        
        // Highlight code blocks with Prism
        if (typeof Prism !== 'undefined') {
            Prism.highlightAll();
        }
        
        // Align footnotes with their references on desktop
        if (window.innerWidth >= 1024 && post.footnotes) {
            requestAnimationFrame(() => {
                Object.keys(post.footnotes).forEach(num => {
                    const ref = document.getElementById(`fnref${num}`);
                    const note = document.getElementById(`fn${num}`);
                    
                    if (ref && note) {
                        const refTop = ref.getBoundingClientRect().top + window.scrollY;
                        const containerTop = document.querySelector('.article-container').getBoundingClientRect().top + window.scrollY;
                        note.style.position = 'absolute';
                        note.style.top = `${refTop - containerTop}px`;
                    }
                });
            });
        }
        
        // Handle internal links
        this.handleInternalLinks();
        
        // Scroll to hash if present
        this.scrollToHash();
    },
    
    scrollToHash() {
        const hash = window.location.hash;
        if (hash) {
            // Use setTimeout to ensure DOM is fully rendered and browser has painted
            setTimeout(() => {
                const element = document.querySelector(hash);
                if (element) {
                    element.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            }, 100);
        }
    },
    
    handleInternalLinks() {
        document.querySelectorAll('a').forEach(link => {
            if (link.href && link.href.startsWith(window.location.origin)) {
                link.addEventListener('click', (e) => {
                    e.preventDefault();
                    window.history.pushState(null, '', link.href);
                    this.route();
                });
            }
        });
    }
};

// Initialize the blog
Blog.init();
