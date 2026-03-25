import requests
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)
DART_API_URL = "https://opendart.fss.or.kr/api/list.json"
MAX_RETRIES = 3

class DartCollector:
    def __init__(self, config: dict, api_key: str):
        self.config = config["dart"]
        self.api_key = api_key

    def collect(self) -> list[dict]:
        bgn_de = (datetime.now() - timedelta(days=self.config["lookback_days"])).strftime("%Y%m%d")
        raw_items = self._fetch_with_retry(bgn_de)
        results = []
        for report_type in self.config["report_types"]:
            results.extend(self._parse(raw_items, report_type))
        return results

    def _fetch_with_retry(self, bgn_de: str) -> list[dict]:
        params = {
            "crtfc_key": self.api_key,
            "bgn_de": bgn_de,
            "pblntf_ty": "A",
            "page_count": 100,
        }
        for attempt in range(MAX_RETRIES):
            try:
                resp = requests.get(DART_API_URL, params=params, timeout=10)
                resp.raise_for_status()
                data = resp.json()
                if data.get("status") != "000":
                    logger.warning(f"DART API status: {data.get('status')}")
                    return []
                return data.get("list", [])
            except Exception as e:
                logger.warning(f"DART fetch attempt {attempt+1} failed: {e}")
        logger.error(f"DART fetch failed after {MAX_RETRIES} retries")
        return []

    def _parse(self, items: list, report_type: str) -> list[dict]:
        result = []
        for item in items:
            if report_type not in item.get("report_nm", ""):
                continue
            rcp_no = item.get("rcp_no", "")
            result.append({
                "company": item.get("corp_name", ""),
                "dart_url": f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={rcp_no}",
                "dart_content": f"{item.get('report_nm', '')} {item.get('rcept_dt', '')}",
                "content": f"{item.get('corp_name', '')} {item.get('report_nm', '')}",
                "news_url": None,
                "news_content": None,
                "sources": ["dart"],
            })
        return result
