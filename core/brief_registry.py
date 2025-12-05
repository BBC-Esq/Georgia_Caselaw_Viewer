from __future__ import annotations
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import List, Optional, Literal, Dict, Any
import logging
from utils.helpers import load_yaml, save_yaml

logger = logging.getLogger(__name__)

USER_PATH = Path(__file__).resolve().parent.parent / "config" / "caselaw_viewer_briefs.yaml"
INITIAL_BRIEFS_PATH = Path(__file__).resolve().parent / "initial_briefs.yaml"

BASE_BRIEF_TEMPLATE = "I need you to summarize this court case for me."
TEMPLATE_ENDING = (
    " Your response should contain three sections. First, I want a \"Facts\" section that "
    "contains the name and citation to the case followed by a short summary of the facts "
    "of the case.  The factual summary should be no longer than two to three sentences. "
    "Secondly, I want a \"Holding(s)\" section that briefly states each of the holdings or "
    "rulings that the court made.  Third, I want a \"Reasoning\" section that contains a "
    "nice summary of all of the issues that the Court decided as well as its reasoning. "
    "This \"Reasoning\" section must include citations to any court cases or statutes that "
    "the court relied on and can be up to three paragraphs long."
)
GENERAL_BRIEF_TEMPLATE = BASE_BRIEF_TEMPLATE + TEMPLATE_ENDING
TOPIC_BRIEF_TEMPLATE = (
    BASE_BRIEF_TEMPLATE
    + " However, I want your analysis to solely focus on the legal issue of {topic}.  "
      "Do not discuss any other legal issues unless they are directly related to this "
      "specific legal issue.  If the case does not discuss this specific legal issue, "
      "simply state so and do not analyze the case at all."
    + TEMPLATE_ENDING
)

@dataclass
class BriefType:
    label: str
    kind: Literal["general", "topic"] = "general"
    topic: Optional[str] = None
    template: Optional[str] = None
    enabled: bool = True
    model: Optional[str] = None
    temperature: Optional[float] = None
    max_output_tokens: Optional[int] = None
    category: Optional[str] = None

    def resolved_template(self) -> str:
        if self.template:
            return self.template
        if self.kind == "general":
            return GENERAL_BRIEF_TEMPLATE
        if self.kind == "topic":
            tpc = self.topic or ""
            return TOPIC_BRIEF_TEMPLATE.format(topic=tpc)
        return GENERAL_BRIEF_TEMPLATE

@dataclass
class BriefConfig:
    items: List[BriefType] = field(default_factory=list)

    @staticmethod
    def _sort_key(item: BriefType):
        return (not item.enabled, item.category or "", item.label.lower())

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "BriefConfig":
        items = []
        allowed = {"label","kind","topic","template","enabled","model","temperature","max_output_tokens","category"}
        for raw in d.get("items", []):
            if not isinstance(raw, dict):
                continue
            filtered = {k: v for k, v in raw.items() if k in allowed}
            try:
                items.append(BriefType(**filtered))
            except TypeError as e:
                logger.error(f"Invalid brief item in YAML: {e}")
        items_sorted = sorted(items, key=BriefConfig._sort_key)
        return BriefConfig(items=items_sorted)

    def to_dict(self) -> Dict[str, Any]:
        return {"items": [asdict(i) for i in self.items]}

class BriefRegistry:
    _instance = None

    def __new__(cls) -> "BriefRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._cfg = BriefConfig()
            cls._instance.reload()
        return cls._instance

    def reload(self) -> None:
        user_data = load_yaml(USER_PATH)

        if not USER_PATH.exists():
            initial_data = load_yaml(INITIAL_BRIEFS_PATH)
            self._cfg = BriefConfig.from_dict(initial_data)
            try:
                self.save()
            except (IOError, OSError) as e:
                logger.error(f"Failed to save initial briefs: {e}", exc_info=True)
        else:
            self._cfg = BriefConfig.from_dict(user_data)

    def save(self) -> None:
        save_yaml(USER_PATH, self._cfg.to_dict())

    def list_enabled(self) -> List[BriefType]:
        return [i for i in self._cfg.items if i.enabled]

    def get_general(self) -> Optional[BriefType]:
        for i in self.list_enabled():
            if i.kind == "general":
                return i
        return None

    def list_topics_alpha(self) -> List[BriefType]:
        topics = [i for i in self.list_enabled() if i.kind == "topic"]
        return sorted(topics, key=lambda i: i.label.lower())

    def all_items(self) -> List[BriefType]:
        return list(self._cfg.items)

    def get_categories(self) -> List[str]:
        categories = {item.category for item in self._cfg.items if item.category}
        return sorted(categories)

    def get_briefs_by_category(self, category: Optional[str]) -> List[BriefType]:
        return [i for i in self.list_enabled() if i.category == category and i.kind == "topic"]

    def upsert(self, item: BriefType) -> None:
        by = {i.label: i for i in self._cfg.items}
        by[item.label] = item
        self._cfg.items = sorted(by.values(), key=BriefConfig._sort_key)
        self.save()

    def delete(self, label: str) -> None:
        self._cfg.items = [i for i in self._cfg.items if i.label != label]
        self.save()

registry = BriefRegistry()