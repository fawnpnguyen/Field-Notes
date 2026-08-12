#!/usr/bin/env python3
"""
Build script for the private journal.
Reads markdown files in entries/, writes a static site to site/.
Run: python3 build_journal.py
Then open site/index.html in your browser.
"""
import shutil
from pathlib import Path
from datetime import datetime
import markdown
import frontmatter

ROOT = Path(__file__).parent
ENTRIES = ROOT / "entries"
IMAGES = ROOT / "images"
SITE = ROOT / "site"

PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} · Field Notes</title>
<link rel="stylesheet" href="style.css">
</head>
<body>
<div class="notebook">
  <aside class="spine">
    <div class="spine-title">Field&nbsp;Notes</div>
    <nav class="tabs">
      {nav_tabs}
    </nav>
  </aside>
  <main class="pages">
    {pages}
  </main>
</div>
</body>
</html>
"""

ENTRY_TEMPLATE = """
    <article class="page" id="{slug}">
      <div class="stamp">
        <span class="stamp-date">{date_display}</span>
        {tags_html}
      </div>
      <h1>{title}</h1>
      <div class="prose">
        {body}
      </div>
    </article>
"""

def month_grouping(entries):
    groups = {}
    for e in entries:
        key = e["date"].strftime("%B %Y")
        groups.setdefault(key, []).append(e)
    return groups

def build():
    if SITE.exists():
        shutil.rmtree(SITE)
    SITE.mkdir()
    (SITE / "images").mkdir()
    if IMAGES.exists():
        shutil.copytree(IMAGES, SITE / "images", dirs_exist_ok=True)
    shutil.copy(ROOT / "style.css", SITE / "style.css")

    entries = []
    for f in sorted(ENTRIES.glob("*.md")):
        post = frontmatter.load(f)
        date = post.get("date")
        if isinstance(date, str):
            date = datetime.strptime(date, "%Y-%m-%d").date()
        elif date is None:
            date = datetime.strptime(f.stem, "%Y-%m-%d").date()
        slug = f.stem
        fixed_content = post.content.replace("../images/", "images/")
        html_body = markdown.markdown(fixed_content, extensions=["extra"])
        tags = post.get("tags", [])
        title = post.get("title") or date.strftime("%B %-d, %Y")
        entries.append({
            "slug": slug,
            "title": title,
            "date": date,
            "tags": tags,
            "body": html_body,
        })

    entries.sort(key=lambda e: e["date"], reverse=True)

    nav_tabs = []
    pages_html = []
    groups = month_grouping(entries)
    for month, group_entries in groups.items():
        nav_tabs.append(f'<div class="tab-month">{month}</div>')
        for e in group_entries:
            nav_tabs.append(
                f'<a class="tab-entry" href="#{e["slug"]}">'
                f'<span class="tab-day">{e["date"].strftime("%d")}</span>'
                f'<span class="tab-label">{e["title"]}</span></a>'
            )

    for e in entries:
        tags_html = "".join(f'<span class="tag">{t}</span>' for t in e["tags"])
        pages_html.append(ENTRY_TEMPLATE.format(
            slug=e["slug"],
            date_display=e["date"].strftime("%b %d, %Y"),
            tags_html=tags_html,
            title=e["title"],
            body=e["body"],
        ))

    html = PAGE_TEMPLATE.format(
        title="Field Notes",
        nav_tabs="\n      ".join(nav_tabs),
        pages="\n".join(pages_html),
    )
    (SITE / "index.html").write_text(html, encoding="utf-8")
    print(f"Built {len(entries)} entries -> {SITE / 'index.html'}")

if __name__ == "__main__":
    build()
