import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from database.db_manager import DatabaseManager
from models.question import Question, QuestionType
from models.session import FormResponse, Session
from models.template import LikertScale, Template


def export_session_backup(session: Session, template: Template, file_path: str):
    """
    تصدير جلسة تفريغ كاملة مع قالبها واستماراتها وإجاباتها إلى ملف نسخة احتياطية JSON.
    """
    # 1. تجهيز مقاييس ليكرت
    scales_data = []
    scale_id_to_index = {}
    for idx, scale in enumerate(template.likert_scales):
        scales_data.append({
            "name": scale.name,
            "answers": scale.answers
        })
        if scale.id:
            scale_id_to_index[scale.id] = idx

    # 2. تجهيز الأسئلة
    questions_data = []
    q_id_to_col = {}
    for q in template.questions:
        if q.id:
            q_id_to_col[q.id] = q.column_index

        scale_idx = -1
        if q.question_type == QuestionType.LIKERT:
            if q.likert_scale_id in scale_id_to_index:
                scale_idx = scale_id_to_index[q.likert_scale_id]
            else:
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

    # 3. تجهيز بيانات الاستمارات
    forms_data = []
    for form in session.forms:
        answers_by_col = {}
        for q_key, ans_val in form.answers.items():
            # المفتاح إما q.id أو column_index
            col_idx = None
            try:
                q_id_int = int(q_key)
                if q_id_int in q_id_to_col:
                    col_idx = q_id_to_col[q_id_int]
                elif any(q.column_index == q_id_int for q in template.questions):
                    col_idx = q_id_int
            except (ValueError, TypeError):
                pass

            if col_idx is not None:
                answers_by_col[str(col_idx)] = ans_val
            else:
                answers_by_col[str(q_key)] = ans_val

        forms_data.append({
            "form_index": form.form_index,
            "answers": answers_by_col,
            "is_complete": bool(form.is_complete),
            "started_at": form.started_at.isoformat() if form.started_at else None,
            "completed_at": form.completed_at.isoformat() if form.completed_at else None,
            "duration_seconds": form.duration_seconds
        })

    payload = {
        "app": "SurveyApp",
        "type": "session_backup",
        "version": "1.0",
        "exported_at": datetime.now().isoformat(),
        "session": {
            "name": session.name,
            "total_forms": session.total_forms,
            "current_form_index": session.current_form_index,
            "current_question_index": session.current_question_index,
            "created_at": session.created_at.isoformat() if hasattr(session, "created_at") and session.created_at else datetime.now().isoformat(),
            "updated_at": session.updated_at.isoformat() if hasattr(session, "updated_at") and session.updated_at else datetime.now().isoformat()
        },
        "template": {
            "name": template.name,
            "likert_scales": scales_data,
            "questions": questions_data
        },
        "forms": forms_data
    }

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def read_session_backup_info(file_path: str) -> dict:
    """
    قراءة ملف النسخة الاحتياطية للجلسة والتحقق من صحته، وإرجاع ملخص للبيانات.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        raise ValueError(f"تعذّر قراءة الملف: {e}")

    if data.get("app") != "SurveyApp" or data.get("type") != "session_backup":
        raise ValueError("الملف المحدد ليس ملف نسخة احتياطية صالح لجلسة تفريغ.")

    session_info = data.get("session", {})
    template_info = data.get("template", {})
    forms_list = data.get("forms", [])

    if not session_info or not template_info:
        raise ValueError("بيانات الجلسة أو القالب مفقودة في الملف.")

    completed_count = sum(1 for f in forms_list if f.get("is_complete"))

    return {
        "session_name": session_info.get("name", "جلسة بدون اسم"),
        "total_forms": session_info.get("total_forms", len(forms_list)),
        "completed_forms": completed_count,
        "current_form_index": session_info.get("current_form_index", 0),
        "template_name": template_info.get("name", "قالب غير معروف"),
        "questions_count": len(template_info.get("questions", [])),
        "exported_at": data.get("exported_at", ""),
        "raw_data": data
    }


def find_or_create_template_for_session(template_data: dict, db: DatabaseManager) -> Template:
    """
    البحث عن قالب مطابق في قاعدة البيانات أو إنشاء قالب جديد إن لم يكن موجوداً.
    """
    t_name = template_data.get("name", "قالب مستورد")
    imp_questions = template_data.get("questions", [])

    # فحص القوالب الحالية
    all_templates = db.load_all_templates()
    for t in all_templates:
        if t.name.strip() == t_name.strip() and len(t.questions) == len(imp_questions):
            # مطابقة الأسئلة
            t_qs = sorted(t.questions, key=lambda q: q.column_index)
            imp_qs_sorted = sorted(imp_questions, key=lambda q: q["column_index"])
            matches = True
            for q1, q2 in zip(t_qs, imp_qs_sorted):
                if q1.column_index != q2["column_index"] or q1.text.strip() != q2["text"].strip():
                    matches = False
                    break
            if matches:
                return t

    # إنشاء قالب جديد
    # إذا كان هناك قالب بنفس الاسم لكن بأسئلة مختلفة، نميز الاسم
    existing_same_name = [t for t in all_templates if t.name.strip() == t_name.strip()]
    if existing_same_name:
        final_t_name = f"{t_name} (مستورد)"
    else:
        final_t_name = t_name

    new_template = Template(
        name=final_t_name,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    # مقاييس ليكرت
    for s_data in template_data.get("likert_scales", []):
        scale = LikertScale(
            name=s_data["name"],
            answers=s_data["answers"]
        )
        new_template.likert_scales.append(scale)

    # الأسئلة
    for q_data in imp_questions:
        q = Question(
            column_index=q_data["column_index"],
            text=q_data["text"],
            question_type=QuestionType(q_data["question_type"]),
            answers=q_data["answers"],
            section_header=q_data.get("section_header", "") or ""
        )
        q._raw_branching = q_data.get("branching", {})

        scale_idx = q_data.get("likert_scale_index", -1)
        if scale_idx != -1 and scale_idx < len(new_template.likert_scales):
            q._likert_scale_ref = new_template.likert_scales[scale_idx]
            q.answers = new_template.likert_scales[scale_idx].answers

        new_template.questions.append(q)

    # ربط قواعد التفريع
    for q in new_template.questions:
        q.branching_rules = {}
        if hasattr(q, "_raw_branching"):
            for ans, target_idx in q._raw_branching.items():
                target_q = next((t for t in new_template.questions if t.column_index == int(target_idx)), None)
                if target_q:
                    q.branching_rules[ans] = target_q

    new_template.question_count = len(new_template.questions)
    new_tid = db.save_template(new_template)
    loaded = db.load_template(new_tid)
    return loaded if loaded else new_template


def import_session_into_db(
    raw_data: dict,
    db: DatabaseManager,
    custom_session_name: Optional[str] = None,
    overwrite_session_id: Optional[int] = None
) -> Session:
    """
    استيراد بيانات الجلسة بالكامل وحفظها في قاعدة البيانات دون مسح أي جلسات أخرى.
    """
    if overwrite_session_id is not None:
        db.delete_session(overwrite_session_id)

    session_data = raw_data["session"]
    template_data = raw_data["template"]
    forms_data = raw_data.get("forms", [])

    # 1. إيجاد أو إنشاء القالب المناسب
    target_template = find_or_create_template_for_session(template_data, db)

    # خريطة column_index إلى كائن السؤال في القالب الهدف
    col_to_q = {q.column_index: q for q in target_template.questions}

    # 2. بناء كائنات FormResponse
    forms: List[FormResponse] = []
    for f_info in forms_data:
        f_idx = f_info.get("form_index", len(forms))
        raw_answers = f_info.get("answers", {})

        mapped_answers = {}
        for col_str, ans_val in raw_answers.items():
            try:
                c_idx = int(col_str)
                if c_idx in col_to_q:
                    q_target = col_to_q[c_idx]
                    mapped_answers[q_target.id] = ans_val
                else:
                    mapped_answers[c_idx] = ans_val
            except (ValueError, TypeError):
                pass

        started_at = None
        if f_info.get("started_at"):
            try:
                started_at = datetime.fromisoformat(f_info["started_at"])
            except Exception:
                pass

        completed_at = None
        if f_info.get("completed_at"):
            try:
                completed_at = datetime.fromisoformat(f_info["completed_at"])
            except Exception:
                pass

        form_resp = FormResponse(
            form_index=f_idx,
            answers=mapped_answers,
            is_complete=bool(f_info.get("is_complete", False)),
            started_at=started_at,
            completed_at=completed_at,
            duration_seconds=f_info.get("duration_seconds", 0)
        )
        forms.append(form_resp)

    # 3. بناء الجلسة
    s_name = custom_session_name or session_data.get("name", "جلسة مستوردة")
    total_forms = session_data.get("total_forms", len(forms))

    created_at = datetime.now()
    if session_data.get("created_at"):
        try:
            created_at = datetime.fromisoformat(session_data["created_at"])
        except Exception:
            pass

    updated_at = datetime.now()
    if session_data.get("updated_at"):
        try:
            updated_at = datetime.fromisoformat(session_data["updated_at"])
        except Exception:
            pass

    session = Session(
        template_id=target_template.id,
        name=s_name,
        created_at=created_at,
        updated_at=updated_at,
        total_forms=total_forms,
        current_form_index=session_data.get("current_form_index", 0),
        current_question_index=session_data.get("current_question_index", 0)
    )
    session.forms = forms
    session.ensure_forms()

    # 4. حفظ الجلسة في قاعدة البيانات
    db.save_session(session)
    db.increment_template_use(target_template.id)

    return session
