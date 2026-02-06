#!/usr/bin/env python3
"""
Development server for Hisam's Journal
Builds the static site and serves it
"""

import http.server
import socketserver
import os
import sys
from pathlib import Path
from urllib.parse import urlparse

# Import build functions
from build import generate_static_site, generate_rss, generate_sitemap, BUILD_DIR

PORT = 3000
# Check if running in development mode (default)
DEV_MODE = '--prod' not in sys.argv

class StaticHandler(http.server.SimpleHTTPRequestHandler):
    def guess_type(self, path):
        # Override to ensure .txt files are served as text/plain with UTF-8
        if path.endswith('.txt'):
            return 'text/plain; charset=utf-8'
        return super().guess_type(path)
    
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
            # Cache HTML for 5 minutes
            elif self.path.endswith('.html') or '.' not in os.path.basename(self.path):
                self.send_header('Cache-Control', 'public, max-age=300')
        
        super().end_headers()
    
    def do_GET(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        # Remove trailing slash (except for root path) - redirect to non-trailing
        if path.endswith('/') and path != '/':
            # Redirect to path without trailing slash
            self.send_response(301)
            new_path = path.rstrip('/')
            # Preserve query string if present
            new_location = new_path + ('?' + parsed_path.query if parsed_path.query else '')
            self.send_header('Location', new_location)
            self.end_headers()
            return
        
        # Let SimpleHTTPRequestHandler handle the rest
        return super().do_GET()
    
    def do_HEAD(self):
        """Handle HEAD requests - same redirect logic as GET"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        # Remove trailing slash (except for root path) - redirect to non-trailing
        if path.endswith('/') and path != '/':
            # Redirect to path without trailing slash
            self.send_response(301)
            new_path = path.rstrip('/')
            # Preserve query string if present
            new_location = new_path + ('?' + parsed_path.query if parsed_path.query else '')
            self.send_header('Location', new_location)
            self.end_headers()
            return
        
        # Let SimpleHTTPRequestHandler handle the rest
        return super().do_HEAD()
    
    def send_head(self):
        """Override send_head to serve .html files and directories without redirecting"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        # First check if a .html file exists for this path (e.g., /about -> /about.html)
        if not path.endswith(('.html', '/')) and path != '/':
            html_file = self.translate_path(path + '.html')
            if os.path.exists(html_file) and os.path.isfile(html_file):
                # Serve the .html file
                self.path = path + '.html'
                return super().send_head()
        
        # If path doesn't end with / and is a directory, serve index.html without redirecting
        if not path.endswith('/') and path != '':
            file_path = self.translate_path(path)
            if os.path.isdir(file_path):
                # Check if index.html exists
                index = os.path.join(file_path, "index.html")
                if os.path.exists(index):
                    # Serve the index.html directly without redirecting
                    self.path = path + '/index.html'
                    return super().send_head()
        
        return super().send_head()

class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True

# Generate static site before starting server
print("Generating static site...")
generate_static_site()
generate_rss()
generate_sitemap()
print()

# Change to build directory to serve files
os.chdir(BUILD_DIR)

with ReusableTCPServer(("", PORT), StaticHandler) as httpd:
    mode = "development" if DEV_MODE else "production"
    print(f"Server running at http://localhost:{PORT}/ ({mode} mode)")
    if not DEV_MODE:
        print("Caching enabled for production")
    print("Press Ctrl+C to stop")
    httpd.serve_forever()
