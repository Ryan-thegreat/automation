import pytest
from src.filters.keyword import KeywordFilter

@pytest.fixture
def config():
    return {
        "filter": {
            "exclusion_keywords": ["코스닥 상장", "부동산", "회생절차"],
            "inclusion_keywords": ["시리즈B", "CFO", "매출 성장"]
        }
    }

def test_excludes_when_exclusion_keyword_present(config):
    f = KeywordFilter(config)
    item = {"company": "테스트", "content": "코스닥 상장 기업의 실적 발표"}
    assert f.should_pass(item) is False

def test_passes_when_inclusion_keyword_present(config):
    f = KeywordFilter(config)
    item = {"company": "테스트", "content": "시리즈B 투자 유치 소식"}
    assert f.should_pass(item) is True

def test_drops_when_no_inclusion_keyword(config):
    f = KeywordFilter(config)
    item = {"company": "테스트", "content": "일반 뉴스 기사"}
    assert f.should_pass(item) is False

def test_exclusion_takes_priority_over_inclusion(config):
    f = KeywordFilter(config)
    item = {"company": "테스트", "content": "시리즈B 회생절차 동시 포함"}
    assert f.should_pass(item) is False

def test_filter_list(config):
    f = KeywordFilter(config)
    items = [
        {"company": "A", "content": "시리즈B 투자"},
        {"company": "B", "content": "부동산 분양"},
        {"company": "C", "content": "CFO 신규 채용"},
    ]
    result = f.filter(items)
    assert len(result) == 2
    assert result[0]["company"] == "A"
    assert result[1]["company"] == "C"
