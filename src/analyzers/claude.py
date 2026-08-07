import json
import logging
import anthropic

logger = logging.getLogger(__name__)

PROMPT_TEMPLATE = """당신은 한국 VC 심사역입니다. 아래 기업 정보를 분석해 JSON으로만 응답하세요.

기업명: {company}
내용: {content}

분석 기준:
1. 스테이지: 시리즈B 이상 여부 추정
2. 신호 품질 점수(1~5): 5=DART감사보고서+3년연속고성장, 4=CFO채용+매출성장, 3=투자유치뉴스, 2=채용급증, 1=키워드매칭만
3. 투자 기준 부합 여부

반드시 아래 JSON 형식으로만 응답:
{{"company":"{company}","stage":"추정 스테이지","signal_score":숫자,"signal_type":["신호유형"],"thesis_match":true/false,"summary":"3줄요약","action":"권장액션"}}"""

class ClaudeAnalyzer:
    def __init__(self, config: dict, api_key: str):
        self.config = config["claude"]
        self.client = anthropic.Anthropic(api_key=api_key)
        self._call_count = 0

    def analyze_batch(self, items: list[dict]) -> list[dict]:
        return [self.analyze(item) for item in items]

    def analyze(self, item: dict) -> dict:
        if self._call_count >= self.config["max_calls_per_day"]:
            logger.warning("Daily Claude call cap reached — skipping")
            return self._fallback(item, score=0)

        content = item.get("content", "")[:self.config["max_content_chars"]]
        prompt = PROMPT_TEMPLATE.format(company=item["company"], content=content)

        for attempt in range(2):
            try:
                self._call_count += 1
                resp = self.client.messages.create(
                    model=self.config["model"],
                    max_tokens=512,
                    messages=[{"role": "user", "content": prompt}]
                )
                text = resp.content[0].text.strip()
                if text.startswith("```"):
                    text = text.split("```")[1]
                    if text.startswith("json"):
                        text = text[4:]
                parsed = json.loads(text.strip())
                return {**item, **parsed}
            except (json.JSONDecodeError, Exception) as e:
                logger.warning(f"Claude attempt {attempt+1} failed: {e}")

        return self._fallback(item, score=0)

    def _fallback(self, item: dict, score: int) -> dict:
        return {
            **item,
            "signal_score": score,
            "stage": "분석 실패",
            "signal_type": [],
            "thesis_match": False,
            "summary": "Claude 분석 실패 — 원본 데이터 보존",
            "action": "수동 확인 필요",
        }
