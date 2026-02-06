#!/usr/bin/env python3
"""
Development server for Hisam's Journal
Runs a local server on port 3000 with hot-reload support
"""

import http.server
import socketserver
import os
import re
from pathlib import Path
from urllib.parse import urlparse, unquote

PORT = 3000

class JournalHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Custom HTTP request handler with redirect logic"""
    
    def do_GET(self):
        """Handle GET requests with custom routing and redirects"""
        
        # Parse the URL path
        parsed_path = urlparse(self.path)
        path = unquote(parsed_path.path)
        
        # Remove trailing slashes (except for root)
        if path != '/' and path.endswith('/'):
            # Redirect to path without trailing slash
            new_path = path.rstrip('/')
            if parsed_path.query:
                new_path += '?' + parsed_path.query
            self.send_response(301)
            self.send_header('Location', new_path)
            self.end_headers()
            return
        
        # Handle static pages: redirect /about/ to /about
        static_pages = ['about', 'uses', 'now', 'crafts', 'contact', 'projects']
        for page in static_pages:
            if path == f'/{page}/':
                self.send_response(301)
                self.send_header('Location', f'/{page}')
                self.end_headers()
                return
        
        # Handle journal URLs with specific redirect logic
        if path.startswith('/journals/'):
            journal_path = path.replace('/journals/', '')
            
            # Match pattern: /journals/YYYY-MM-DD or /journals/YYYY-MM-DD/
            date_only_match = re.match(r'^(\d{4}-\d{2}-\d{2})/?$', journal_path)
            if date_only_match:
                # Redirect to /journals/YYYY-MM-DD/normalized-title
                date_slug = date_only_match.group(1)
                
                # Try to find the corresponding markdown file
                md_file = Path(f'content/journals/{date_slug}.md')
                if md_file.exists():
                    # Read the title from the markdown file
                    try:
                        with open(md_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # Parse frontmatter for title
                        title_match = re.search(r'^title\s*=\s*"(.+)"$', content, re.MULTILINE)
                        if title_match:
                            title = title_match.group(1)
                            title_slug = self.slugify(title)
                            redirect_url = f'/journals/{date_slug}/{title_slug}'
                            
                            self.send_response(301)
                            self.send_header('Location', redirect_url)
                            self.end_headers()
                            return
                    except:
                        pass
                
                # If we can't find the file or parse it, return 404
                self.send_error(404, 'Journal not found')
                return
            
            # Match pattern: /journals/YYYY-MM-DD/anything/ (with trailing slash)
            path_with_slash_match = re.match(r'^(\d{4}-\d{2}-\d{2})/(.+)/$', journal_path)
            if path_with_slash_match:
                date_slug = path_with_slash_match.group(1)
                title_part = path_with_slash_match.group(2)
                
                # Redirect to URL without trailing slash
                redirect_url = f'/journals/{date_slug}/{title_part}'
                self.send_response(301)
                self.send_header('Location', redirect_url)
                self.end_headers()
                return
            
            # Match pattern: /journals/YYYY-MM-DD/anything (without trailing slash)
            path_match = re.match(r'^(\d{4}-\d{2}-\d{2})/(.+)$', journal_path)
            if path_match:
                date_slug = path_match.group(1)
                # Any string after the date is acceptable, we'll resolve to the markdown file
                # The client-side JavaScript will handle displaying the correct content
                # Just verify the markdown file exists
                md_file = Path(f'content/journals/{date_slug}.md')
                if not md_file.exists():
                    self.send_error(404, 'Journal not found')
                    return
                # Fall through to serve index.html
        
        # For all other paths, serve index.html (SPA)
        if path == '/' or path.startswith('/journals') or path in [f'/{p}' for p in static_pages]:
            self.path = '/index.html'
        
        # Serve the file
        return super().do_GET()
    
    def slugify(self, text):
        """Convert text to URL-friendly slug"""
        return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')
    
    def end_headers(self):
        """Add CORS headers for development"""
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        self.send_header('Expires', '0')
        return super().end_headers()

def run_server():
    """Start the development server"""
    Handler = JournalHTTPRequestHandler
    
    # Change to the project directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print("="*50)
        print(f"🚀 Development server running!")
        print(f"   URL: http://localhost:{PORT}")
        print("="*50)
        print("\nPress Ctrl+C to stop the server\n")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\n" + "="*50)
            print("Server stopped")
            print("="*50)

if __name__ == '__main__':
    run_server()
