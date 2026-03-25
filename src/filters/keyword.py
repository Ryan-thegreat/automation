class KeywordFilter:
    def __init__(self, config: dict):
        self.exclusions = config["filter"]["exclusion_keywords"]
        self.inclusions = config["filter"]["inclusion_keywords"]

    def should_pass(self, item: dict) -> bool:
        content = item.get("content", "") + " " + item.get("company", "")
        for kw in self.exclusions:
            if kw in content:
                return False
        for kw in self.inclusions:
            if kw in content:
                return True
        return False

    def filter(self, items: list[dict]) -> list[dict]:
        return [item for item in items if self.should_pass(item)]
