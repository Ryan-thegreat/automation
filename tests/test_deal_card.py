import pytest
from pathlib import Path
from src.outputs.deal_card import DealCardWriter

@pytest.fixture
def config():
    return {"alerts": {"hot_score_threshold": 4}}

@pytest.fixture
def tmp_deals(tmp_path):
    for folder in ["hot", "watch", "archive"]:
        (tmp_path / folder).mkdir()
    return tmp_path

@pytest.fixture
def hot_item():
    return {
        "company": "테스트컴퍼니",
        "signal_score": 4,
        "stage": "Series B 추정",
        "signal_type": ["CFO 채용"],
        "thesis_match": True,
        "summary": "요약 3줄",
        "action": "소개 요청",
        "dart_url": "https://dart.example.com",
        "news_url": None,
        "sources": ["dart"],
    }

def test_hot_item_written_to_hot_folder(config, tmp_deals, hot_item):
    writer = DealCardWriter(config, deals_dir=str(tmp_deals))
    writer.write(hot_item, date_str="2026-03-25")
    files = list((tmp_deals / "hot").glob("*.md"))
    assert len(files) == 1

def test_watch_item_written_to_watch_folder(config, tmp_deals, hot_item):
    hot_item["signal_score"] = 3
    writer = DealCardWriter(config, deals_dir=str(tmp_deals))
    writer.write(hot_item, date_str="2026-03-25")
    files = list((tmp_deals / "watch").glob("*.md"))
    assert len(files) == 1

def test_archive_item_written_to_archive_folder(config, tmp_deals, hot_item):
    hot_item["signal_score"] = 1
    writer = DealCardWriter(config, deals_dir=str(tmp_deals))
    writer.write(hot_item, date_str="2026-03-25")
    files = list((tmp_deals / "archive").glob("*.md"))
    assert len(files) == 1

def test_score_zero_written_to_archive(config, tmp_deals, hot_item):
    hot_item["signal_score"] = 0
    writer = DealCardWriter(config, deals_dir=str(tmp_deals))
    writer.write(hot_item, date_str="2026-03-25")
    files = list((tmp_deals / "archive").glob("*.md"))
    assert len(files) == 1

def test_duplicate_company_appends_not_creates(config, tmp_deals, hot_item):
    writer = DealCardWriter(config, deals_dir=str(tmp_deals))
    writer.write(hot_item, date_str="2026-03-25")
    writer.write(hot_item, date_str="2026-03-26")
    all_files = list(tmp_deals.rglob("*.md"))
    assert len(all_files) == 1

def test_dart_only_no_news_link(config, tmp_deals, hot_item):
    writer = DealCardWriter(config, deals_dir=str(tmp_deals))
    writer.write(hot_item, date_str="2026-03-25")
    content = list((tmp_deals / "hot").glob("*.md"))[0].read_text(encoding="utf-8")
    assert "DART 공시" in content
    assert "뉴스 기사" not in content
