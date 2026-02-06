#!/usr/bin/env python3
"""
Development server for Hisam's Journal
Runs a local server on port 3000 serving pre-built HTML files
"""

import http.server
import socketserver
import os
import re
import subprocess
from pathlib import Path
from urllib.parse import urlparse, unquote

PORT = 3000

class JournalHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Custom HTTP request handler with redirect logic"""
    
    def __init__(self, *args, **kwargs):
        # Serve from dist/ directory
        super().__init__(*args, directory='dist', **kwargs)
    
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
        
        # Handle journal URLs with specific redirect logic
        if path.startswith('/journals/'):
            journal_path = path.replace('/journals/', '')
            
            # Match pattern: /journals/YYYY-MM-DD
            date_only_match = re.match(r'^(\d{4}-\d{2}-\d{2})$', journal_path)
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
            
            # Match pattern: /journals/YYYY-MM-DD/anything
            path_match = re.match(r'^(\d{4}-\d{2}-\d{2})/(.+)$', journal_path)
            if path_match:
                date_slug = path_match.group(1)
                provided_slug = path_match.group(2)
                
                # Check if markdown file exists
                md_file = Path(f'content/journals/{date_slug}.md')
                if not md_file.exists():
                    self.send_error(404, 'Journal not found')
                    return
                
                # Serve the _fallback.html which contains the journal content
                # This allows any slug after the date to work
                self.path = f'/journals/{date_slug}/_fallback.html'
        
        # For clean URLs, try appending /index.html if path is a directory
        if not path.endswith('.html') and not path.endswith('.xml') and not path.endswith('.txt') and not path.endswith('.ico') and not path.endswith('.js') and not path.endswith('.css'):
            # Try to serve index.html from that directory
            test_path = (Path('dist') / path.lstrip('/')).resolve()
            
            # Security check: ensure the path is within dist/
            try:
                test_path.relative_to(Path('dist').resolve())
            except ValueError:
                self.send_error(403, 'Forbidden')
                return
            
            if test_path.is_dir():
                self.path = path.rstrip('/') + '/index.html'
        
        # Serve the file
        return super().do_GET()
    
    def slugify(self, text):
        """Convert text to URL-friendly slug"""
        return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')
    
    def send_error(self, code, message=None, explain=None):
        """Override to serve custom 404.html"""
        if code == 404:
            # Serve custom 404.html
            custom_404 = Path('dist/404.html')
            if custom_404.exists():
                try:
                    self.send_response(404)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    with open(custom_404, 'rb') as f:
                        self.wfile.write(f.read())
                    return
                except:
                    pass
        
        # Fall back to default error handling
        return super().send_error(code, message, explain)
    
    def end_headers(self):
        """Add CORS headers for development"""
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        self.send_header('Expires', '0')
        return super().end_headers()

def run_build():
    """Run build.py first"""
    print("Building site...")
    result = subprocess.run(['python3', 'build.py'], capture_output=True, text=True)
    
    if result.returncode != 0:
        print("Build failed!")
        print(result.stderr)
        return False
    
    print(result.stdout)
    return True

def run_server():
    """Start the development server"""
    
    # Build first
    if not run_build():
        return
    
    Handler = JournalHTTPRequestHandler
    
    # Change to the project directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print("="*50)
        print(f"🚀 Development server running!")
        print(f"   URL: http://localhost:{PORT}")
        print("="*50)
        print("\nPress Ctrl+C to stop the server")
        print("(Restart server to rebuild after changes)\n")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\n" + "="*50)
            print("Server stopped")
            print("="*50)

if __name__ == '__main__':
    run_server()
