# Feeds

Personal RSS feeds, rebuilt every morning.

- Design (English): https://chiki03.github.io/Feeds/design.xml
- Le point du jour (français) : https://chiki03.github.io/Feeds/actu.xml — one daily digest per item, each linking to a page in `actu/`.

Data lives in `data/*.json`; `python3 build_feed.py` regenerates the XML and pages and prunes entries older than 21 days.
