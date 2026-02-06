#!/usr/bin/env python3
"""
Build script for Hisam's Journal
Generates RSS feed, pages manifest, and sitemap
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom

# Configuration
SITE_URL = "https://hisam.dev"  # Update with your actual domain
SITE_TITLE = "Hisam's Journal"
SITE_DESCRIPTION = "Personal blog and writing"
AUTHOR = "Hisam"

def parse_frontmatter(content):
    """Parse custom +++ frontmatter from markdown content"""
    meta = {}
    lines = content.split('\n')
    
    if lines[0].strip() == '+++':
        for i in range(1, len(lines)):
            if lines[i].strip() == '+++':
                break
            match = re.match(r'^(\w+)\s*=\s*"(.+)"$', lines[i])
            if match:
                meta[match.group(1)] = match.group(2)
    
    return meta

def extract_description(content):
    """Extract first paragraph as description"""
    lines = content.split('\n')
    in_frontmatter = False
    
    for line in lines:
        if line.strip() == '+++':
            in_frontmatter = not in_frontmatter
            continue
        
        if in_frontmatter:
            continue
        
        # Skip empty lines and headers
        if line.strip() and not line.startswith('#'):
            # Clean markdown formatting
            text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', line)  # Remove links
            text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # Remove bold
            text = re.sub(r'\*([^*]+)\*', r'\1', text)  # Remove italic
            text = re.sub(r'`([^`]+)`', r'\1', text)  # Remove code
            return text[:200]
    
    return ""

def slugify(text):
    """Convert text to URL-friendly slug"""
    return re.sub(r'^-+|-+$', '', re.sub(r'[^a-z0-9]+', '-', text.lower()))

def parse_date(date_str, filename):
    """Parse date from frontmatter or filename"""
    month_map = {
        'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
        'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
    }
    
    # Try to parse "DD Mon YYYY" format
    match = re.match(r'(\d+)\s+(\w+)\s+(\d+)', date_str)
    if match:
        day = int(match.group(1))
        month = month_map.get(match.group(2), 1)
        year = int(match.group(3))
        return datetime(year, month, day)
    
    # Fallback: extract from YYYY-MM-DD filename
    file_match = re.search(r'(\d{4})-(\d{2})-(\d{2})', filename)
    if file_match:
        return datetime(int(file_match.group(1)), int(file_match.group(2)), int(file_match.group(3)))
    
    return datetime.now()

def generate_pages_manifest():
    """Generate a JSON manifest of all markdown pages in content directory"""
    content_dir = Path(__file__).parent / 'content'
    
    if not content_dir.exists():
        print(f"Error: {content_dir} does not exist")
        return
    
    # Find all .md files in content directory (excluding subdirectories)
    page_files = []
    for md_file in content_dir.glob('*.md'):
        page_files.append(md_file.name)
    
    # Sort alphabetically
    page_files.sort()
    
    # Write manifest
    manifest_file = content_dir / 'pages.json'
    with open(manifest_file, 'w', encoding='utf-8') as f:
        json.dump(page_files, f, indent=2)
    
    print(f"✓ Generated pages manifest: {manifest_file}")
    print(f"  Pages found: {', '.join(page_files)}")

def generate_rss():
    """Generate RSS feed from journal entries"""
    content_dir = Path(__file__).parent / 'content' / 'journals'
    
    if not content_dir.exists():
        print(f"Error: {content_dir} does not exist")
        return
    
    # Parse all journal entries
    posts = []
    
    for md_file in sorted(content_dir.glob('*.md'), reverse=True):
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        meta = parse_frontmatter(content)
        
        if not meta.get('title'):
            continue
        
        # Generate slug
        date_slug = md_file.stem  # e.g., "2023-01-29"
        title_slug = slugify(meta['title'])
        slug = f"{date_slug}/{title_slug}"
        
        # Parse date
        date_obj = parse_date(meta.get('date', ''), md_file.name)
        
        description = meta.get('description') or extract_description(content)
        
        posts.append({
            'title': meta['title'],
            'description': description,
            'link': f"{SITE_URL}/journals/{slug}",
            'date': date_obj,
            'guid': f"{SITE_URL}/journals/{slug}"
        })
    
    # Create RSS feed
    rss = Element('rss', version='2.0', attrib={
        'xmlns:atom': 'http://www.w3.org/2005/Atom'
    })
    
    channel = SubElement(rss, 'channel')
    
    SubElement(channel, 'title').text = SITE_TITLE
    SubElement(channel, 'link').text = SITE_URL
    SubElement(channel, 'description').text = SITE_DESCRIPTION
    SubElement(channel, 'language').text = 'en-us'
    
    # Add atom:link for self-reference
    SubElement(channel, '{http://www.w3.org/2005/Atom}link', attrib={
        'href': f'{SITE_URL}/rss.xml',
        'rel': 'self',
        'type': 'application/rss+xml'
    })
    
    # Add posts
    for post in posts[:20]:  # Limit to 20 most recent posts
        item = SubElement(channel, 'item')
        SubElement(item, 'title').text = post['title']
        SubElement(item, 'link').text = post['link']
        SubElement(item, 'description').text = post['description']
        SubElement(item, 'guid', isPermaLink='true').text = post['guid']
        SubElement(item, 'pubDate').text = post['date'].strftime('%a, %d %b %Y %H:%M:%S +0000')
    
    # Pretty print XML
    xml_str = minidom.parseString(tostring(rss, encoding='utf-8')).toprettyxml(indent='  ')
    
    # Remove extra blank lines
    xml_lines = [line for line in xml_str.split('\n') if line.strip()]
    xml_str = '\n'.join(xml_lines)
    
    # Write to file
    output_file = Path(__file__).parent / 'rss.xml'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(xml_str)
    
    print(f"✓ Generated RSS feed: {output_file}")
    print(f"  Total posts: {len(posts)}")

def generate_sitemap():
    """Generate sitemap.xml from content directory"""
    content_dir = Path(__file__).parent / 'content'
    
    if not content_dir.exists():
        print(f"Error: {content_dir} does not exist")
        return
    
    urls = []
    
    # Add homepage
    urls.append({
        'loc': f'{SITE_URL}/',
        'changefreq': 'weekly',
        'priority': '1.0'
    })
    
    # Add static pages
    for md_file in content_dir.glob('*.md'):
        page_name = md_file.stem
        urls.append({
            'loc': f'{SITE_URL}/{page_name}',
            'changefreq': 'monthly',
            'priority': '0.7'
        })
    
    # Add journal posts
    journals_dir = content_dir / 'journals'
    if journals_dir.exists():
        for md_file in sorted(journals_dir.glob('*.md'), reverse=True):
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            meta = parse_frontmatter(content)
            
            if not meta.get('title'):
                continue
            
            # Generate slug
            date_slug = md_file.stem  # e.g., "2023-01-29"
            title_slug = slugify(meta['title'])
            slug = f"{date_slug}/{title_slug}"
            
            # Get last modified date from filename
            date_match = re.search(r'(\d{4})-(\d{2})-(\d{2})', md_file.name)
            lastmod = f"{date_match.group(1)}-{date_match.group(2)}-{date_match.group(3)}" if date_match else datetime.now().strftime('%Y-%m-%d')
            
            urls.append({
                'loc': f'{SITE_URL}/journals/{slug}',
                'lastmod': lastmod,
                'changefreq': 'monthly',
                'priority': '0.8'
            })
    
    # Generate XML
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    
    for url in urls:
        xml += '    <url>\n'
        xml += f'        <loc>{url["loc"]}</loc>\n'
        if 'lastmod' in url:
            xml += f'        <lastmod>{url["lastmod"]}</lastmod>\n'
        xml += f'        <changefreq>{url["changefreq"]}</changefreq>\n'
        xml += f'        <priority>{url["priority"]}</priority>\n'
        xml += '    </url>\n'
    
    xml += '</urlset>\n'
    
    # Write to file
    output_file = Path(__file__).parent / 'sitemap.xml'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(xml)
    
    print(f"✓ Generated sitemap: {output_file}")
    print(f"  Total URLs: {len(urls)}")

if __name__ == '__main__':
    print("Building Hisam's Journal...\n")
    generate_pages_manifest()
    generate_rss()
    generate_sitemap()
    print("\n✓ Build complete!")
