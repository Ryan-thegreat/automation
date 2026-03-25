import pytest
from src.main import deduplicate

def test_deduplication_merges_dart_and_news_same_company():
    dart_items = [{"company": "테스트컴퍼니", "dart_url": "http://dart", "dart_content": "감사보고서", "news_url": None, "news_content": None, "content": "테스트컴퍼니 감사보고서", "sources": ["dart"]}]
    news_items = [{"company": "테스트컴퍼니", "news_url": "http://news", "news_content": "시리즈B", "dart_url": None, "dart_content": None, "content": "테스트컴퍼니 시리즈B", "sources": ["news"]}]
    result = deduplicate(dart_items, news_items)
    assert len(result) == 1
    assert "dart" in result[0]["sources"]
    assert "news" in result[0]["sources"]
    assert result[0]["dart_url"] == "http://dart"
    assert result[0]["news_url"] == "http://news"

def test_deduplication_keeps_separate_companies():
    dart_items = [{"company": "회사A", "dart_url": "http://dart", "dart_content": "x", "news_url": None, "news_content": None, "content": "x", "sources": ["dart"]}]
    news_items = [{"company": "회사B", "news_url": "http://news", "news_content": "y", "dart_url": None, "dart_content": None, "content": "y", "sources": ["news"]}]
    result = deduplicate(dart_items, news_items)
    assert len(result) == 2

def test_deduplication_empty_inputs():
    assert deduplicate([], []) == []
    dart_only = [{"company": "A", "dart_url": "d", "dart_content": "x", "news_url": None, "news_content": None, "content": "x", "sources": ["dart"]}]
    assert len(deduplicate(dart_only, [])) == 1
    assert len(deduplicate([], dart_only)) == 1

def test_deduplication_merged_content_combines_both():
    dart_items = [{"company": "테스트컴퍼니", "dart_url": "d", "dart_content": "감사보고서", "news_url": None, "news_content": None, "content": "테스트컴퍼니 감사보고서", "sources": ["dart"]}]
    news_items = [{"company": "테스트컴퍼니", "news_url": "n", "news_content": "시리즈B 투자", "dart_url": None, "dart_content": None, "content": "테스트컴퍼니 시리즈B", "sources": ["news"]}]
    result = deduplicate(dart_items, news_items)
    assert "감사보고서" in result[0]["content"]
    assert "시리즈B" in result[0]["content"]
