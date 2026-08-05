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
        path.parent.mkdir(parents=True, exist_ok=True)
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

    # quick_review(IR덱 딥다이브) 결과를 같은 딜카드에 연결하기 위한 진입점.
    # 소싱(daily scan)과 딥다이브(수동 업로드) 두 경로가 동일한 회사에 대해
    # 서로 다른 파일에 흩어지지 않고 하나의 파이프라인 뷰로 모이도록 한다.
    GRADE_TO_FOLDER = {"A": "hot", "B": "hot", "C": "watch", "D": "archive"}

    def attach_deep_dive(
        self,
        company: str,
        grade: str,
        total_score: float,
        summary: str,
        report_ref: str,
        date_str: str = None,
    ) -> Path:
        """quick_review의 5축 딥다이브 결과를 딜카드에 첨부.

        기존 딜카드가 있으면 append, 없으면(소싱을 거치지 않고 IR덱을 바로
        업로드한 경우) grade 기준으로 새 카드를 만든다.
        """
        if date_str is None:
            date_str = Date.today().isoformat()
        safe_company = re.sub(r'[\\/*?:"<>|]', "", company)
        block = (
            f"\n---\n## 심층 DD 리포트 (quick_review): {date_str}\n"
            f"- 등급: {grade} (종합 {total_score}/100)\n"
            f"- 리포트: {report_ref}\n\n{summary}\n"
        )
        existing = self._find_existing(safe_company)
        if existing:
            with existing.open("a", encoding="utf-8") as f:
                f.write(block)
            logger.info(f"Attached deep-dive to existing deal card: {existing}")
            return existing

        folder = self.GRADE_TO_FOLDER.get(grade, "watch")
        path = self.deals_dir / folder / f"{date_str}-{safe_company}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        header = (
            f"---\ntype: deal-deep-dive\ncompany: {company}\n"
            f"grade: {grade}\ntotal-score: {total_score}\n"
            f"source-date: {date_str}\nstatus: 검토대기\n---\n"
        )
        path.write_text(header + block, encoding="utf-8")
        logger.info(f"Created deal card from deep-dive: {path}")
        return path
