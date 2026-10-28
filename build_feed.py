#!/usr/bin/env python3
"""Build RSS feeds from the JSON item lists in data/.

Usage: python3 build_feed.py            # builds every feed defined in FEEDS
Items older than KEEP_DAYS (by their "added" time) are pruned from the JSON too.
"""
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
        "title": "Kiki · Design Daily",
        "description": "Daily picks from UX, visual design and creative industries, summarised in English with key terms.",
        "language": "en",
        "terms_label": "Key terms",
    },
}


def parse_time(item):
    """Publication time: the article date when known, else when it was added."""
    if item.get("date"):
        return datetime.strptime(item["date"], "%Y-%m-%d").replace(hour=8, tzinfo=timezone.utc)
    return datetime.fromisoformat(item["added"].replace("Z", "+00:00"))


def build(name, cfg):
    data_path = ROOT / "data" / f"{name}.json"
    items = json.loads(data_path.read_text(encoding="utf-8"))
    cutoff = datetime.now(timezone.utc) - timedelta(days=KEEP_DAYS)
    items = [i for i in items if datetime.fromisoformat(i["added"].replace("Z", "+00:00")) >= cutoff]
    seen, unique = set(), []
    for i in items:
        if i["link"] not in seen:
            seen.add(i["link"])
            unique.append(i)
    unique.sort(key=lambda i: (parse_time(i), i["added"]), reverse=True)
    unique = unique[:MAX_ITEMS]
    data_path.write_text(json.dumps(unique, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    now = format_datetime(datetime.now(timezone.utc))
    out = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">',
        "<channel>",
        f"<title>{escape(cfg['title'])}</title>",
        f"<link>{SITE}/</link>",
        f'<atom:link href="{SITE}/{name}.xml" rel="self" type="application/rss+xml"/>',
        f"<description>{escape(cfg['description'])}</description>",
        f"<language>{cfg['language']}</language>",
        f"<lastBuildDate>{now}</lastBuildDate>",
        "<ttl>180</ttl>",
    ]
    for i in unique:
        desc = i["summary"]
        if i.get("terms"):
            terms = "; ".join(f"{t[0]} — {t[1]}" for t in i["terms"])
            desc += f"\n\n{cfg['terms_label']}: {terms}"
        desc += f"\n\nSource: {i['source']}"
        out += [
            "<item>",
            f"<title>{escape(i['title'])}</title>",
            f"<link>{escape(i['link'])}</link>",
            f'<guid isPermaLink="true">{escape(i["link"])}</guid>',
            f"<pubDate>{format_datetime(parse_time(i))}</pubDate>",
            f"<category>{escape(i['source'])}</category>",
            f"<description>{escape(desc)}</description>",
            "</item>",
        ]
    out += ["</channel>", "</rss>", ""]
    (ROOT / f"{name}.xml").write_text("\n".join(out), encoding="utf-8")
    return len(unique)


if __name__ == "__main__":
    for name, cfg in FEEDS.items():
        print(f"{name}.xml: {build(name, cfg)} items")
