import feedparser
import re
import logging
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)

class NewsCollector:
    def __init__(self, config: dict):
        self.config = config["news"]

    def collect(self) -> list[dict]:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=self.config["lookback_hours"])
        results = []
        for source in self.config["sources"]:
            items = self._fetch_source(source, cutoff)
            results.extend(items)
        return results

    def _fetch_source(self, source: dict, cutoff: datetime) -> list[dict]:
        try:
            feed = feedparser.parse(source["url"])
            results = []
            for entry in feed.entries:
                published = self._parse_date(entry)
                if published and published < cutoff:
                    continue
                company = self._extract_company(entry.title)
                content = f"{entry.title} {getattr(entry, 'summary', '')}"[:500]
                results.append({
                    "company": company,
                    "news_url": getattr(entry, "link", ""),
                    "news_content": content,
                    "dart_url": None,
                    "dart_content": None,
                    "content": content,
                    "sources": ["news"],
                    "source_name": source["name"],
                })
            return results
        except Exception as e:
            logger.warning(f"RSS fetch failed for {source['name']}: {e}")
            return []

    def _extract_company(self, title: str) -> str:
        match = re.match(r"^([^\s,·…]+)", title.strip())
        return match.group(1) if match else title.split()[0] if title.split() else ""

    def _parse_date(self, entry) -> datetime | None:
        try:
            t = entry.published_parsed
            return datetime(*t[:6], tzinfo=timezone.utc)
        except Exception:
            return None
