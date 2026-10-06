import json
from datetime import datetime
from models.template import Template, LikertScale
from models.question import Question, QuestionType

def export_template_to_json(template: Template, file_path: str):
    """
    تصدير قالب (الأسئلة ومقاييس ليكرت) إلى ملف JSON.
    """
    # تجهيز مقاييس ليكرت
    scales_data = []
    scale_id_to_index = {}
    for idx, scale in enumerate(template.likert_scales):
        scales_data.append({
            "name": scale.name,
            "answers": scale.answers
        })
        if scale.id:
            scale_id_to_index[scale.id] = idx

    # تجهيز الأسئلة
    questions_data = []
    for q in template.questions:
        scale_idx = -1
        if q.question_type == QuestionType.LIKERT:
            if q.likert_scale_id in scale_id_to_index:
                scale_idx = scale_id_to_index[q.likert_scale_id]
            else:
                # محاولة المطابقة بالإجابات إذا لم يكن المعرف مسجلاً
                for idx, s in enumerate(template.likert_scales):
                    if s.answers == q.answers:
                        scale_idx = idx
                        break

        branching_data = {}
        if hasattr(q, "branching_rules") and q.branching_rules:
            for ans, target_q in q.branching_rules.items():
                if isinstance(target_q, Question):
                    branching_data[ans] = target_q.column_index
                elif isinstance(target_q, int):
                    branching_data[ans] = target_q

        questions_data.append({
            "column_index": q.column_index,
            "text": q.text,
            "question_type": int(q.question_type),
            "answers": q.answers,
            "likert_scale_index": scale_idx,
            "branching": branching_data,
            "section_header": getattr(q, "section_header", "") or ""
        })

    data = {
        "version": "1.0",
        "app": "SurveyApp",
        "name": template.name,
        "likert_scales": scales_data,
        "questions": questions_data
    }

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def import_template_from_json(file_path: str) -> Template:
    """
    استيراد قالب من ملف JSON المصدر.
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if data.get("app") != "SurveyApp":
        raise ValueError("الملف المحدد ليس ملف قالب صالح لتطبيق تفريغ الاستبيانات.")

    template = Template(
        name=data.get("name", "قالب مستورد"),
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    # استيراد مقاييس ليكرت
    for s_data in data.get("likert_scales", []):
        scale = LikertScale(
            name=s_data["name"],
            answers=s_data["answers"]
        )
        template.likert_scales.append(scale)

    # استيراد الأسئلة
    for q_data in data.get("questions", []):
        q = Question(
            column_index=q_data["column_index"],
            text=q_data["text"],
            question_type=QuestionType(q_data["question_type"]),
            answers=q_data["answers"],
            section_header=q_data.get("section_header", "") or ""
        )
        q._raw_branching = q_data.get("branching", {})
        
        # ربط مرجعي بمقياس ليكرت إذا كان السؤال من هذا النوع
        scale_idx = q_data.get("likert_scale_index", -1)
        if scale_idx != -1 and scale_idx < len(template.likert_scales):
            q._likert_scale_ref = template.likert_scales[scale_idx]  # type: ignore[attr-defined]
            # نضمن تطابق الإجابات مع المقياس
            q.answers = template.likert_scales[scale_idx].answers
            
        template.questions.append(q)

    # ربط قواعد التفريع
    for q in template.questions:
        q.branching_rules = {}
        if hasattr(q, "_raw_branching"):
            for ans, target_idx in q._raw_branching.items():
                target_q = next((t for t in template.questions if t.column_index == int(target_idx)), None)
                if target_q:
                    q.branching_rules[ans] = target_q

    template.question_count = len(template.questions)
    return template
