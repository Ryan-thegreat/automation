import pytest
from unittest.mock import patch, MagicMock
from src.analyzers.claude import ClaudeAnalyzer

@pytest.fixture
def config():
    return {
        "claude": {
            "model": "claude-opus-4-6",
            "max_calls_per_day": 5,
            "max_content_chars": 500
        }
    }

@pytest.fixture
def sample_item():
    return {
        "company": "테스트컴퍼니",
        "content": "테스트컴퍼니 시리즈B 투자 유치, CFO 신규 채용",
        "dart_url": "https://dart.example.com",
        "news_url": None,
        "sources": ["dart"]
    }

def make_mock_response(json_str: str):
    mock_resp = MagicMock()
    mock_resp.content = [MagicMock(text=json_str)]
    return mock_resp

def test_analyze_returns_scored_item(config, sample_item):
    json_str = '{"company":"테스트컴퍼니","stage":"Series B 추정","signal_score":4,"signal_type":["CFO 채용"],"thesis_match":true,"summary":"요약","action":"소개 요청"}'
    with patch("anthropic.Anthropic") as MockClient:
        MockClient.return_value.messages.create.return_value = make_mock_response(json_str)
        analyzer = ClaudeAnalyzer(config, api_key="test")
        result = analyzer.analyze(sample_item)
    assert result["signal_score"] == 4
    assert result["company"] == "테스트컴퍼니"

def test_analyze_handles_json_parse_failure_with_retry(config, sample_item):
    bad_response = make_mock_response("이것은 JSON이 아닙니다")
    good_json = '{"company":"테스트컴퍼니","stage":"추정","signal_score":3,"signal_type":[],"thesis_match":false,"summary":"요약","action":"모니터링"}'
    good_response = make_mock_response(good_json)
    with patch("anthropic.Anthropic") as MockClient:
        MockClient.return_value.messages.create.side_effect = [bad_response, good_response]
        analyzer = ClaudeAnalyzer(config, api_key="test")
        result = analyzer.analyze(sample_item)
    assert result["signal_score"] == 3

def test_analyze_returns_score_zero_on_repeated_failure(config, sample_item):
    bad_response = make_mock_response("not json")
    with patch("anthropic.Anthropic") as MockClient:
        MockClient.return_value.messages.create.return_value = bad_response
        analyzer = ClaudeAnalyzer(config, api_key="test")
        result = analyzer.analyze(sample_item)
    assert result["signal_score"] == 0

def test_daily_cap_enforced(config, sample_item):
    json_str = '{"company":"X","stage":"추정","signal_score":3,"signal_type":[],"thesis_match":false,"summary":"요약","action":"모니터링"}'
    with patch("anthropic.Anthropic") as MockClient:
        MockClient.return_value.messages.create.return_value = make_mock_response(json_str)
        analyzer = ClaudeAnalyzer(config, api_key="test")
        items = [sample_item] * 10  # cap=5
        results = analyzer.analyze_batch(items)
    assert MockClient.return_value.messages.create.call_count <= 5
    assert all(r["signal_score"] == 0 for r in results[5:])
