from dataclasses import dataclass, field
from datetime import datetime
from typing import List
from models.question import Question


@dataclass
class LikertScale:
    id: int = 0
    template_id: int = 0
    name: str = ""
    answers: List[str] = field(default_factory=list)


@dataclass
class Template:
    id: int = 0
    name: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    question_count: int = 0
    use_count: int = 0
    questions: List[Question] = field(default_factory=list)
    likert_scales: List[LikertScale] = field(default_factory=list)
