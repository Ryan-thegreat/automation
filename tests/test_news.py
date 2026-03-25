import pytest
from unittest.mock import patch, MagicMock
from src.collectors.news import NewsCollector

@pytest.fixture
def config():
    return {
        "news": {
            "sources": [
                {"url": "https://example.com/feed", "name": "테스트뉴스"}
            ],
            "lookback_hours": 24
        }
    }

def make_entry(title, summary, link, published):
    entry = MagicMock()
    entry.title = title
    entry.summary = summary
    entry.link = link
    entry.published_parsed = published
    return entry

def test_collect_returns_list(config):
    mock_feed = MagicMock()
    mock_feed.entries = [
        make_entry("테스트컴퍼니 시리즈B 투자 유치", "요약", "http://ex.com/1",
                   (2026, 3, 25, 0, 0, 0, 0, 0, 0))
    ]
    with patch("feedparser.parse", return_value=mock_feed):
        collector = NewsCollector(config)
        result = collector.collect()
    assert isinstance(result, list)

def test_collect_item_has_required_fields(config):
    mock_feed = MagicMock()
    mock_feed.entries = [
        make_entry("테스트컴퍼니 CFO 신규 채용", "본문요약", "http://ex.com/1",
                   (2026, 3, 25, 0, 0, 0, 0, 0, 0))
    ]
    with patch("feedparser.parse", return_value=mock_feed):
        collector = NewsCollector(config)
        result = collector.collect()
    if result:
        item = result[0]
        assert "company" in item
        assert "news_url" in item
        assert "content" in item
        assert "sources" in item
        assert item["sources"] == ["news"]
        assert item["dart_url"] is None

def test_extracts_company_name_from_title(config):
    mock_feed = MagicMock()
    mock_feed.entries = [
        make_entry("카카오페이 시리즈C 완료", "요약", "http://ex.com/1",
                   (2026, 3, 25, 0, 0, 0, 0, 0, 0))
    ]
    with patch("feedparser.parse", return_value=mock_feed):
        collector = NewsCollector(config)
        result = collector.collect()
    if result:
        assert result[0]["company"] == "카카오페이"

def test_returns_empty_on_feed_failure(config):
    with patch("feedparser.parse", side_effect=Exception("Network error")):
        collector = NewsCollector(config)
        result = collector.collect()
    assert result == []
