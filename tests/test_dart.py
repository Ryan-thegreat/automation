import pytest
from unittest.mock import patch, MagicMock
from src.collectors.dart import DartCollector

@pytest.fixture
def config():
    return {
        "dart": {
            "report_types": ["감사보고서", "유상증자결정"],
            "lookback_days": 1
        }
    }

@pytest.fixture
def mock_dart_response():
    return {
        "status": "000",
        "list": [
            {
                "corp_name": "테스트컴퍼니",
                "report_nm": "감사보고서",
                "rcept_dt": "20260325",
                "rcp_no": "20260325000001"
            },
            {
                "corp_name": "상장회사",
                "report_nm": "유상증자결정",
                "rcept_dt": "20260325",
                "rcp_no": "20260325000002"
            }
        ]
    }

def test_collect_returns_list(config, mock_dart_response):
    with patch("requests.get") as mock_get:
        mock_get.return_value.json.return_value = mock_dart_response
        mock_get.return_value.raise_for_status = MagicMock()
        collector = DartCollector(config, api_key="test_key")
        result = collector.collect()
    assert isinstance(result, list)
    assert len(result) == 2

def test_collect_item_has_required_fields(config, mock_dart_response):
    with patch("requests.get") as mock_get:
        mock_get.return_value.json.return_value = mock_dart_response
        mock_get.return_value.raise_for_status = MagicMock()
        collector = DartCollector(config, api_key="test_key")
        result = collector.collect()
    item = result[0]
    assert "company" in item
    assert "dart_url" in item
    assert "content" in item
    assert "sources" in item
    assert item["sources"] == ["dart"]

def test_collect_returns_empty_on_api_failure(config):
    with patch("requests.get") as mock_get:
        mock_get.side_effect = Exception("Network error")
        collector = DartCollector(config, api_key="test_key")
        result = collector.collect()
    assert result == []

def test_collect_retries_on_timeout(config, mock_dart_response):
    with patch("requests.get") as mock_get:
        mock_get.side_effect = [
            Exception("Timeout"),
            Exception("Timeout"),
            MagicMock(json=MagicMock(return_value=mock_dart_response),
                      raise_for_status=MagicMock())
        ]
        collector = DartCollector(config, api_key="test_key")
        result = collector.collect()
    assert len(result) == 2
    assert mock_get.call_count == 3
