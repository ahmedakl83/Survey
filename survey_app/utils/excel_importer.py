from datetime import datetime
from typing import Dict, List, Tuple
import openpyxl
from models.question import Question, QuestionType
from models.template import Template, LikertScale
from models.session import Session, FormResponse


class ImportError(Exception):
    pass


def import_template_from_excel(file_path: str) -> Tuple[Template, List[str]]:
    """
    يقرأ ملف Excel ويستخرج الأسئلة وأنواعها وإجاباتها.
    يعيد (Template, warnings) حيث warnings قائمة تحذيرات غير مميتة.
    يرفع ImportError عند وجود خطأ مميت.
    """
    try:
        wb = openpyxl.load_workbook(file_path, data_only=True)
    except Exception as e:
        raise ImportError(f"تعذّر فتح الملف: {e}")

    ws = wb.active
    if ws is None:
        wb.close()
        raise ImportError("الملف لا يحتوي على أي ورقة بيانات.")

    # قراءة كل الأعمدة عبر iter_cols
    all_columns: List[List] = []
    for col in ws.iter_cols():
        values = [cell.value for cell in col]
        all_columns.append(values)

    wb.close()
    del wb

    if not all_columns:
        raise ImportError("الملف فارغ.")

    warnings: List[str] = []
    questions: List[Question] = []
    likert_map: dict = {}   # answers_key -> LikertScale
    likert_scales: List[LikertScale] = []

    for col_idx, col_values in enumerate(all_columns):
        if not col_values or col_values[0] is None:
            warnings.append(f"العمود {col_idx + 1} فارغ، تم تجاهله.")
            continue

        header = str(col_values[0]).strip()
        if not header:
            warnings.append(f"العمود {col_idx + 1} لا يحتوي على رأس، تم تجاهله.")
            continue

        # استخراج الخلايا غير الفارغة بعد الرأس
        rest = [v for v in col_values[1:] if v is not None and str(v).strip() != ""]

        if not rest:
            # سؤال عام (لا توجد إجابات ولا رقم نوع)
            q = Question(
                column_index=col_idx,
                text=header,
                question_type=QuestionType.GENERAL,
                answers=[]
            )
            questions.append(q)
            continue

        # آخر عنصر هو رقم النوع إذا كان رقماً صحيحاً 1/2/3/4
        last = str(rest[-1]).strip()
        if last in ("1", "2", "3", "4"):
            type_num = int(last)
            answer_values = [str(v).strip() for v in rest[:-1] if str(v).strip()]
        else:
            # لا يوجد رقم نوع → سؤال عام
            type_num = 0
            answer_values = []

        if type_num == 0:
            q = Question(
                column_index=col_idx,
                text=header,
                question_type=QuestionType.GENERAL,
                answers=[]
            )
        elif type_num == 1:
            if not answer_values:
                warnings.append(f"السؤال '{header}' ديموغرافي لكن لا يحتوي على إجابات.")
            q = Question(
                column_index=col_idx,
                text=header,
                question_type=QuestionType.DEMOGRAPHIC_SINGLE,
                answers=answer_values
            )
        elif type_num == 2:
            if not answer_values:
                warnings.append(f"السؤال '{header}' ديموغرافي متعدد لكن لا يحتوي على إجابات.")
            q = Question(
                column_index=col_idx,
                text=header,
                question_type=QuestionType.DEMOGRAPHIC_MULTIPLE,
                answers=answer_values
            )
        elif type_num == 3:
            if not answer_values:
                warnings.append(f"السؤال '{header}' ليكرت لكن لا يحتوي على إجابات.")
            # تجميع مقاييس ليكرت المتطابقة
            key = tuple(answer_values)
            if key not in likert_map:
                scale = LikertScale(
                    name=f"مقياس ليكرت {len(likert_scales) + 1}",
                    answers=answer_values
                )
                likert_scales.append(scale)
                likert_map[key] = scale
            else:
                scale = likert_map[key]

            q = Question(
                column_index=col_idx,
                text=header,
                question_type=QuestionType.LIKERT,
                answers=answer_values,
                likert_scale_id=0  # سيُحدَّث بعد الحفظ
            )
            # نربط السؤال بالمقياس مؤقتاً عبر الكائن
            q._likert_scale_ref = scale  # type: ignore[attr-defined]
        elif type_num == 4:
            if not answer_values:
                warnings.append(f"السؤال '{header}' ديموغرافي مع أخرى لكن لا يحتوي على إجابات.")
            q = Question(
                column_index=col_idx,
                text=header,
                question_type=QuestionType.DEMOGRAPHIC_SINGLE_OTHER,
                answers=answer_values
            )
        else:
            warnings.append(
                f"السؤال '{header}': رقم النوع '{last}' غير معروف، تم تصنيفه كسؤال عام."
            )
            q = Question(
                column_index=col_idx,
                text=header,
                question_type=QuestionType.GENERAL,
                answers=[]
            )

        questions.append(q)

    if not questions:
        raise ImportError("لم يتم العثور على أي أسئلة صالحة في الملف.")

    template = Template(
        questions=questions,
        likert_scales=likert_scales,
        question_count=len(questions)
    )
    return template, warnings


def import_responses_from_excel(
    file_path: str,
    template: Template
) -> Tuple[List[FormResponse], List[str]]:
    """
    يقرأ ملف Excel يحتوي على إجابات رقمية ويحوّلها إلى نصوص بالاستناد إلى القالب.

    بنية الملف المتوقعة:
    - الصف الأول: أسماء الأسئلة (رؤوس الأعمدة)
    - الصفوف التالية: كل صف = استمارة واحدة، القيم أرقام تمثل رقم الإجابة

    يعيد (forms, warnings) حيث:
    - forms: قائمة FormResponse جاهزة للحفظ
    - warnings: تحذيرات غير مميتة
    يرفع ImportError عند وجود خطأ مميت.
    """
    try:
        wb = openpyxl.load_workbook(file_path, data_only=True)
    except Exception as e:
        raise ImportError(f"تعذّر فتح الملف: {e}")

    ws = wb.active
    if ws is None:
        wb.close()
        raise ImportError("الملف لا يحتوي على أي ورقة بيانات.")

    rows = list(ws.iter_rows(values_only=True))
    wb.close()

    if not rows:
        raise ImportError("الملف فارغ.")

    # ─── الصف الأول: رؤوس الأعمدة (أسماء الأسئلة) ───────────────────────────
    header_row = [str(v).strip() if v is not None else "" for v in rows[0]]
    data_rows = rows[1:]

    if not data_rows:
        raise ImportError("الملف لا يحتوي على أي بيانات (صف الرأس فقط).")

    # بناء خريطة: اسم السؤال → كائن Question من القالب
    # نستخدم المطابقة بالنص (case-insensitive مع تجاهل المسافات الزائدة)
    question_map: Dict[str, Question] = {}
    for q in template.questions:
        question_map[q.text.strip().lower()] = q

    warnings: List[str] = []

    # ربط كل عمود في الملف بسؤال من القالب
    col_to_question: Dict[int, Question] = {}
    for col_idx, header in enumerate(header_row):
        if not header:
            warnings.append(f"العمود {col_idx + 1} لا يحتوي على رأس، سيتم تجاهله.")
            continue
        q = question_map.get(header.lower())
        if q is None:
            warnings.append(
                f"العمود '{header}' لا يطابق أي سؤال في القالب، سيتم تجاهله."
            )
        else:
            col_to_question[col_idx] = q

    if not col_to_question:
        raise ImportError(
            "لم يتم العثور على أي تطابق بين أعمدة الملف وأسئلة القالب.\n"
            "تأكد من أن أسماء الأعمدة في الملف تطابق أسماء الأسئلة في القالب."
        )

    # ─── معالجة صفوف البيانات ────────────────────────────────────────────────
    forms: List[FormResponse] = []
    now = datetime.now()

    for row_idx, row in enumerate(data_rows):
        # تجاهل الصفوف الفارغة كلياً
        if all(v is None or str(v).strip() == "" for v in row):
            continue

        answers: Dict[int, str] = {}

        for col_idx, q in col_to_question.items():
            raw = row[col_idx] if col_idx < len(row) else None

            if raw is None or str(raw).strip() == "":
                # خلية فارغة → إجابة فارغة
                answers[q.id] = ""
                continue

            raw_str = str(raw).strip()

            if q.question_type == QuestionType.GENERAL:
                # سؤال عام: نأخذ القيمة كما هي
                answers[q.id] = raw_str

            elif q.question_type == QuestionType.DEMOGRAPHIC_MULTIPLE:
                # متعدد: قد يكون "1,3" أو "1" أو "1 3"
                # نحوّل كل رقم إلى نص الإجابة
                # نقبل الفاصلة أو المسافة أو الشرطة كفاصل
                import re
                parts = re.split(r"[,،\s/]+", raw_str)
                selected = []
                for part in parts:
                    part = part.strip()
                    if not part:
                        continue
                    try:
                        num = int(float(part))
                        if 1 <= num <= len(q.answers):
                            selected.append(q.answers[num - 1])
                        else:
                            warnings.append(
                                f"الصف {row_idx + 2}، السؤال '{q.text}': "
                                f"الرقم {num} خارج النطاق (1–{len(q.answers)})، تم تجاهله."
                            )
                    except (ValueError, TypeError):
                        # ليس رقماً → نأخذه كنص مباشر إن كان موجوداً في الإجابات
                        if part in q.answers:
                            selected.append(part)
                        else:
                            warnings.append(
                                f"الصف {row_idx + 2}، السؤال '{q.text}': "
                                f"القيمة '{part}' غير صالحة، تم تجاهلها."
                            )
                answers[q.id] = ",".join(selected)

            else:
                # DEMOGRAPHIC_SINGLE أو LIKERT أو DEMOGRAPHIC_SINGLE_OTHER: رقم واحد
                try:
                    num = int(float(raw_str))
                    if 1 <= num <= len(q.answers):
                        answers[q.id] = q.answers[num - 1]
                    else:
                        warnings.append(
                            f"الصف {row_idx + 2}، السؤال '{q.text}': "
                            f"الرقم {num} خارج النطاق (1–{len(q.answers)})، "
                            f"تم ترك الإجابة فارغة."
                        )
                        answers[q.id] = ""
                except (ValueError, TypeError):
                    # ليس رقماً → قد يكون نص الإجابة مباشرة
                    if raw_str in q.answers:
                        answers[q.id] = raw_str
                    elif q.question_type == QuestionType.DEMOGRAPHIC_SINGLE_OTHER:
                        answers[q.id] = raw_str
                    else:
                        warnings.append(
                            f"الصف {row_idx + 2}، السؤال '{q.text}': "
                            f"القيمة '{raw_str}' ليست رقماً صحيحاً ولا تطابق أي إجابة، "
                            f"تم ترك الإجابة فارغة."
                        )
                        answers[q.id] = ""

        form = FormResponse(
            form_index=len(forms),
            answers=answers,
            is_complete=True,
            started_at=now,
            completed_at=now,
            duration_seconds=0
        )
        forms.append(form)

    if not forms:
        raise ImportError("لم يتم العثور على أي صفوف بيانات صالحة في الملف.")

    return forms, warnings
