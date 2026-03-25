import re
import logging
from pathlib import Path
from datetime import date as Date

logger = logging.getLogger(__name__)

SCORE_TO_FOLDER = {
    (4, 5): "hot",
    (3, 3): "watch",
    (0, 2): "archive",
}

def _get_folder(score: int) -> str:
    for (low, high), folder in SCORE_TO_FOLDER.items():
        if low <= score <= high:
            return folder
    return "archive"

class DealCardWriter:
    def __init__(self, config: dict, deals_dir: str = "Deals/pipeline"):
        self.deals_dir = Path(deals_dir)

    def write(self, item: dict, date_str: str = None) -> Path:
        if date_str is None:
            date_str = Date.today().isoformat()
        company = re.sub(r'[\\/*?:"<>|]', "", item["company"])
        existing = self._find_existing(company)
        if existing:
            self._append(existing, item, date_str)
            return existing
        folder = _get_folder(item["signal_score"])
        path = self.deals_dir / folder / f"{date_str}-{company}.md"
        path.write_text(self._render(item, date_str), encoding="utf-8")
        logger.info(f"Created deal card: {path}")
        return path

    def _find_existing(self, company: str) -> Path | None:
        for md in self.deals_dir.rglob(f"*{company}.md"):
            return md
        return None

    def _append(self, path: Path, item: dict, date_str: str):
        append_block = f"\n---\n## 업데이트: {date_str}\n{item.get('summary', '')}\n"
        with path.open("a", encoding="utf-8") as f:
            f.write(append_block)
        logger.info(f"Appended to existing deal card: {path}")

    def _render(self, item: dict, date_str: str) -> str:
        signal_types = ", ".join(item.get("signal_type", []))
        sources_block = self._render_sources(item)
        return f"""---
type: deal-incoming
company: {item['company']}
stage: {item.get('stage', '미상')}
signal-score: {item.get('signal_score', 0)}
signal-type: [{signal_types}]
thesis-match: {str(item.get('thesis_match', False)).lower()}
source-date: {date_str}
status: 검토대기
---

## AI 요약
{item.get('summary', '')}

## 권장 액션
{item.get('action', '')}

## 소스
{sources_block}
"""

    def _render_sources(self, item: dict) -> str:
        lines = []
        if item.get("dart_url"):
            lines.append(f"- [DART 공시]({item['dart_url']})")
        if item.get("news_url"):
            lines.append(f"- [뉴스 기사]({item['news_url']})")
        return "\n".join(lines) if lines else "- 소스 없음"
