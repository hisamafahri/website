#!/usr/bin/env python3
"""
Build script for Hisam's Journal
Generates static output in dist/ directory ready to serve
"""

import os
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
        'index.html',
        'blog.js'
    ]
    
    for filename in static_files:
        src = Path(filename)
        if src.exists():
            dst = DIST_DIR / filename
            shutil.copy2(src, dst)
            print(f"  Copied: {filename}")
        else:
            print(f"  Warning: {filename} not found, skipping")

def update_blog_js(journals):
    """Update blog.js with auto-generated journal list"""
    blog_js_path = Path('blog.js')
    
    if not blog_js_path.exists():
        print("  Warning: blog.js not found, skipping auto-generation")
        return
    
    with open(blog_js_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Generate the journal files list
    journal_files = [f"'{j['filename']}.md'" for j in journals]
    journal_list = ',\n            '.join([f"'journals/{j['filename']}.md'" for j in journals])
    
    # Replace the hardcoded list in loadPosts()
    pattern = r"const contentFiles = \[([\s\S]*?)\];"
    replacement = f"const contentFiles = [\n            {journal_list}\n        ];"
    
    updated_content = re.sub(pattern, replacement, content)
    
    # Write to dist/blog.js
    with open(DIST_DIR / 'blog.js', 'w', encoding='utf-8') as f:
        f.write(updated_content)
    
    print(f"  Updated: blog.js with {len(journals)} journal entries")

def build():
    """Main build function"""
    print(f"Building {SITE_NAME}...")
    print()
    
    # Clean dist directory
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    print(f"✓ Cleaned dist/ directory")
    
    # Copy content directory
    shutil.copytree(CONTENT_DIR, DIST_DIR / 'content', dirs_exist_ok=True)
    print(f"✓ Copied content/ directory")
    
    # Get all content
    print("\nLoading content...")
    journals = get_all_journals()
    pages = get_all_pages()
    print(f"  Found {len(journals)} journals")
    print(f"  Found {len(pages)} pages")
    
    # Generate RSS
    print("\nGenerating RSS feed...")
    rss_content = generate_rss(journals)
    with open(DIST_DIR / 'rss.xml', 'w', encoding='utf-8') as f:
        f.write(rss_content)
    print("  ✓ Generated rss.xml")
    
    # Generate sitemap
    print("\nGenerating sitemap...")
    sitemap_content = generate_sitemap(journals, pages)
    with open(DIST_DIR / 'sitemap.xml', 'w', encoding='utf-8') as f:
        f.write(sitemap_content)
    print("  ✓ Generated sitemap.xml")
    
    # Copy static files
    print("\nCopying static files...")
    copy_static_files()
    
    # Update blog.js with auto-generated journal list
    print("\nUpdating blog.js...")
    update_blog_js(journals)
    
    print("\n" + "="*50)
    print("✓ Build complete!")
    print(f"  Output directory: {DIST_DIR.absolute()}")
    print("="*50)

if __name__ == '__main__':
    build()
