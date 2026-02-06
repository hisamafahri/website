# Hisam's Journal

A minimal, fast blog built with vanilla JavaScript and Python.

## Quick Start

```bash
# Start development server
python3 dev.py

# Preview with production caching
python3 dev.py --prod

# Build for deployment
python3 build.py
```

On all command, the server will:
- Generate pages manifest from `content/*.md` files
- Generate RSS feed from `content/journals/*.md` files  
- Generate `sitemap.xml`
- Start server at `http://localhost:3000`
