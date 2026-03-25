import os
import yaml
import logging
from datetime import date
from dotenv import load_dotenv

from src.collectors.dart import DartCollector
from src.collectors.news import NewsCollector
from src.filters.keyword import KeywordFilter
from src.analyzers.claude import ClaudeAnalyzer
from src.outputs.deal_card import DealCardWriter

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def deduplicate(dart_items: list[dict], news_items: list[dict]) -> list[dict]:
    """동일 회사명(exact match) DART+뉴스 항목을 병합"""
    merged = {item["company"]: item.copy() for item in dart_items}
    for news in news_items:
        company = news["company"]
        if company in merged:
            existing = merged[company]
            existing["news_url"] = news["news_url"]
            existing["news_content"] = news["news_content"]
            existing["sources"] = list(set(existing["sources"] + ["news"]))
            existing["content"] = f"{existing.get('content','')} {news.get('content','')}".strip()
        else:
            merged[company] = news.copy()
    return list(merged.values())


def run():
    load_dotenv()
    with open("config.yaml", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    dart_key = os.environ["DART_API_KEY"]
    claude_key = os.environ["ANTHROPIC_API_KEY"]
    today = date.today().isoformat()

    logger.info("=== VC Sourcing Pipeline Start ===")

    dart_items = DartCollector(config, api_key=dart_key).collect()
    logger.info(f"DART: {len(dart_items)} items collected")

    news_items = NewsCollector(config).collect()
    logger.info(f"News: {len(news_items)} items collected")

    all_items = deduplicate(dart_items, news_items)
    logger.info(f"After dedup: {len(all_items)} items")

    filtered = KeywordFilter(config).filter(all_items)
    logger.info(f"After keyword filter: {len(filtered)} items")

    analyzed = ClaudeAnalyzer(config, api_key=claude_key).analyze_batch(filtered)
    logger.info(f"Claude analyzed: {len(analyzed)} items")

    writer = DealCardWriter(config)
    for item in analyzed:
        writer.write(item, date_str=today)

    hot = [i for i in analyzed if i.get("signal_score", 0) >= config["alerts"]["hot_score_threshold"]]
    logger.info(f"Hot deals: {len(hot)}")
    logger.info("=== Pipeline Complete ===")


if __name__ == "__main__":
    run()
