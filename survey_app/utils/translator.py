"""
نظام الترجمة وتعدد اللغات والتوجيه (RTL / LTR) لتطبيق تفريغ الاستبيانات.
Localization, Translation, and Layout Direction System.
"""
from typing import Callable, List, Optional
from PyQt6.QtCore import Qt

_CURRENT_LANGUAGE = "ar"
_LISTENERS: List[Callable[[str], None]] = []

TRANSLATIONS = {
    "ar": {
        # General & App
        "app_name": "تفريغ الاستبيانات",
        "app_title": "تفريغ الاستبيانات - الإصدار {version}",
        "language_toggle": "🌐 English",
        "ready": "جاهز",
        "saving": "⏳ جاري الحفظ...",
        "saved": "✅ تم الحفظ",
        "error_saving": "❌ خطأ في الحفظ",
        "autosaved": "✅ تم الحفظ تلقائياً",
        "back": "→ رجوع",
        "cancel": "إلغاء",
        "ok": "موافق",
        "save": "حفظ",
        "edit": "تعديل",
        "delete": "حذف",
        "close": "إغلاق",
        "use": "استخدام",
        "export": "تصدير",
        "import": "استيراد",
        "confirm": "تأكيد",
        "search": "بحث:",
        "actions": "الإجراءات",
        "warning": "تنبيه",
        "error": "خطأ",
        "success": "نجاح",
        "confirm_delete": "تأكيد الحذف",
        "yes": "نعم",
        "no": "لا",
        "created_date": "تاريخ الإنشاء",
        "last_modified": "آخر تعديل",
        "questions_count": "عدد الأسئلة",
        "usage_count": "مرات الاستخدام",

        # MainWindow Navigation
        "nav_home": "الصفحة الرئيسية",
        "nav_review": "مراجعة الأسئلة",
        "nav_entry": "تفريغ البيانات",
        "nav_results": "النتائج المحفوظة",
        "nav_templates": "إدارة القوالب",
        "nav_stats": "إحصائيات النظام",

        # Home View
        "start_new_session": "ابدأ جلسة تفريغ جديدة",
        "card_import_excel_title": "📂  استيراد ملف Excel",
        "card_import_excel_desc": "استورد ملف Excel يحتوي على الأسئلة\nوإجاباتها وابدأ جلسة تفريغ جديدة",
        "card_import_excel_btn": "استيراد",
        "card_create_template_title": "✨  إنشاء قالب من الصفر",
        "card_create_template_desc": "أنشئ قالباً جديداً يدوياً وقم بإضافة\nالأسئلة والخيارات بنفسك",
        "card_create_template_btn": "إنشاء جديد",
        "card_open_template_title": "📋  فتح قالب محفوظ",
        "card_open_template_desc": "اختر قالباً محفوظاً مسبقاً\nوابدأ جلسة تفريغ جديدة",
        "card_open_template_btn": "فتح قالب",
        "card_resume_session_title": "▶️  استئناف جلسة",
        "card_resume_session_desc": "استأنف جلسة تفريغ سابقة\nمن النقطة التي توقفت عندها",
        "card_resume_session_btn": "استئناف",
        "card_import_responses_title": "🔢  استيراد إجابات رقمية",
        "card_import_responses_desc": "لديك ملف Excel جاهز بأرقام الإجابات؟\nاختر قالباً وسيتم تحويل الأرقام\nإلى نصوص الإجابات تلقائياً",
        "card_import_responses_btn": "استيراد إجابات",
        "recent_templates": "القوالب الأخيرة",
        "no_templates_yet": "لا توجد قوالب محفوظة بعد.",
        "questions_num": "{count} سؤال",
        "used_num_times": "استُخدم {count} مرة",
        "btn_numeric_answers": "📥 إجابات رقمية",
        "tooltip_numeric_answers": "استورد ملف Excel بأرقام الإجابات وطبّق هذا القالب عليه",
        "data_maintenance": "صيانة البيانات",
        "maintenance_desc": "قم بحماية بياناتك عن طريق أخذ نسخة احتياطية دورية أو استعادتها.",
        "btn_backup": "📦 نسخة احتياطية",
        "btn_restore": "🔄 استعادة البيانات",
        "create_new_template_title": "إنشاء قالب جديد",
        "create_new_template_prompt": "أدخل اسماً للقالب الجديد:",
        "default_template_name": "قالب جديد",
        "choose_excel_file": "اختر ملف Excel",
        "excel_files_filter": "ملفات Excel (*.xlsx *.xls)",
        "import_error": "خطأ في الاستيراد",
        "import_warnings_title": "تحذيرات",
        "import_warnings_msg": "تم الاستيراد مع التحذيرات التالية:\n\n{warnings}",
        "template_name_prompt_title": "اسم القالب",
        "template_name_prompt_msg": "أدخل اسماً للقالب:",
        "no_sessions_title": "لا توجد جلسات",
        "no_sessions_msg": "لا توجد جلسات غير مكتملة.",
        "template_not_found": "لم يتم العثور على القالب.",
        "choose_responses_file_title": "اختر ملف الإجابات الرقمية — {template_name}",
        "import_responses_warning_msg": "تم قراءة الملف مع {count} تحذير:\n\n{warnings}\n\nهل تريد المتابعة؟",
        "session_name_title": "اسم الجلسة",
        "session_name_prompt": "القالب: {template}\nعدد الاستمارات المستوردة: {count}\n\nأدخل اسماً لهذه الجلسة:",
        "default_session_name": "جلسة {template}",
        "import_success_title": "تم الاستيراد بنجاح",
        "import_responses_success_msg": "✅ تم استيراد {count} استمارة بنجاح\nالقالب: {template}\n\nيمكنك الآن عرض النتائج أو تصديرها.",
        "need_template_first": "لا توجد قوالب محفوظة بعد.\nيجب استيراد قالب أولاً قبل استيراد ملف الإجابات.",
        "session_name_prompt_simple": "تم استيراد {count} استمارة.\nأدخل اسماً لهذه الجلسة:",
        "backup_save_title": "حفظ نسخة احتياطية",
        "db_files_filter": "قاعدة بيانات (*.db)",
        "backup_success_msg": "تم إنشاء النسخة الاحتياطية بنجاح في:\n{path}",
        "backup_failed_msg": "فشل النسخ الاحتياطي: {error}",
        "restore_confirm_title": "تأكيد استعادة البيانات",
        "restore_confirm_msg": "تحذير: استعادة البيانات سيؤدي إلى استبدال قاعدة البيانات الحالية بالكامل.\nهل تريد الاستمرار؟",
        "choose_backup_file": "اختر ملف النسخة الاحتياطية",
        "restore_success_msg": "تمت استعادة البيانات بنجاح. سيتم إعادة تحميل الواجهة.",
        "restore_failed_msg": "فشل الاستعادة: {error}",

        # Review View
        "review_questions_title": "مراجعة الأسئلة",
        "review_questions_template": "مراجعة الأسئلة — {name}",
        "review_info_lbl": "عدد الأسئلة: {questions}  |  مقاييس ليكرت: {scales}",
        "btn_save_changes": "حفظ التعديلات",
        "btn_start_entry": "▶  بدء التفريغ",
        "btn_import_responses": "📥 استيراد إجابات رقمية",
        "th_num": "#",
        "th_question_text": "نص السؤال",
        "th_question_type": "النوع",
        "th_answers": "الإجابات",
        "btn_add_question": "+ إضافة سؤال",
        "btn_duplicate_question": "📋 نسخ السؤال",
        "btn_section_header": "📑 فاصل مقطعي",
        "tooltip_section_header": "إضافة أو تعديل أو إزالة فاصل مقطعي قبل السؤال المحدد",
        "btn_delete_selected": "حذف المحدد",
        "btn_manage_likert": "📋 إدارة مقاييس ليكرت",
        "custom_answers_picker": "— إجابات مخصصة —",
        "tooltip_edit_custom": "تعديل الإجابات المخصصة",
        "tooltip_edit_question": "تعديل السؤال ونوعه وإجاباته",
        "drag_handle_tooltip": "اسحب هذا الرمز وأفلته على السؤال المراد التفريع إليه",
        "delete_branch_tooltip": "حذف التفريع",
        "section_prefix": "فاصل مقطعي: {header}",
        "constraint_prefix": "تقييد: {subtype}",
        "subtype_text": "نص حر",
        "subtype_paragraph": "فقرة",
        "subtype_number": "رقم",
        "subtype_date": "تاريخ",
        "subtype_time": "وقت",
        "subtype_tooltip": "انقر مرتين لتعديل نوع التقييد",
        "reorder_title": "إعادة ترتيب السؤال",
        "reorder_prompt": "أدخل الرقم الجديد للسؤال (من 1 إلى {max}):",
        "duplicate_success_title": "تم النسخ",
        "duplicate_success_msg": "تم نسخ السؤال: {text}",
        "section_prompt_title": "فاصل مقطعي / عنوان الجزء",
        "section_prompt_msg": "أدخل عنوان الفاصل المقطعي الذي يسبق السؤال رقم ({num}):\n(اتركه فارغاً لإلغاء الفاصل المقطعي)",
        "select_question_first_section": "يرجى تحديد سؤال من الجدول أولاً لإضافة أو تعديل الفاصل المقطعي له.",
        "delete_questions_confirm_title": "تأكيد الحذف",
        "delete_questions_confirm_msg": "هل تريد حذف {count} سؤال محدد؟",
        "no_questions_error": "لا يمكن بدء التفريغ: القالب لا يحتوي على أي أسئلة.",
        "start_session_dialog_title": "بدء جلسة تفريغ",
        "start_session_prompt": "القالب: {template}\nعدد الأسئلة: {count}\n\nأدخل اسماً لهذه الجلسة:",
        "total_forms_prompt_title": "عدد الاستمارات",
        "total_forms_prompt_msg": "كم عدد الاستمارات الإجمالي المراد تفريغها؟",
        "branch_badge": "➔ س{target}",

        # Question Types
        "qtype_general": "عام",
        "qtype_demographic_single": "ديموغرافي (إجابة واحدة)",
        "qtype_demographic_multiple": "ديموغرافي (إجابات متعددة)",
        "qtype_likert": "ليكرت",
        "qtype_demographic_single_other": "ديموغرافي (إجابة واحدة + أخرى)",
        "qtype_unknown": "غير معروف",
        "qtype_combo_general": "عام (نص حر)",
        "qtype_combo_single": "ديموغرافي (إجابة واحدة)",
        "qtype_combo_multiple": "ديموغرافي (إجابات متعددة)",
        "qtype_combo_likert": "ليكرت (مقياس)",
        "qtype_combo_single_other": "ديموغرافي (إجابة واحدة + أخرى)",

        # Question Dialogs
        "add_question_title": "إضافة سؤال جديد",
        "edit_question_title": "تعديل السؤال: {text}",
        "question_text_lbl": "نص السؤال:",
        "section_header_optional": "فاصل مقطعي / عنوان الجزء (اختياري - يظهر قبل هذا السؤال):",
        "section_header_placeholder": "مثال: (الجزء الأول)، (المحور الثاني: تقييم الخدمات)...",
        "question_type_lbl": "نوع السؤال:",
        "question_position_lbl": "موضع السؤال (الرقم المطلوب):",
        "constraint_lbl": "تقييد الإجابة (نوع الإدخال المتوقع):",
        "constraint_opt_text": "نص حر (سطر واحد)",
        "constraint_opt_paragraph": "فقرة (نص متعدد الأسطر)",
        "constraint_opt_number": "رقم (أرقام فقط)",
        "constraint_opt_date": "تاريخ (يوم/شهر/سنة)",
        "constraint_opt_time": "وقت (ساعة:دقيقة)",
        "options_per_line": "خيارات الإجابة (واحد في كل سطر):",
        "options_last_other": "خيارات الإجابة (الخيار الأخير سيعامل كخيار مفتوح/أخرى):",
        "choose_likert_scale": "اختر مقياس ليكرت:",
        "btn_manage_scales": "⚙ إدارة المقاييس...",
        "enter_question_text_warning": "يرجى إدخال نص السؤال.",
        "enter_options_warning": "يرجى إدخال خيارات الإجابة.",
        "no_likert_scales_warning": "لا توجد مقاييس ليكرت معرفة. يرجى إضافة مقياس أولاً.",
        "default_option_1": "خيار 1",
        "default_option_2": "خيار 2",
        "default_option_other": "أخرى",

        # Likert Scales Manager Dialog
        "likert_manager_title": "إدارة مقاييس ليكرت المشتركة",
        "btn_add_scale": "+ إضافة مقياس جديد",
        "btn_edit_selected": "تعديل المحدد",
        "new_scale_dialog_title": "مقياس جديد",
        "new_scale_prompt": "اسم المقياس (مثلاً: خماسي موافقة):",
        "scale_options_count": "({count} خيارات)",
        "edit_scale_title": "تعديل مقياس: {name}",
        "scale_options_label": "خيارات المقياس (واحد في كل سطر):",
        "default_likert_agree_5": ["موافق بشدة", "موافق", "محايد", "غير موافق", "غير موافق بشدة"],

        # Entry View
        "session_header_lbl": "جلسة التفريغ",
        "session_title_lbl": "جلسة: {name}",
        "btn_save_shortcut": "Ctrl+S  حفظ",
        "btn_finish_form": "Ctrl+Q  إنهاء الاستمارة",
        "form_progress_lbl": "الاستمارة {cur} من {total}",
        "forms_panel_title": "الاستمارات",
        "form_item_label": "استمارة {num}",
        "btn_prev_question": "→ السابق",
        "btn_next_question": "التالي ←",
        "question_counter_lbl": "السؤال {cur} من {total}",
        "enter_paragraph_lbl": "أدخل الفقرة (اضغط Ctrl+Enter للحفظ أو Tab للتنقل):",
        "type_paragraph_placeholder": "اكتب الفقرة هنا...",
        "btn_confirm_next": "✔  تأكيد والتالي",
        "enter_number_lbl": "أدخل الرقم (Enter أو Tab للتالي):",
        "number_only_placeholder": "أدخل أرقاماً فقط...",
        "select_date_lbl": "اختر التاريخ (اضغط Enter للتأكيد أو Tab للتنقل):",
        "select_time_lbl": "اختر الوقت (اضغط Enter للتأكيد أو Tab للتنقل):",
        "enter_text_lbl": "أدخل الإجابة  (Enter أو Tab للتالي):",
        "type_text_placeholder": "اكتب الإجابة هنا...",
        "enter_number_ans_lbl": "اكتب رقم الإجابة (1–{count}):",
        "number_placeholder": "رقم...",
        "or_click_directly": "أو انقر على الإجابة مباشرة:",
        "multiple_hint": "اختر إجابة أو أكثر، ثم اضغط زر التأكيد:",
        "multiple_nums_lbl": "أو اكتب الأرقام مفصولة بفواصل:",
        "multiple_nums_placeholder": "مثال: 1,3",
        "type_other_placeholder": "اكتب الإجابة الحرة هنا...",
        "btn_confirm_other_next": "✔  تأكيد الإجابة والتالي",
        "form_done_msg": "تم الانتهاء من جميع أسئلة هذه الاستمارة!",
        "btn_next_form": "الانتقال للاستمارة التالية  →",
        "session_all_done_msg": "تم الانتهاء من جميع الاستمارات!",
        "session_stats_msg": "إجمالي الاستمارات: {total}\nمكتملة: {comp}",
        "btn_export_results_excel": "تصدير النتائج إلى Excel",

        # Results View
        "results_title": "النتائج المحفوظة",
        "search_results_placeholder": "ابحث باسم الجلسة أو القالب...",
        "th_session_name": "اسم الجلسة",
        "th_template": "القالب",
        "th_forms": "الاستمارات",
        "th_completed": "مكتملة",
        "btn_resume": "استئناف",
        "btn_export_excel": "تصدير Excel",
        "session_not_found": "لم يتم العثور على الجلسة.",
        "template_linked_not_found": "لم يتم العثور على القالب المرتبط.",
        "save_excel_title": "حفظ ملف Excel",
        "export_success_title": "تم التصدير",
        "export_success_msg": "تم تصدير النتائج بنجاح إلى:\n{path}",
        "export_error_title": "خطأ في التصدير",
        "delete_session_confirm_title": "تأكيد الحذف",
        "delete_session_confirm_msg": "هل تريد حذف هذه الجلسة وجميع بياناتها؟\nلا يمكن التراجع عن هذا الإجراء.",
        "delete_error_title": "خطأ في الحذف",

        # Templates View
        "templates_title": "إدارة القوالب",
        "th_template_name": "اسم القالب",
        "btn_import_template_json": "📥 استيراد قالب من ملف (.json)",
        "tooltip_import_responses_template": "استورد ملف Excel يحتوي على أرقام الإجابات وطبّق عليه هذا القالب",
        "delete_template_linked_msg": "هذا القالب مرتبط بـ {count} جلسة تفريغ:\n{names}{extra}\n\nحذف القالب سيؤدي إلى حذف هذه الجلسات وجميع بياناتها نهائياً.\nهل تريد المتابعة؟",
        "delete_template_msg": "هل تريد حذف هذا القالب وجميع أسئلته؟\nلا يمكن التراجع عن هذا الإجراء.",
        "export_template_title": "تصدير القالب",
        "json_files_filter": "ملفات القوالب (*.json)",
        "export_template_success": "✅ تم تصدير القالب بنجاح إلى:\n{path}",
        "import_template_title": "استيراد قالب",
        "import_template_error": "تعذر قراءة ملف القالب:\n{error}",
        "imported_template_name_title": "اسم القالب المستورد",
        "imported_template_name_prompt": "تأكيد أو تعديل اسم القالب:",
        "imported_template_success": "✅ تم استيراد قالب '{name}' بنجاح وحفظه في قاعدة البيانات.",
        "imported_template_save_failed": "فشل حفظ القالب المستورد:\n{error}",

        # Statistics View
        "stats_title": "إحصائيات النظام",
        "stat_total_templates": "إجمالي القوالب",
        "stat_total_sessions": "إجمالي الجلسات",
        "stat_completed_forms": "الاستمارات المفرغة",
        "stat_avg_form_time": "متوسط وقت الاستمارة",
        "seconds_unit": "{count} ثانية",
        "top_used_templates": "القوالب الأكثر استخداماً",
        "no_data_yet": "لا توجد بيانات متاحة بعد.",
        "times_unit": "{count} مرة",

        # Template Picker Dialog
        "template_picker_title": "اختر القالب",
        "template_picker_heading": "اختر القالب الذي يتوافق مع ملف الإجابات:",
        "template_picker_hint": "يجب أن تتطابق أسماء الأعمدة في ملف الإجابات مع أسماء الأسئلة في القالب.",
        "btn_select": "اختيار",

        # Excel Exporter
        "sheet_text_results": "النتائج النصية",
        "sheet_numeric_results": "النتائج الرقمية",
        "col_form_number": "رقم الاستمارة",
    },

    "en": {
        # General & App
        "app_name": "Survey Data Entry",
        "app_title": "Survey Data Entry - v{version}",
        "language_toggle": "🌐 العربية",
        "ready": "Ready",
        "saving": "⏳ Saving...",
        "saved": "✅ Saved",
        "error_saving": "❌ Error saving",
        "autosaved": "✅ Auto-saved",
        "back": "← Back",
        "cancel": "Cancel",
        "ok": "OK",
        "save": "Save",
        "edit": "Edit",
        "delete": "Delete",
        "close": "Close",
        "use": "Use",
        "export": "Export",
        "import": "Import",
        "confirm": "Confirm",
        "search": "Search:",
        "actions": "Actions",
        "warning": "Warning",
        "error": "Error",
        "success": "Success",
        "confirm_delete": "Confirm Deletion",
        "yes": "Yes",
        "no": "No",
        "created_date": "Created Date",
        "last_modified": "Last Modified",
        "questions_count": "Questions",
        "usage_count": "Times Used",

        # MainWindow Navigation
        "nav_home": "Home",
        "nav_review": "Review Questions",
        "nav_entry": "Data Entry",
        "nav_results": "Saved Results",
        "nav_templates": "Manage Templates",
        "nav_stats": "System Statistics",

        # Home View
        "start_new_session": "Start a New Entry Session",
        "card_import_excel_title": "📂  Import Excel File",
        "card_import_excel_desc": "Import an Excel file with questions\nand answers to start a new entry session",
        "card_import_excel_btn": "Import",
        "card_create_template_title": "✨  Create from Scratch",
        "card_create_template_desc": "Create a new template manually and add\nquestions and options yourself",
        "card_create_template_btn": "Create New",
        "card_open_template_title": "📋  Open Saved Template",
        "card_open_template_desc": "Select a previously saved template\nand start a new entry session",
        "card_open_template_btn": "Open Template",
        "card_resume_session_title": "▶️  Resume Session",
        "card_resume_session_desc": "Resume a previous entry session\nfrom where you left off",
        "card_resume_session_btn": "Resume",
        "card_import_responses_title": "🔢  Import Numeric Responses",
        "card_import_responses_desc": "Have an Excel file ready with numbers?\nSelect a template to convert numbers\nto response texts automatically",
        "card_import_responses_btn": "Import Responses",
        "recent_templates": "Recent Templates",
        "no_templates_yet": "No saved templates yet.",
        "questions_num": "{count} questions",
        "used_num_times": "Used {count} times",
        "btn_numeric_answers": "📥 Numeric Answers",
        "tooltip_numeric_answers": "Import Excel file with response numbers and apply this template",
        "data_maintenance": "Data Maintenance",
        "maintenance_desc": "Protect your data by creating periodic backups or restoring them.",
        "btn_backup": "📦 Backup Data",
        "btn_restore": "🔄 Restore Data",
        "create_new_template_title": "Create New Template",
        "create_new_template_prompt": "Enter a name for the new template:",
        "default_template_name": "New Template",
        "choose_excel_file": "Select Excel File",
        "excel_files_filter": "Excel Files (*.xlsx *.xls)",
        "import_error": "Import Error",
        "import_warnings_title": "Warnings",
        "import_warnings_msg": "Imported with the following warnings:\n\n{warnings}",
        "template_name_prompt_title": "Template Name",
        "template_name_prompt_msg": "Enter a name for the template:",
        "no_sessions_title": "No Sessions",
        "no_sessions_msg": "No incomplete sessions found.",
        "template_not_found": "Template not found.",
        "choose_responses_file_title": "Select Numeric Responses File — {template_name}",
        "import_responses_warning_msg": "File read with {count} warnings:\n\n{warnings}\n\nDo you want to continue?",
        "session_name_title": "Session Name",
        "session_name_prompt": "Template: {template}\nImported forms count: {count}\n\nEnter a name for this session:",
        "default_session_name": "{template} Session",
        "import_success_title": "Import Successful",
        "import_responses_success_msg": "✅ Successfully imported {count} forms\nTemplate: {template}\n\nYou can now view or export results.",
        "need_template_first": "No templates saved yet.\nYou must import a template first before importing responses.",
        "session_name_prompt_simple": "Imported {count} forms.\nEnter a name for this session:",
        "backup_save_title": "Save Backup",
        "db_files_filter": "Database (*.db)",
        "backup_success_msg": "Backup successfully created at:\n{path}",
        "backup_failed_msg": "Backup failed: {error}",
        "restore_confirm_title": "Confirm Data Restore",
        "restore_confirm_msg": "Warning: Restoring data will overwrite the current database entirely.\nDo you want to continue?",
        "choose_backup_file": "Select Backup File",
        "restore_success_msg": "Data successfully restored. The interface will now refresh.",
        "restore_failed_msg": "Restore failed: {error}",

        # Review View
        "review_questions_title": "Review Questions",
        "review_questions_template": "Review Questions — {name}",
        "review_info_lbl": "Questions: {questions}  |  Likert Scales: {scales}",
        "btn_save_changes": "Save Changes",
        "btn_start_entry": "▶  Start Entry",
        "btn_import_responses": "📥 Import Numeric Responses",
        "th_num": "#",
        "th_question_text": "Question Text",
        "th_question_type": "Type",
        "th_answers": "Answers",
        "btn_add_question": "+ Add Question",
        "btn_duplicate_question": "📋 Duplicate",
        "btn_section_header": "📑 Section Header",
        "tooltip_section_header": "Add, edit, or remove a section header preceding the selected question",
        "btn_delete_selected": "Delete Selected",
        "btn_manage_likert": "📋 Manage Likert Scales",
        "custom_answers_picker": "— Custom Answers —",
        "tooltip_edit_custom": "Edit custom answers",
        "tooltip_edit_question": "Edit question text, type, and answers",
        "drag_handle_tooltip": "Drag and drop this icon onto target question for branching",
        "delete_branch_tooltip": "Delete branching rule",
        "section_prefix": "Section: {header}",
        "constraint_prefix": "Constraint: {subtype}",
        "subtype_text": "Free Text",
        "subtype_paragraph": "Paragraph",
        "subtype_number": "Number",
        "subtype_date": "Date",
        "subtype_time": "Time",
        "subtype_tooltip": "Double-click to edit input constraint",
        "reorder_title": "Reorder Question",
        "reorder_prompt": "Enter the new question number (1 to {max}):",
        "duplicate_success_title": "Duplicated",
        "duplicate_success_msg": "Question duplicated: {text}",
        "section_prompt_title": "Section Header / Part Title",
        "section_prompt_msg": "Enter section header preceding question #{num}:\n(leave blank to remove section header)",
        "select_question_first_section": "Please select a question from the table first to set its section header.",
        "delete_questions_confirm_title": "Confirm Deletion",
        "delete_questions_confirm_msg": "Are you sure you want to delete {count} selected question(s)?",
        "no_questions_error": "Cannot start entry: Template has no questions.",
        "start_session_dialog_title": "Start Data Entry Session",
        "start_session_prompt": "Template: {template}\nQuestions count: {count}\n\nEnter a name for this session:",
        "total_forms_prompt_title": "Total Forms",
        "total_forms_prompt_msg": "How many total forms do you want to enter?",
        "branch_badge": "➔ Q{target}",

        # Question Types
        "qtype_general": "General",
        "qtype_demographic_single": "Demographic (Single Choice)",
        "qtype_demographic_multiple": "Demographic (Multiple Choice)",
        "qtype_likert": "Likert",
        "qtype_demographic_single_other": "Demographic (Single + Other)",
        "qtype_unknown": "Unknown",
        "qtype_combo_general": "General (Free Text)",
        "qtype_combo_single": "Demographic (Single Choice)",
        "qtype_combo_multiple": "Demographic (Multiple Choice)",
        "qtype_combo_likert": "Likert (Scale)",
        "qtype_combo_single_other": "Demographic (Single + Other)",

        # Question Dialogs
        "add_question_title": "Add New Question",
        "edit_question_title": "Edit Question: {text}",
        "question_text_lbl": "Question Text:",
        "section_header_optional": "Section Header (optional - appears before this question):",
        "section_header_placeholder": "e.g., (Part One), (Section 2: Service Evaluation)...",
        "question_type_lbl": "Question Type:",
        "question_position_lbl": "Question Position (Desired Number):",
        "constraint_lbl": "Input Constraint (Expected Type):",
        "constraint_opt_text": "Free Text (Single Line)",
        "constraint_opt_paragraph": "Paragraph (Multi-line Text)",
        "constraint_opt_number": "Number (Digits only)",
        "constraint_opt_date": "Date (YYYY-MM-DD)",
        "constraint_opt_time": "Time (HH:MM)",
        "options_per_line": "Answer options (one per line):",
        "options_last_other": "Answer options (last option will be treated as other/open-ended):",
        "choose_likert_scale": "Select Likert Scale:",
        "btn_manage_scales": "⚙ Manage Scales...",
        "enter_question_text_warning": "Please enter question text.",
        "enter_options_warning": "Please enter answer options.",
        "no_likert_scales_warning": "No Likert scales defined. Please add a scale first.",
        "default_option_1": "Option 1",
        "default_option_2": "Option 2",
        "default_option_other": "Other",

        # Likert Scales Manager Dialog
        "likert_manager_title": "Manage Shared Likert Scales",
        "btn_add_scale": "+ Add New Scale",
        "btn_edit_selected": "Edit Selected",
        "new_scale_dialog_title": "New Scale",
        "new_scale_prompt": "Scale name (e.g., 5-Point Agreement):",
        "scale_options_count": "({count} options)",
        "edit_scale_title": "Edit Scale: {name}",
        "scale_options_label": "Scale options (one per line):",
        "default_likert_agree_5": ["Strongly Agree", "Agree", "Neutral", "Disagree", "Strongly Disagree"],

        # Entry View
        "session_header_lbl": "Entry Session",
        "session_title_lbl": "Session: {name}",
        "btn_save_shortcut": "Ctrl+S  Save",
        "btn_finish_form": "Ctrl+Q  Finish Form",
        "form_progress_lbl": "Form {cur} of {total}",
        "forms_panel_title": "Forms",
        "form_item_label": "Form {num}",
        "btn_prev_question": "← Previous",
        "btn_next_question": "Next →",
        "question_counter_lbl": "Question {cur} of {total}",
        "enter_paragraph_lbl": "Enter paragraph (Ctrl+Enter to save, Tab to navigate):",
        "type_paragraph_placeholder": "Type paragraph here...",
        "btn_confirm_next": "✔ Confirm & Next",
        "enter_number_lbl": "Enter number (Enter or Tab for next):",
        "number_only_placeholder": "Numbers only...",
        "select_date_lbl": "Select date (Enter to confirm, Tab to navigate):",
        "select_time_lbl": "Select time (Enter to confirm, Tab to navigate):",
        "enter_text_lbl": "Enter answer (Enter or Tab for next):",
        "type_text_placeholder": "Type answer here...",
        "enter_number_ans_lbl": "Enter answer number (1–{count}):",
        "number_placeholder": "Num...",
        "or_click_directly": "Or click the answer directly:",
        "multiple_hint": "Select one or more answers, then click confirm:",
        "multiple_nums_lbl": "Or type numbers separated by commas:",
        "multiple_nums_placeholder": "e.g., 1,3",
        "type_other_placeholder": "Type custom answer here...",
        "btn_confirm_other_next": "✔ Confirm Answer & Next",
        "form_done_msg": "All questions in this form are completed!",
        "btn_next_form": "Proceed to Next Form →",
        "session_all_done_msg": "All forms are completed!",
        "session_stats_msg": "Total forms: {total}\nCompleted: {comp}",
        "btn_export_results_excel": "Export Results to Excel",

        # Results View
        "results_title": "Saved Results",
        "search_results_placeholder": "Search by session or template name...",
        "th_session_name": "Session Name",
        "th_template": "Template",
        "th_forms": "Forms",
        "th_completed": "Completed",
        "btn_resume": "Resume",
        "btn_export_excel": "Export Excel",
        "session_not_found": "Session not found.",
        "template_linked_not_found": "Linked template not found.",
        "save_excel_title": "Save Excel File",
        "export_success_title": "Exported",
        "export_success_msg": "Results successfully exported to:\n{path}",
        "export_error_title": "Export Error",
        "delete_session_confirm_title": "Confirm Deletion",
        "delete_session_confirm_msg": "Do you want to delete this session and all its data?\nThis action cannot be undone.",
        "delete_error_title": "Deletion Error",

        # Templates View
        "templates_title": "Manage Templates",
        "th_template_name": "Template Name",
        "btn_import_template_json": "📥 Import Template from (.json)",
        "tooltip_import_responses_template": "Import Excel file with response numbers and apply this template",
        "delete_template_linked_msg": "This template is linked to {count} entry session(s):\n{names}{extra}\n\nDeleting the template will permanently delete these sessions and all their data.\nDo you want to proceed?",
        "delete_template_msg": "Do you want to delete this template and all its questions?\nThis action cannot be undone.",
        "export_template_title": "Export Template",
        "json_files_filter": "Template Files (*.json)",
        "export_template_success": "✅ Template successfully exported to:\n{path}",
        "import_template_title": "Import Template",
        "import_template_error": "Could not read template file:\n{error}",
        "imported_template_name_title": "Imported Template Name",
        "imported_template_name_prompt": "Confirm or edit template name:",
        "imported_template_success": "✅ Template '{name}' successfully imported and saved.",
        "imported_template_save_failed": "Failed to save imported template:\n{error}",

        # Statistics View
        "stats_title": "System Statistics",
        "stat_total_templates": "Total Templates",
        "stat_total_sessions": "Total Sessions",
        "stat_completed_forms": "Completed Forms",
        "stat_avg_form_time": "Avg Form Time",
        "seconds_unit": "{count} seconds",
        "top_used_templates": "Most Used Templates",
        "no_data_yet": "No data available yet.",
        "times_unit": "{count} times",

        # Template Picker Dialog
        "template_picker_title": "Select Template",
        "template_picker_heading": "Select the template matching the responses file:",
        "template_picker_hint": "Column headers in the responses file must match question texts in the template.",
        "btn_select": "Select",

        # Excel Exporter
        "sheet_text_results": "Text Results",
        "sheet_numeric_results": "Numeric Results",
        "col_form_number": "Form #",
    }
}


def get_language() -> str:
    """الحصول على رمز اللغة الحالية ('ar' أو 'en')"""
    return _CURRENT_LANGUAGE


def is_rtl() -> bool:
    """هل الاتجاه الحالي من اليمين إلى اليسار (عربي)"""
    return _CURRENT_LANGUAGE == "ar"


def get_layout_direction() -> Qt.LayoutDirection:
    """الحصول على اتجاه التخطيط المناسب لـ Qt"""
    return Qt.LayoutDirection.RightToLeft if is_rtl() else Qt.LayoutDirection.LeftToRight


def get_text_alignment() -> Qt.AlignmentFlag:
    """الحصول على محاذاة النصوص الافتراضية"""
    return Qt.AlignmentFlag.AlignRight if is_rtl() else Qt.AlignmentFlag.AlignLeft


def tr(key: str, **kwargs) -> str:
    """
    ترجمة مفتاح نصي حسب اللغة النشطة حالياً، مع دعم استبدال المتغيرات kwargs.
    """
    lang_dict = TRANSLATIONS.get(_CURRENT_LANGUAGE, TRANSLATIONS["ar"])
    text = lang_dict.get(key)
    if text is None:
        # محاولة البحث في اللغة الافتراضية (العربية)
        text = TRANSLATIONS["ar"].get(key, key)
    
    if kwargs and isinstance(text, str):
        try:
            return text.format(**kwargs)
        except Exception:
            return text
    return text


def set_language(lang: str, db=None) -> None:
    """
    تغيير لغة التطبيق وتحديث قاعدة البيانات وإشعار المستمعين.
    """
    global _CURRENT_LANGUAGE
    if lang not in TRANSLATIONS:
        lang = "ar"
    _CURRENT_LANGUAGE = lang

    if db is not None:
        try:
            db.set_setting("language", lang)
        except Exception:
            pass

    for listener in _LISTENERS:
        try:
            listener(lang)
        except Exception as e:
            print(f"Error in language change listener: {e}")


def register_listener(callback: Callable[[str], None]) -> None:
    """تسجيل دالة استماع عند تغيير اللغة"""
    if callback not in _LISTENERS:
        _LISTENERS.append(callback)


def unregister_listener(callback: Callable[[str], None]) -> None:
    """إلغاء تسجيل دالة الاستماع"""
    if callback in _LISTENERS:
        _LISTENERS.remove(callback)
