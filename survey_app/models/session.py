from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class FormResponse:
    """إجابات استمارة واحدة"""
    form_index: int = 0          # رقم الاستمارة (يبدأ من 0)
    answers: Dict[int, str] = field(default_factory=dict)  # question_id -> answer
    is_complete: bool = False
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: int = 0


@dataclass
class Session:
    """جلسة تفريغ نشطة"""
    id: int = 0
    template_id: int = 0
    name: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    total_forms: int = 0
    current_form_index: int = 0
    current_question_index: int = 0
    forms: List[FormResponse] = field(default_factory=list)

    @property
    def completed_forms(self) -> int:
        return sum(1 for f in self.forms if f.is_complete)

    @property
    def progress_percent(self) -> float:
        if self.total_forms == 0:
            return 0.0
        return (self.completed_forms / self.total_forms) * 100

    def get_current_form(self) -> Optional[FormResponse]:
        if 0 <= self.current_form_index < len(self.forms):
            return self.forms[self.current_form_index]
        return None

    def ensure_forms(self):
        """تأكد من وجود كافة الاستمارات في القائمة"""
        while len(self.forms) < self.total_forms:
            idx = len(self.forms)
            self.forms.append(FormResponse(form_index=idx))
