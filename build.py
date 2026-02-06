#!/usr/bin/env python3
"""
Build script for Hisam's Journal
Generates static HTML files (no markdown files served to client)
"""

import os
import json
import shutil
import re
from pathlib import Path
from datetime import datetime
import markdown
from xml.etree import ElementTree as ET

SITE_NAME = "Hisam's Journal"
BASE_URL = "https://hisam.dev"
CONTENT_DIR = Path("content")
DIST_DIR = Path("dist")
JOURNALS_DIR = CONTENT_DIR / "journals"

# HTML template
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <meta name="description" content="{description}">
    <meta property="og:title" content="{title}">
    <meta property="og:description" content="{description}">
    <meta property="og:type" content="website">
    <link rel="canonical" href="{canonical_url}">
    <link rel="alternate" type="application/rss+xml" title="Hisam's Journal RSS Feed" href="/rss.xml">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap" rel="stylesheet">
    <link href="/prism.css" rel="stylesheet" />
    <style>
        body {{
            margin: 0;
            padding: 0;
            font-family: 'Roboto', sans-serif;
        }}
        
        nav {{
            background-color: #004F19;
            padding: 10px 0;
            margin-bottom: 40px;
        }}
        
        nav .nav-container {{
            max-width: 650px;
            margin: 0 auto;
            padding: 0 10px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        nav .site-title {{
            font-weight: bold;
            font-size: 18px;
        }}
        
        nav .site-title a {{
            text-decoration: none;
            color: #FFF;
        }}
        
        nav .nav-links {{
            display: flex;
            gap: 20px;
        }}

        nav .nav-links a {{
            color: #FFF;
            text-decoration: none;
        }}
        
        #app {{
            max-width: 650px;
            margin: 0 auto;
            padding: 0 10px;
        }}
        
        a {{ color: #00e; }}
        a:visited {{ color: #551a8b; }}
        img {{ max-width: 100%; }}
        pre {{ overflow: auto; background: none !important; }}
        code[class*="language-"], pre[class*="language-"] {{ 
          background: none !important; 
          font-size: 0.8rem;
        }}
        
        h1, h2, h3 {{
            position: relative;
        }}
        
        .header-link {{
            opacity: 0;
            margin-left: 8px;
            text-decoration: none;
            color: #ccc;
            font-weight: normal;
            transition: opacity 0.2s;
        }}
        
        h1:hover .header-link,
        h2:hover .header-link,
        h3:hover .header-link {{
            opacity: 1;
        }}
        
        ul, ol {{
            margin: 16px 0;
            padding-left: 30px;
        }}
        
        li {{
            margin: 8px 0;
            line-height: 1.6;
        }}
        
        hr {{
            border: none;
            border-top: 1px solid #ccc;
            margin: 30px 0;
        }}
        
        table {{ border-collapse: collapse; }}
        td, th {{ border: 1px solid #000; padding: 4px; }}
        blockquote {{
            margin: 20px 0;
            padding-left: 20px;
            border-left: 3px solid #ccc;
            color: #666;
            font-style: italic;
        }}
        blockquote em {{
            font-style: italic;
        }}
        
        @media (min-width: 1024px) {{
            nav .nav-container {{
                max-width: 1000px;
            }}
            
            #app {{
                max-width: 1000px;
            }}
        }}
    </style>
</head>
<body>
    <nav>
        <div class="nav-container">
            <div class="site-title">
                <a href="/">Hisam's Journal</a>
            </div>
            <div class="nav-links">
                <a href="/about">about</a>
                <a href="/now">now</a>
                <a href="/rss.xml">rss</a>
            </div>
        </div>
    </nav>
    <div id="app">
        {content}
    </div>
    <script src="/prism.js"></script>
    <script>
        if (typeof Prism !== 'undefined') {{
            Prism.highlightAll();
        }}
    </script>
</body>
</html>
"""

def slugify(text):
    """Convert text to URL-friendly slug"""
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')

def parse_frontmatter(content):
    """Parse +++ frontmatter from markdown content"""
    lines = content.split('\n')
    meta = {}
    content_start = 0
    
    if lines[0].strip() == '+++':
        for i in range(1, len(lines)):
            if lines[i].strip() == '+++':
                content_start = i + 1
                break
            match = re.match(r'^(\w+)\s*=\s*"(.+)"$', lines[i])
            if match:
                meta[match.group(1)] = match.group(2)
    
    markdown_content = '\n'.join(lines[content_start:]).strip()
    return meta, markdown_content

def parse_date(date_str):
    """Parse date from 'DD Mon YYYY' format"""
    try:
        return datetime.strptime(date_str, '%d %b %Y')
    except:
        # Fallback to current date
        return datetime.now()

def read_markdown_file(filepath):
    """Read and parse a markdown file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    meta, markdown_content = parse_frontmatter(content)
    
    # Convert markdown to HTML
    md = markdown.Markdown(extensions=[
        'tables',
        'fenced_code',
        'nl2br',
        'sane_lists'
    ])
    html_content = md.convert(markdown_content)
    
    return {
        'title': meta.get('title', 'Untitled'),
        'description': meta.get('description', ''),
        'date': meta.get('date', ''),
        'html': html_content,
        'meta': meta
    }

def get_all_journals():
    """Get all journal entries sorted by date (newest first)"""
    journals = []
    
    if not JOURNALS_DIR.exists():
        return journals
    
    for md_file in JOURNALS_DIR.glob('*.md'):
        filename = md_file.stem  # e.g., '2024-01-01'
        
        try:
            data = read_markdown_file(md_file)
            date_obj = parse_date(data['date']) if data['date'] else datetime.now()
            
            title_slug = slugify(data['title'])
            
            journals.append({
                'filename': filename,
                'date_slug': filename,
                'title': data['title'],
                'title_slug': title_slug,
                'description': data['description'],
                'date': data['date'],
                'date_obj': date_obj,
                'html': data['html'],
                'slug': f"{filename}/{title_slug}"
            })
        except Exception as e:
            print(f"Warning: Error processing {md_file}: {e}")
            continue
    
    # Sort by date (newest first)
    journals.sort(key=lambda x: x['date_obj'], reverse=True)
    return journals

def get_all_pages():
    """Get all static pages (about, uses, etc.)"""
    pages = []
    
    for md_file in CONTENT_DIR.glob('*.md'):
        page_name = md_file.stem
        
        try:
            data = read_markdown_file(md_file)
            pages.append({
                'name': page_name,
                'title': data['title'],
                'description': data['description'],
                'html': data['html']
            })
        except Exception as e:
            print(f"Warning: Error processing page {md_file}: {e}")
            continue
    
    return pages

def generate_html_file(output_path, title, description, content, canonical_url):
    """Generate an HTML file from template"""
    html = HTML_TEMPLATE.format(
        title=title,
        description=description,
        content=content,
        canonical_url=canonical_url
    )
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

def generate_journal_html(journal):
    """Generate HTML for a journal entry"""
    content = f"""
        <a href="/">← Back</a>
        <br><br>
        <b>{journal['title']}</b>
        <br>
        {journal['date']}
        <br><br>
        {journal['html']}
    """
    
    # Main journal HTML at /journals/YYYY-MM-DD/title-slug/index.html
    output_path = DIST_DIR / 'journals' / journal['date_slug'] / journal['title_slug'] / 'index.html'
    canonical_url = f"{BASE_URL}/journals/{journal['slug']}"
    
    generate_html_file(
        output_path,
        journal['title'],
        journal['description'],
        content,
        canonical_url
    )
    
    # Create redirect HTML at /journals/YYYY-MM-DD/index.html
    # This handles /journals/YYYY-MM-DD -> /journals/YYYY-MM-DD/title-slug
    redirect_path = DIST_DIR / 'journals' / journal['date_slug'] / 'index.html'
    redirect_path.parent.mkdir(parents=True, exist_ok=True)
    
    redirect_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta http-equiv="refresh" content="0; url=/journals/{journal['slug']}">
    <link rel="canonical" href="{BASE_URL}/journals/{journal['slug']}">
    <title>Redirecting...</title>
</head>
<body>
    <p>Redirecting to <a href="/journals/{journal['slug']}">{journal['title']}</a>...</p>
    <script>window.location.href='/journals/{journal['slug']}';</script>
</body>
</html>"""
    
    with open(redirect_path, 'w', encoding='utf-8') as f:
        f.write(redirect_html)
    
    # Create a fallback HTML for any other slug
    # This file will be used by a rewrite rule in Netlify
    fallback_path = DIST_DIR / 'journals' / journal['date_slug'] / '_fallback.html'
    generate_html_file(
        fallback_path,
        journal['title'],
        journal['description'],
        content,
        canonical_url
    )

def generate_page_html(page):
    """Generate HTML for a static page"""
    output_path = DIST_DIR / page['name'] / 'index.html'
    canonical_url = f"{BASE_URL}/{page['name']}"
    
    generate_html_file(
        output_path,
        page['title'],
        page['description'],
        page['html'],
        canonical_url
    )

def generate_homepage(journals):
    """Generate homepage with journal listing"""
    content = '\n'.join([
        f'<a href="/journals/{journal["slug"]}">{journal["title"]}</a><br>'
        for journal in journals
    ])
    
    output_path = DIST_DIR / 'index.html'
    
    generate_html_file(
        output_path,
        SITE_NAME,
        'Personal blog and writing',
        content,
        BASE_URL
    )

def generate_manifest(journals):
    """Generate manifest.json with metadata for client-side routing"""
    manifest = {
        'journals': [
            {
                'date_slug': j['date_slug'],
                'title': j['title'],
                'title_slug': j['title_slug'],
                'description': j['description'],
                'date': j['date'],
                'slug': j['slug']
            }
            for j in journals
        ]
    }
    
    with open(DIST_DIR / 'manifest.json', 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)

def generate_rss(journals):
    """Generate RSS feed"""
    rss = ET.Element('rss', version='2.0')
    rss.set('{http://www.w3.org/2005/Atom}atom', 'http://www.w3.org/2005/Atom')
    
    channel = ET.SubElement(rss, 'channel')
    
    title = ET.SubElement(channel, 'title')
    title.text = SITE_NAME
    
    link = ET.SubElement(channel, 'link')
    link.text = BASE_URL
    
    description = ET.SubElement(channel, 'description')
    description.text = 'Personal blog and writing'
    
    language = ET.SubElement(channel, 'language')
    language.text = 'en-us'
    
    atom_link = ET.SubElement(channel, '{http://www.w3.org/2005/Atom}link')
    atom_link.set('href', f'{BASE_URL}/rss.xml')
    atom_link.set('rel', 'self')
    atom_link.set('type', 'application/rss+xml')
    
    # Add items (journals)
    for journal in journals:
        item = ET.SubElement(channel, 'item')
        
        item_title = ET.SubElement(item, 'title')
        item_title.text = journal['title']
        
        item_link = ET.SubElement(item, 'link')
        item_link.text = f"{BASE_URL}/journals/{journal['slug']}"
        
        item_desc = ET.SubElement(item, 'description')
        item_desc.text = journal['description']
        
        guid = ET.SubElement(item, 'guid')
        guid.set('isPermaLink', 'true')
        guid.text = f"{BASE_URL}/journals/{journal['slug']}"
        
        pub_date = ET.SubElement(item, 'pubDate')
        pub_date.text = journal['date_obj'].strftime('%a, %d %b %Y 00:00:00 +0000')
    
    tree = ET.ElementTree(rss)
    ET.indent(tree, space='  ')
    return ET.tostring(rss, encoding='unicode', xml_declaration=True)

def generate_sitemap(journals, pages):
    """Generate sitemap.xml"""
    urlset = ET.Element('urlset')
    urlset.set('xmlns', 'http://www.sitemaps.org/schemas/sitemap/0.9')
    
    # Homepage
    url = ET.SubElement(urlset, 'url')
    loc = ET.SubElement(url, 'loc')
    loc.text = f'{BASE_URL}/'
    changefreq = ET.SubElement(url, 'changefreq')
    changefreq.text = 'weekly'
    priority = ET.SubElement(url, 'priority')
    priority.text = '1.0'
    
    # Static pages
    for page in pages:
        url = ET.SubElement(urlset, 'url')
        loc = ET.SubElement(url, 'loc')
        loc.text = f"{BASE_URL}/{page['name']}"
        changefreq = ET.SubElement(url, 'changefreq')
        changefreq.text = 'monthly'
        priority = ET.SubElement(url, 'priority')
        priority.text = '0.7'
    
    # Journals
    for journal in journals:
        url = ET.SubElement(urlset, 'url')
        loc = ET.SubElement(url, 'loc')
        loc.text = f"{BASE_URL}/journals/{journal['slug']}"
        lastmod = ET.SubElement(url, 'lastmod')
        lastmod.text = journal['date_obj'].strftime('%Y-%m-%d')
        changefreq = ET.SubElement(url, 'changefreq')
        changefreq.text = 'monthly'
        priority = ET.SubElement(url, 'priority')
        priority.text = '0.8'
    
    tree = ET.ElementTree(urlset)
    ET.indent(tree, space='    ')
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(urlset, encoding='unicode')

def copy_static_files():
    """Copy static files to dist/"""
    static_files = [
        'favicon.ico',
        '404.html',
        'pgp.txt',
        'prism.js',
        'prism.css',
        'robots.txt',
        '_redirects'
    ]
    
    for filename in static_files:
        src = Path(filename)
        if src.exists():
            dst = DIST_DIR / filename
            shutil.copy2(src, dst)
            print(f"  Copied: {filename}")
        else:
            print(f"  Warning: {filename} not found, skipping")

def build():
    """Main build function"""
    print(f"Building {SITE_NAME}...")
    print()
    
    # Clean dist directory
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    print(f"✓ Cleaned dist/ directory")
    
    # Get all content
    print("\nLoading content...")
    journals = get_all_journals()
    pages = get_all_pages()
    print(f"  Found {len(journals)} journals")
    print(f"  Found {len(pages)} pages")
    
    # Generate HTML files for journals
    print("\nGenerating journal HTML files...")
    for journal in journals:
        generate_journal_html(journal)
        print(f"  ✓ {journal['slug']}")
    
    # Generate HTML files for pages
    print("\nGenerating page HTML files...")
    for page in pages:
        generate_page_html(page)
        print(f"  ✓ {page['name']}")
    
    # Generate homepage
    print("\nGenerating homepage...")
    generate_homepage(journals)
    print("  ✓ index.html")
    
    # Generate manifest
    print("\nGenerating manifest...")
    generate_manifest(journals)
    print("  ✓ manifest.json")
    
    # Generate RSS
    print("\nGenerating RSS feed...")
    rss_content = generate_rss(journals)
    with open(DIST_DIR / 'rss.xml', 'w', encoding='utf-8') as f:
        f.write(rss_content)
    print("  ✓ rss.xml")
    
    # Generate sitemap
    print("\nGenerating sitemap...")
    sitemap_content = generate_sitemap(journals, pages)
    with open(DIST_DIR / 'sitemap.xml', 'w', encoding='utf-8') as f:
        f.write(sitemap_content)
    print("  ✓ sitemap.xml")
    
    # Copy static files
    print("\nCopying static files...")
    copy_static_files()
    
    print("\n" + "="*50)
    print("✓ Build complete!")
    print(f"  Output directory: {DIST_DIR.absolute()}")
    print(f"  Total HTML files: {len(journals) + len(pages) + 1}")
    print("="*50)

if __name__ == '__main__':
    build()
