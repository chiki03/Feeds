# Feeds

Personal RSS feeds, rebuilt every morning.

- Main feed: https://chiki03.github.io/Feeds/design.xml — the daily French digest at the top of each day, plus English design picks
- Le point du jour (français) : https://chiki03.github.io/Feeds/actu.xml — one daily digest per item, each linking to a page in `actu/`.

Data lives in `data/*.json`; `python3 build_feed.py` regenerates the XML and pages and prunes entries older than 21 days.
