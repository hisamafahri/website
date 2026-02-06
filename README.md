# Hisam's Journal

A minimal, fast static site generator built with Python.

## Quick Start

```bash
# Start development server (rebuilds on start)
python3 dev.py

# Preview with production caching
python3 dev.py --prod

# Build for deployment
python3 build.py
```

## How It Works

The build process:
1. Reads all markdown files from `content/journals/*.md` and `content/*.md`
2. Converts markdown to HTML using a custom parser
3. Generates static HTML files in `dist/` directory
4. Creates RSS feed at `dist/rss.xml`
5. Generates sitemap at `dist/sitemap.xml`

All pages are pre-rendered at build time, eliminating the need for client-side API calls to fetch markdown files.

## Deployment

After running `python3 build.py`, deploy the `dist/` directory to your hosting provider. The site is completely static with no runtime dependencies.

**Benefits:**
- Zero API calls to fetch markdown files
- No egress costs for markdown content
- Faster page loads
- Better SEO (pre-rendered HTML)
- Works without JavaScript
