#!/usr/bin/env python3
"""
Build script for Hisam's Journal
Generates static HTML pages, RSS feed, and sitemap
"""

import json
import os
import re
import shutil
from datetime import datetime
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom
from html import escape as html_escape

# Configuration
SITE_URL = "https://hisam.dev"
SITE_TITLE = "Hisam's Journal"
SITE_DESCRIPTION = "Personal blog and writing"
AUTHOR = "Hisam"
BUILD_DIR = Path(__file__).parent / "dist"

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
        
        .article-container {{
            display: grid;
            gap: 40px;
            position: relative;
        }}
        
        .article-content {{
            max-width: 650px;
        }}
        
        .footnotes-sidebar {{
            display: none;
            position: relative;
        }}
        
        .footnote-ref sup a {{
            text-decoration: none;
        }}
        
        @media (min-width: 1024px) {{
            nav .nav-container {{
                max-width: 1000px;
            }}
            
            #app {{
                max-width: 1000px;
            }}
            
            .article-container {{
                grid-template-columns: 650px 250px;
            }}
            
            .footnotes-sidebar {{
                display: block;
                font-size: 14px;
                line-height: 1.4;
                color: #666;
            }}
            
            .footnote-item {{
                margin-bottom: 20px;
                position: absolute;
                width: 250px;
            }}
            
            .footnote-item a {{
                color: #00e;
            }}
        }}
        
        @media (max-width: 1023px) {{
            .footnotes-sidebar {{
                display: block;
                margin-top: 40px;
                padding-top: 20px;
                border-top: 1px solid #ccc;
                font-size: 14px;
            }}
            
            .footnote-item {{
                margin-bottom: 15px;
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
    <div id="app">{content}</div>
    <script src="/prism.js"></script>
    <script>
        // Auto-highlight code
        if (typeof Prism !== 'undefined') {{
            Prism.highlightAll();
        }}
        
        // Align footnotes with their references on desktop
        if (window.innerWidth >= 1024) {{
            window.addEventListener('load', function() {{
                document.querySelectorAll('.footnote-item').forEach(function(note) {{
                    var id = note.id;
                    var num = id.replace('fn', '');
                    var ref = document.getElementById('fnref' + num);
                    
                    if (ref && note) {{
                        var refTop = ref.getBoundingClientRect().top + window.scrollY;
                        var containerTop = document.querySelector('.article-container').getBoundingClientRect().top + window.scrollY;
                        note.style.position = 'absolute';
                        note.style.top = (refTop - containerTop) + 'px';
                    }}
                }});
            }});
        }}
    </script>
</body>
</html>
"""


def slugify(text):
    """Convert text to URL-friendly slug"""
    return re.sub(r"^-+|-+$", "", re.sub(r"[^a-z0-9]+", "-", text.lower()))


def parse_frontmatter(content):
    """Parse custom +++ frontmatter from markdown content"""
    meta = {}
    lines = content.split("\n")

    if lines[0].strip() == "+++":
        for i in range(1, len(lines)):
            if lines[i].strip() == "+++":
                break
            match = re.match(r'^(\w+)\s*=\s*"(.+)"$', lines[i])
            if match:
                meta[match.group(1)] = match.group(2)

    return meta


def extract_description(content):
    """Extract first paragraph as description"""
    lines = content.split("\n")
    in_frontmatter = False

    for line in lines:
        if line.strip() == "+++":
            in_frontmatter = not in_frontmatter
            continue

        if in_frontmatter:
            continue

        # Skip empty lines and headers
        if line.strip() and not line.startswith("#"):
            # Clean markdown formatting
            text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", line)
            text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
            text = re.sub(r"\*([^*]+)\*", r"\1", text)
            text = re.sub(r"`([^`]+)`", r"\1", text)
            return text[:200]

    return ""


def parse_date(date_str, filename):
    """Parse date from frontmatter or filename"""
    month_map = {
        "Jan": 1,
        "Feb": 2,
        "Mar": 3,
        "Apr": 4,
        "May": 5,
        "Jun": 6,
        "Jul": 7,
        "Aug": 8,
        "Sep": 9,
        "Oct": 10,
        "Nov": 11,
        "Dec": 12,
    }

    # Try to parse "DD Mon YYYY" format
    match = re.match(r"(\d+)\s+(\w+)\s+(\d+)", date_str)
    if match:
        day = int(match.group(1))
        month = month_map.get(match.group(2), 1)
        year = int(match.group(3))
        return datetime(year, month, day)

    # Fallback: extract from YYYY-MM-DD filename
    file_match = re.search(r"(\d{4})-(\d{2})-(\d{2})", filename)
    if file_match:
        return datetime(
            int(file_match.group(1)), int(file_match.group(2)), int(file_match.group(3))
        )

    return datetime.now()


def render_table(rows):
    """Render table rows to HTML"""
    if not rows:
        return ""

    html = "<table>\n<tr>"
    for cell in rows[0]:
        html += f"<th>{cell}</th>"
    html += "</tr>\n"

    for row in rows[1:]:
        html += "<tr>"
        for cell in row:
            html += f"<td>{cell}</td>"
        html += "</tr>\n"

    html += "</table>"
    return html


def markdown_to_html(markdown):
    """Convert markdown to HTML"""
    # Extract footnote definitions
    footnotes = {}

    def extract_footnote(match):
        footnotes[match.group(1)] = match.group(2).strip()
        return ""

    html = re.sub(
        r"^\[\^(\d+)\]:\s*(.+)$", extract_footnote, markdown, flags=re.MULTILINE
    )

    # Protect code blocks
    code_blocks = []

    def protect_code(match):
        lang = match.group(1) or ""
        code = match.group(2)
        placeholder = f"<!--CODEBLOCK{len(code_blocks)}-->"
        lang_class = f' class="language-{lang}"' if lang else ""
        code_blocks.append(
            f"<pre><code{lang_class}>{html_escape(code.strip())}</code></pre>"
        )
        return placeholder

    html = re.sub(r"```(\w*)\n([\s\S]*?)```", protect_code, html)

    # Process tables
    lines = html.split("\n")
    result = []
    in_table = False
    table_rows = []

    for line in lines:
        if "<!--CODEBLOCK" in line:
            if in_table:
                result.append(render_table(table_rows))
                table_rows = []
                in_table = False
            result.append(line)
            continue

        if re.match(r"^\|(.+)\|$", line.strip()):
            if re.match(r"^\|[\s:-]+\|$", line):
                continue
            if not in_table:
                in_table = True
                table_rows = []
            cells = [c.strip() for c in line.split("|")[1:-1]]
            table_rows.append(cells)
        else:
            if in_table:
                result.append(render_table(table_rows))
                table_rows = []
                in_table = False
            result.append(line)

    if in_table:
        result.append(render_table(table_rows))

    html = "\n".join(result)

    # Process blockquotes
    lines = html.split("\n")
    result = []
    in_blockquote = False
    blockquote_content = []

    for line in lines:
        if line.strip().startswith("> "):
            if not in_blockquote:
                in_blockquote = True
                blockquote_content = []
            blockquote_content.append(line.strip()[2:])
        elif line.strip() == ">":
            if not in_blockquote:
                in_blockquote = True
                blockquote_content = []
            blockquote_content.append("")
        else:
            if in_blockquote:
                result.append(
                    f'<blockquote>{"<br>".join(blockquote_content)}</blockquote>'
                )
                blockquote_content = []
                in_blockquote = False
            result.append(line)

    if in_blockquote:
        result.append(f'<blockquote>{"<br>".join(blockquote_content)}</blockquote>')

    html = "\n".join(result)

    # Process lists
    lines = html.split("\n")
    result = []
    in_ul = False
    in_ol = False

    for line in lines:
        trimmed = line.strip()
        ul_match = re.match(r"^[-*]\s+(.+)$", trimmed)
        ol_match = re.match(r"^(\d+)\.\s+(.+)$", trimmed)

        if ul_match:
            if in_ol:
                result.append("</ol>")
                in_ol = False
            if not in_ul:
                result.append("<ul>")
                in_ul = True
            result.append(f"<li>{ul_match.group(1)}</li>")
        elif ol_match:
            if in_ul:
                result.append("</ul>")
                in_ul = False
            if not in_ol:
                result.append("<ol>")
                in_ol = True
            result.append(f"<li>{ol_match.group(2)}</li>")
        else:
            if in_ul:
                result.append("</ul>")
                in_ul = False
            if in_ol:
                result.append("</ol>")
                in_ol = False
            result.append(line)

    if in_ul:
        result.append("</ul>")
    if in_ol:
        result.append("</ol>")

    html = "\n".join(result)

    # Horizontal rules
    html = re.sub(r"^---+$", "<hr>", html, flags=re.MULTILINE)
    html = re.sub(r"^\*\*\*+$", "<hr>", html, flags=re.MULTILINE)
    html = re.sub(r"^___+$", "<hr>", html, flags=re.MULTILINE)

    # Headers with anchor links
    def header_with_link(match):
        level = len(match.group(1))
        text = match.group(2)
        id_slug = slugify(text)
        return f'<h{level} id="{id_slug}">{text} <a href="#{id_slug}" class="header-link">#</a></h{level}>'

    html = re.sub(r"^(#{1,3})\s+(.+)$", header_with_link, html, flags=re.MULTILINE)

    # Images (before links)
    html = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", r'<img src="\2" alt="\1">', html)

    # Links
    html = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', html)

    # Bold
    html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html)

    # Italic
    html = re.sub(r"_([^_]+)_", r"<em>\1</em>", html)
    html = re.sub(r"(?<!\*)\*(?!\*)([^*]+)\*(?!\*)", r"<em>\1</em>", html)

    # Inline code
    html = re.sub(r"`([^`]+)`", r"<code>\1</code>", html)

    # Footnote references
    html = re.sub(
        r"\[\^(\d+)\]",
        lambda m: f'<span class="footnote-ref"><sup><a href="#fn{m.group(1)}" id="fnref{m.group(1)}">{m.group(1)}</a></sup></span>',
        html,
    )

    # Paragraphs
    lines = html.split("\n")
    result = []
    in_paragraph = False

    for line in lines:
        trimmed = line.strip()

        if not trimmed:
            if in_paragraph:
                result.append("</p>")
                in_paragraph = False
            continue

        if (
            trimmed.startswith("<h")
            or trimmed.startswith("<blockquote>")
            or trimmed.startswith("<pre>")
            or trimmed.startswith("<table>")
            or trimmed.startswith("<img")
            or "<!--CODEBLOCK" in trimmed
            or trimmed.startswith("<ul>")
            or trimmed.startswith("</ul>")
            or trimmed.startswith("<ol>")
            or trimmed.startswith("</ol>")
            or trimmed.startswith("<li>")
            or trimmed == "<hr>"
        ):
            if in_paragraph:
                result.append("</p>")
                in_paragraph = False
            result.append(trimmed)
        else:
            if not in_paragraph:
                result.append("<p>")
                in_paragraph = True
            result.append(trimmed + " ")

    if in_paragraph:
        result.append("</p>")

    html = "\n".join(result)

    # Restore code blocks
    for i, block in enumerate(code_blocks):
        html = html.replace(f"<!--CODEBLOCK{i}-->", block)

    # Process footnote content
    processed_footnotes = {}
    for num, content in footnotes.items():
        processed = content
        processed = re.sub(
            r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', processed
        )
        processed = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", processed)
        processed = re.sub(r"\*(.+?)\*", r"<em>\1</em>", processed)
        processed = re.sub(r"`([^`]+)`", r"<code>\1</code>", processed)
        processed_footnotes[num] = processed

    return html, processed_footnotes


def render_footnotes_sidebar(footnotes):
    """Render footnotes sidebar HTML"""
    if not footnotes:
        return ""

    items = sorted(footnotes.items(), key=lambda x: int(x[0]))
    html = '<div class="footnotes-sidebar">'
    for num, content in items:
        html += (
            f'<div class="footnote-item" id="fn{num}"><sup>{num}</sup> {content}</div>'
        )
    html += "</div>"
    return html


def generate_static_site():
    """Generate static HTML files for all pages and posts"""
    content_dir = Path(__file__).parent / "content"

    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
    BUILD_DIR.mkdir(exist_ok=True)

    # Copy static assets to build directory
    root_dir = Path(__file__).parent
    prism_js = root_dir / "prism.js"
    prism_css = root_dir / "prism.css"
    favicon = root_dir / "favicon.ico"
    pgp = root_dir / "pgp.txt"

    if prism_js.exists():
        shutil.copy(prism_js, BUILD_DIR / "prism.js")
    if prism_css.exists():
        shutil.copy(prism_css, BUILD_DIR / "prism.css")
    if favicon.exists():
        shutil.copy(favicon, BUILD_DIR / "favicon.ico")
    if pgp.exists():
        shutil.copy(pgp, BUILD_DIR / "pgp.txt")

    # Parse all journal entries
    posts = []
    journals_dir = content_dir / "journals"

    if journals_dir.exists():
        for md_file in sorted(journals_dir.glob("*.md"), reverse=True):
            with open(md_file, "r", encoding="utf-8") as f:
                content = f.read()

            meta = parse_frontmatter(content)

            if not meta.get("title"):
                continue

            # Extract content (skip frontmatter)
            lines = content.split("\n")
            content_start = 0
            if lines[0] == "+++":
                for i in range(1, len(lines)):
                    if lines[i] == "+++":
                        content_start = i + 1
                        break
            markdown_content = "\n".join(lines[content_start:]).strip()

            # Convert to HTML
            html_content, footnotes = markdown_to_html(markdown_content)

            # Generate slug
            date_slug = md_file.stem
            title_slug = slugify(meta["title"])
            slug = f"{date_slug}/{title_slug}"

            # Parse date
            date_obj = parse_date(meta.get("date", ""), md_file.name)
            description = meta.get("description") or extract_description(content)

            posts.append(
                {
                    "title": meta["title"],
                    "description": description,
                    "date": meta.get("date", ""),
                    "date_obj": date_obj,
                    "slug": slug,
                    "html": html_content,
                    "footnotes": footnotes,
                }
            )

    # Generate individual post pages
    journals_out_dir = BUILD_DIR / "journals"
    for post in posts:
        # Create directory for post
        post_dir = journals_out_dir / post["slug"]
        post_dir.mkdir(parents=True, exist_ok=True)

        # Build footnotes sidebar
        footnotes_html = render_footnotes_sidebar(post["footnotes"])

        # Build post content
        post_content = f"""
<div class="article-container">
    <div class="article-content">
        <a href="/">← Back</a>
        <br><br>
        <b>{post['title']}</b>
        <br>
        {post['date']}
        <br><br>
        {post['html']}
    </div>
    {footnotes_html}
</div>
"""

        # Write HTML file
        html = HTML_TEMPLATE.format(
            title=f"{post['title']} - {SITE_TITLE}",
            description=post["description"],
            canonical_url=f"{SITE_URL}/journals/{post['slug']}",
            content=post_content,
        )

        with open(post_dir / "index.html", "w", encoding="utf-8") as f:
            f.write(html)

    # Generate static pages (about, now, uses, etc.)
    for md_file in content_dir.glob("*.md"):
        page_name = md_file.stem

        with open(md_file, "r", encoding="utf-8") as f:
            content = f.read()

        meta = parse_frontmatter(content)

        # Extract content (skip frontmatter)
        lines = content.split("\n")
        content_start = 0
        if lines[0] == "+++":
            for i in range(1, len(lines)):
                if lines[i] == "+++":
                    content_start = i + 1
                    break
        markdown_content = "\n".join(lines[content_start:]).strip()

        # Convert to HTML
        html_content, footnotes = markdown_to_html(markdown_content)

        # Build footnotes sidebar
        footnotes_html = render_footnotes_sidebar(footnotes)

        # Build page content
        page_content = f"""
<div class="article-container">
    <div class="article-content">
        {html_content}
    </div>
    {footnotes_html}
</div>
"""

        title = meta.get("title", page_name.capitalize())
        description = meta.get("description") or extract_description(content)

        # Write HTML file directly (not in a directory)
        # This allows /about to be served as /about.html instead of /about/index.html
        html = HTML_TEMPLATE.format(
            title=f"{title} - {SITE_TITLE}",
            description=description,
            canonical_url=f"{SITE_URL}/{page_name}",
            content=page_content,
        )

        with open(BUILD_DIR / f"{page_name}.html", "w", encoding="utf-8") as f:
            f.write(html)

    # Generate home page (index.html)
    home_content = "\n".join(
        [
            f'<a href="/journals/{post["slug"]}">{post["title"]}</a><br>'
            for post in posts
        ]
    )

    html = HTML_TEMPLATE.format(
        title=SITE_TITLE,
        description=SITE_DESCRIPTION,
        canonical_url=SITE_URL,
        content=home_content,
    )

    with open(BUILD_DIR / "index.html", "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✓ Generated static site in {BUILD_DIR}")
    print(f"  Total posts: {len(posts)}")
    print(f"  Total pages: {len(list(content_dir.glob('*.md')))}")


def generate_pages_manifest():
    """Generate a JSON manifest of all markdown pages in content directory"""
    content_dir = Path(__file__).parent / "content"

    if not content_dir.exists():
        print(f"Error: {content_dir} does not exist")
        return

    # Find all .md files in content directory (excluding subdirectories)
    page_files = []
    for md_file in content_dir.glob("*.md"):
        page_files.append(md_file.name)

    # Sort alphabetically
    page_files.sort()

    # Write manifest
    manifest_file = content_dir / "pages.json"
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(page_files, f, indent=2)

    print(f"✓ Generated pages manifest: {manifest_file}")
    print(f"  Pages found: {', '.join(page_files)}")


def generate_rss():
    """Generate RSS feed from journal entries"""
    content_dir = Path(__file__).parent / "content" / "journals"

    if not content_dir.exists():
        print(f"Error: {content_dir} does not exist")
        return

    # Parse all journal entries
    posts = []

    for md_file in sorted(content_dir.glob("*.md"), reverse=True):
        with open(md_file, "r", encoding="utf-8") as f:
            content = f.read()

        meta = parse_frontmatter(content)

        if not meta.get("title"):
            continue

        # Generate slug
        date_slug = md_file.stem  # e.g., "2023-01-29"
        title_slug = slugify(meta["title"])
        slug = f"{date_slug}/{title_slug}"

        # Parse date
        date_obj = parse_date(meta.get("date", ""), md_file.name)

        description = meta.get("description") or extract_description(content)

        posts.append(
            {
                "title": meta["title"],
                "description": description,
                "link": f"{SITE_URL}/journals/{slug}",
                "date": date_obj,
                "guid": f"{SITE_URL}/journals/{slug}",
            }
        )

    # Create RSS feed
    rss = Element(
        "rss", version="2.0", attrib={"xmlns:atom": "http://www.w3.org/2005/Atom"}
    )

    channel = SubElement(rss, "channel")

    SubElement(channel, "title").text = SITE_TITLE
    SubElement(channel, "link").text = SITE_URL
    SubElement(channel, "description").text = SITE_DESCRIPTION
    SubElement(channel, "language").text = "en-us"

    # Add atom:link for self-reference
    SubElement(
        channel,
        "{http://www.w3.org/2005/Atom}link",
        attrib={
            "href": f"{SITE_URL}/rss.xml",
            "rel": "self",
            "type": "application/rss+xml",
        },
    )

    # Add posts
    for post in posts[:20]:  # Limit to 20 most recent posts
        item = SubElement(channel, "item")
        SubElement(item, "title").text = post["title"]
        SubElement(item, "link").text = post["link"]
        SubElement(item, "description").text = post["description"]
        SubElement(item, "guid", isPermaLink="true").text = post["guid"]
        SubElement(item, "pubDate").text = post["date"].strftime(
            "%a, %d %b %Y %H:%M:%S +0000"
        )

    # Pretty print XML
    xml_str = minidom.parseString(tostring(rss, encoding="utf-8")).toprettyxml(
        indent="  "
    )

    # Remove extra blank lines
    xml_lines = [line for line in xml_str.split("\n") if line.strip()]
    xml_str = "\n".join(xml_lines)

    # Write to file
    output_file = BUILD_DIR / "rss.xml"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(xml_str)

    print(f"✓ Generated RSS feed: {output_file}")
    print(f"  Total posts: {len(posts)}")


def generate_sitemap():
    """Generate sitemap.xml from content directory"""
    content_dir = Path(__file__).parent / "content"

    if not content_dir.exists():
        print(f"Error: {content_dir} does not exist")
        return

    urls = []

    # Add homepage
    urls.append({"loc": f"{SITE_URL}/", "changefreq": "weekly", "priority": "1.0"})

    # Add static pages
    for md_file in content_dir.glob("*.md"):
        page_name = md_file.stem
        urls.append(
            {
                "loc": f"{SITE_URL}/{page_name}",
                "changefreq": "monthly",
                "priority": "0.7",
            }
        )

    # Add journal posts
    journals_dir = content_dir / "journals"
    if journals_dir.exists():
        for md_file in sorted(journals_dir.glob("*.md"), reverse=True):
            with open(md_file, "r", encoding="utf-8") as f:
                content = f.read()

            meta = parse_frontmatter(content)

            if not meta.get("title"):
                continue

            # Generate slug
            date_slug = md_file.stem  # e.g., "2023-01-29"
            title_slug = slugify(meta["title"])
            slug = f"{date_slug}/{title_slug}"

            # Get last modified date from filename
            date_match = re.search(r"(\d{4})-(\d{2})-(\d{2})", md_file.name)
            lastmod = (
                f"{date_match.group(1)}-{date_match.group(2)}-{date_match.group(3)}"
                if date_match
                else datetime.now().strftime("%Y-%m-%d")
            )

            urls.append(
                {
                    "loc": f"{SITE_URL}/journals/{slug}",
                    "lastmod": lastmod,
                    "changefreq": "monthly",
                    "priority": "0.8",
                }
            )

    # Generate XML
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'

    for url in urls:
        xml += "    <url>\n"
        xml += f'        <loc>{url["loc"]}</loc>\n'
        if "lastmod" in url:
            xml += f'        <lastmod>{url["lastmod"]}</lastmod>\n'
        xml += f'        <changefreq>{url["changefreq"]}</changefreq>\n'
        xml += f'        <priority>{url["priority"]}</priority>\n'
        xml += "    </url>\n"

    xml += "</urlset>\n"

    # Write to file
    output_file = BUILD_DIR / "sitemap.xml"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(xml)

    print(f"✓ Generated sitemap: {output_file}")
    print(f"  Total URLs: {len(urls)}")


def generate_redirects():
    """Generate _redirects file for Netlify to handle trailing slashes"""
    content_dir = Path(__file__).parent / "content"
    
    redirects = []
    
    # Redirect URLs with trailing slash to without trailing slash
    # Add redirects for static pages
    for md_file in content_dir.glob("*.md"):
        page_name = md_file.stem
        redirects.append(f"/{page_name}/  /{page_name}  301")
    
    # Add redirects for journal posts
    journals_dir = content_dir / "journals"
    if journals_dir.exists():
        for md_file in sorted(journals_dir.glob("*.md"), reverse=True):
            with open(md_file, "r", encoding="utf-8") as f:
                content = f.read()
            
            meta = parse_frontmatter(content)
            
            if not meta.get("title"):
                continue
            
            # Generate slug
            date_slug = md_file.stem
            title_slug = slugify(meta["title"])
            slug = f"{date_slug}/{title_slug}"
            
            # Redirect both the directory-style URL and flat-style URL with trailing slash
            redirects.append(f"/journals/{slug}/  /journals/{slug}  301")
    
    # Write _redirects file
    output_file = BUILD_DIR / "_redirects"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(redirects))
        f.write("\n")
    
    print(f"✓ Generated _redirects: {output_file}")
    print(f"  Total redirects: {len(redirects)}")



if __name__ == "__main__":
    print("Building Hisam's Journal...\n")
    generate_static_site()
    generate_rss()
    generate_sitemap()
    generate_redirects()
    print("\n✓ Build complete!")
