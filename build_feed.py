#!/usr/bin/env python3
"""Build RSS feeds (and daily digest pages) from the JSON files in data/.

Usage: python3 build_feed.py

- design: data/design.json is a list of articles; one RSS item per article (English).
- actu:   data/actu.json is a list of daily digests; each digest becomes a page
          actu/YYYY-MM-DD.html and one RSS item linking to it (French).
Entries older than KEEP_DAYS (by their "added" time) are pruned from the JSON too.
"""
import html
import json
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).parent
SITE = "https://chiki03.github.io/Feeds"
KEEP_DAYS = 21
MAX_ITEMS = 60

FEEDS = {
    "design": {
        "kind": "articles",
        "title": "Kiki · Design Daily",
        "description": "Daily picks from UX, visual design and creative industries, summarised in English with key terms.",
        "language": "en",
        "terms_label": "Key terms",
        "source_label": "Source",
    },
    "actu": {
        "kind": "digest",
        "title": "Kiki · Le point du jour",
        "description": "Chaque matin, ce qui s'est passé en Europe, en France et en Suisse, politique et économie, avec les liens vers les articles.",
        "language": "fr",
        "terms_label": "Mots clés",
    },
}

MONTHS_FR = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet",
             "août", "septembre", "octobre", "novembre", "décembre"]


def ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def pub_time(item):
    if item.get("date"):
        return datetime.strptime(item["date"], "%Y-%m-%d").replace(hour=6, tzinfo=timezone.utc)
    return ts(item["added"])


def load(name):
    path = ROOT / "data" / f"{name}.json"
    items = json.loads(path.read_text(encoding="utf-8"))
    cutoff = datetime.now(timezone.utc) - timedelta(days=KEEP_DAYS)
    items = [i for i in items if ts(i["added"]) >= cutoff]
    seen, unique = set(), []
    for i in items:
        key = i.get("date") if name == "actu" else i["link"]
        if key not in seen:
            seen.add(key)
            unique.append(i)
    unique.sort(key=lambda i: (pub_time(i), i["added"]), reverse=True)
    unique = unique[:MAX_ITEMS]
    path.write_text(json.dumps(unique, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return unique


def channel_head(name, cfg):
    return [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">',
        "<channel>",
        f"<title>{escape(cfg['title'])}</title>",
        f"<link>{SITE}/</link>",
        f'<atom:link href="{SITE}/{name}.xml" rel="self" type="application/rss+xml"/>',
        f"<description>{escape(cfg['description'])}</description>",
        f"<language>{cfg['language']}</language>",
        f"<lastBuildDate>{format_datetime(datetime.now(timezone.utc))}</lastBuildDate>",
        "<ttl>180</ttl>",
    ]


def rss_item(title, link, when, description, category=None):
    out = ["<item>", f"<title>{escape(title)}</title>", f"<link>{escape(link)}</link>",
           f'<guid isPermaLink="true">{escape(link)}</guid>',
           f"<pubDate>{format_datetime(when)}</pubDate>"]
    if category:
        out.append(f"<category>{escape(category)}</category>")
    out += [f"<description>{escape(description)}</description>", "</item>"]
    return out


def build_articles(name, cfg):
    items = load(name)
    out = channel_head(name, cfg)
    for i in items:
        desc = i["summary"]
        if i.get("terms"):
            desc += f"\n\n{cfg['terms_label']}: " + "; ".join(f"{a} — {b}" for a, b in i["terms"])
        desc += f"\n\n{cfg['source_label']}: {i['source']}"
        out += rss_item(i["title"], i["link"], pub_time(i), desc, i["source"])
    out += ["</channel>", "</rss>", ""]
    (ROOT / f"{name}.xml").write_text("\n".join(out), encoding="utf-8")
    return len(items)


def fr_date(d):
    dt = datetime.strptime(d, "%Y-%m-%d")
    return f"{dt.day} {MONTHS_FR[dt.month - 1]} {dt.year}"


PAGE_CSS = """
:root{--bg:#f6f5f2;--fg:#22211e;--muted:#6a675f;--rule:#dcd9d1;--accent:#2f5d8a;color-scheme:light}
@media (prefers-color-scheme:dark){:root{--bg:#161719;--fg:#e9e7e2;--muted:#a19e96;--rule:#33353a;--accent:#8db7e0;color-scheme:dark}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:17px/1.6 Georgia,"Times New Roman",serif}
main{max-width:640px;margin:0 auto;padding:32px max(18px,env(safe-area-inset-right)) 48px max(18px,env(safe-area-inset-left))}
.date{font:600 12px/1 -apple-system,"Segoe UI",sans-serif;letter-spacing:.12em;text-transform:uppercase;color:var(--muted)}
h1{font-weight:normal;font-size:1.9rem;line-height:1.2;margin:.4em 0 .2em;text-wrap:balance}
.lede{color:var(--muted);margin:0 0 1.5em}
h2{font:600 13px/1 -apple-system,"Segoe UI",sans-serif;letter-spacing:.1em;text-transform:uppercase;color:var(--accent);margin:2em 0 .6em;padding-top:1em;border-top:1px solid var(--rule)}
ul{margin:0;padding-left:1.1em}
li{margin:.55em 0}
a{color:var(--fg);text-decoration-color:var(--accent);text-underline-offset:3px}
.src{font:14px -apple-system,"Segoe UI",sans-serif;color:var(--muted);white-space:nowrap}
dl{margin:0}
dt{font-style:italic;margin-top:.5em}
dd{margin:0 0 0 1em;color:var(--muted)}
.note{margin-top:2.5em;font:13px/1.5 -apple-system,"Segoe UI",sans-serif;color:var(--muted)}
"""


def digest_page(d, cfg):
    e = html.escape
    parts = [
        "<!doctype html>", '<html lang="fr">', "<head>", '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">',
        f"<title>{e(d['title'])}</title>", f"<style>{PAGE_CSS}</style>", "</head>", "<body>", "<main>",
        f'<div class="date">{e(fr_date(d["date"]))}</div>',
        f"<h1>{e(d['title'])}</h1>",
    ]
    if d.get("lede"):
        parts.append(f'<p class="lede">{e(d["lede"])}</p>')
    for sec in d["sections"]:
        parts.append(f"<h2>{e(sec['name'])}</h2><ul>")
        for p in sec["points"]:
            parts.append(f'<li>{e(p["text"])} <a class="src" href="{e(p["link"])}" target="_blank" rel="noopener">{e(p["source"])} →</a></li>')
        parts.append("</ul>")
    if d.get("terms"):
        parts.append(f"<h2>{e(cfg['terms_label'])}</h2><dl>")
        for a, b in d["terms"]:
            parts.append(f"<dt>{e(a)}</dt><dd>{e(b)}</dd>")
        parts.append("</dl>")
    parts.append('<p class="note">Synthèse rédigée chaque matin à partir des titres et des brèves des sources citées. Les détails et les nuances se trouvent dans les articles.</p>')
    parts += ["</main>", "</body>", "</html>", ""]
    return "\n".join(parts)


def digest_text(d, cfg):
    lines = [d["lede"]] if d.get("lede") else []
    for sec in d["sections"]:
        lines.append(f"\n{sec['name'].upper()}")
        for p in sec["points"]:
            lines.append(f"• {p['text']} ({p['source']}: {p['link']})")
    if d.get("terms"):
        lines.append(f"\n{cfg['terms_label']} : " + " ; ".join(f"{a} — {b}" for a, b in d["terms"]))
    return "\n".join(lines)


def build_digest(name, cfg):
    digests = load(name)
    (ROOT / name).mkdir(exist_ok=True)
    out = channel_head(name, cfg)
    for d in digests:
        page = f"{name}/{d['date']}.html"
        (ROOT / page).write_text(digest_page(d, cfg), encoding="utf-8")
        out += rss_item(d["title"], f"{SITE}/{page}", ts(d["added"]), digest_text(d, cfg))
    out += ["</channel>", "</rss>", ""]
    (ROOT / f"{name}.xml").write_text("\n".join(out), encoding="utf-8")
    return len(digests)


if __name__ == "__main__":
    for name, cfg in FEEDS.items():
        n = (build_digest if cfg["kind"] == "digest" else build_articles)(name, cfg)
        print(f"{name}.xml: {n} entries")
