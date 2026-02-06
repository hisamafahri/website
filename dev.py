#!/usr/bin/env python3
"""
Development server for Hisam's Journal
Auto-generates manifests and serves the site
"""

import http.server
import socketserver
import os
import sys
from urllib.parse import urlparse

# Import build functions
from build import generate_pages_manifest, generate_rss, generate_sitemap

PORT = 3000
# Check if running in development mode (default)
DEV_MODE = '--prod' not in sys.argv

class SPAHandler(http.server.SimpleHTTPRequestHandler):
    # Valid SPA routes that should serve index.html
    VALID_SPA_ROUTES = {'/', '/about', '/now', '/uses', '/crafts', '/journals'}
    
    def end_headers(self):
        if DEV_MODE:
            # Development: disable caching
            self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Expires', '0')
        else:
            # Production: enable caching
            # Cache static assets for 1 year
            if self.path.endswith(('.js', '.css', '.woff', '.woff2', '.ttf', '.jpg', '.jpeg', '.png', '.gif', '.svg', '.ico')):
                self.send_header('Cache-Control', 'public, max-age=31536000, immutable')
            # Cache markdown files for 1 hour
            elif self.path.endswith('.md'):
                self.send_header('Cache-Control', 'public, max-age=3600')
            # Cache HTML for 5 minutes
            elif self.path.endswith('.html') or '.' not in os.path.basename(self.path):
                self.send_header('Cache-Control', 'public, max-age=300')
        
        super().end_headers()
    
    def is_valid_spa_route(self, path):
        """Check if the path is a valid SPA route"""
        # Root path
        if path in self.VALID_SPA_ROUTES:
            return True
        
        # Journal paths (e.g., /journals/2023-01-29/slug)
        if path.startswith('/journals/'):
            return True
        
        # Legacy redirects
        if path.startswith('/essay/') or path.startswith('/essays/') or path.startswith('/journal/'):
            return True
        
        return False
    
    def do_GET(self):
        # Parse the URL
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        # Remove trailing slash
        if path.endswith('/') and path != '/':
            path = path[:-1]
        
        # Check if the file exists
        file_path = path[1:] if path.startswith('/') else path
        if file_path and os.path.isfile(file_path):
            # Serve the file normally
            return http.server.SimpleHTTPRequestHandler.do_GET(self)
        
        # Check if it's a valid SPA route
        if self.is_valid_spa_route(path):
            # Serve index.html for valid SPA routes
            self.path = '/index.html'
            return http.server.SimpleHTTPRequestHandler.do_GET(self)
        
        # Otherwise, serve 404 page
        self.path = '/404.html'
        self.send_response(404)
        return http.server.SimpleHTTPRequestHandler.do_GET(self)

class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True

# Generate manifests and feeds before starting server
print("Generating build artifacts...")
generate_pages_manifest()
generate_rss()
generate_sitemap()
print()

with ReusableTCPServer(("", PORT), SPAHandler) as httpd:
    mode = "development" if DEV_MODE else "production"
    print(f"Server running at http://localhost:{PORT}/ ({mode} mode)")
    if not DEV_MODE:
        print("Caching enabled for production")
    print("Press Ctrl+C to stop")
    httpd.serve_forever()
