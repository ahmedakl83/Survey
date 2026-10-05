from dataclasses import dataclass, field
from enum import IntEnum
from typing import List


class QuestionType(IntEnum):
    GENERAL = 0       # نص حر
    DEMOGRAPHIC_SINGLE = 1    # ديموغرافي - إجابة واحدة
    DEMOGRAPHIC_MULTIPLE = 2  # ديموغرافي - إجابات متعددة
    LIKERT = 3        # ليكرت - إجابة واحدة
    DEMOGRAPHIC_SINGLE_OTHER = 4 # ديموغرافي - إجابة واحدة مع خيار أخرى


@dataclass
class Question:
    id: int = 0
    template_id: int = 0
    column_index: int = 0
    text: str = ""
    question_type: QuestionType = QuestionType.GENERAL
    answers: List[str] = field(default_factory=list)
    likert_scale_id: int = 0  # 0 = لا ينتمي لمقياس
    branching_rules: dict = field(default_factory=dict)  # خريطة: {نص_الإجابة: كائن_السؤال_المستهدف}

    @property
    def is_general(self) -> bool:
        return self.question_type == QuestionType.GENERAL

    @property
    def is_single_choice(self) -> bool:
        return self.question_type in (
            QuestionType.DEMOGRAPHIC_SINGLE,
            QuestionType.LIKERT,
            QuestionType.DEMOGRAPHIC_SINGLE_OTHER
        )

    @property
    def is_multiple_choice(self) -> bool:
        return self.question_type == QuestionType.DEMOGRAPHIC_MULTIPLE

    def get_type_label(self) -> str:
        labels = {
            QuestionType.GENERAL: "عام",
            QuestionType.DEMOGRAPHIC_SINGLE: "ديموغرافي (إجابة واحدة)",
            QuestionType.DEMOGRAPHIC_MULTIPLE: "ديموغرافي (إجابات متعددة)",
            QuestionType.LIKERT: "ليكرت",
            QuestionType.DEMOGRAPHIC_SINGLE_OTHER: "ديموغرافي (إجابة واحدة + أخرى)",
        }
        return labels.get(self.question_type, "غير معروف")
