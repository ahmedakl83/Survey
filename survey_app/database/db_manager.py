import sqlite3
import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from models.question import Question, QuestionType
from models.template import Template, LikertScale
from models.session import Session, FormResponse
import shutil


class DatabaseManager:
    def __init__(self):
        app_data = Path(os.environ.get("APPDATA", ".")) / "SurveyApp"
        app_data.mkdir(parents=True, exist_ok=True)
        self.db_path = app_data / "survey_app.db"
        self._conn: Optional[sqlite3.Connection] = None

    def _get_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA foreign_keys=ON")
        return self._conn

    def initialize(self):
        conn = self._get_conn()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS templates (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                name        TEXT NOT NULL,
                created_at  TEXT NOT NULL,
                updated_at  TEXT NOT NULL,
                use_count   INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS likert_scales (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                template_id INTEGER NOT NULL REFERENCES templates(id) ON DELETE CASCADE,
                name        TEXT NOT NULL,
                answers     TEXT NOT NULL  -- JSON array
            );

            CREATE TABLE IF NOT EXISTS questions (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                template_id     INTEGER NOT NULL REFERENCES templates(id) ON DELETE CASCADE,
                column_index    INTEGER NOT NULL,
                text            TEXT NOT NULL,
                question_type   INTEGER NOT NULL,
                answers         TEXT NOT NULL DEFAULT '[]',  -- JSON array
                likert_scale_id INTEGER DEFAULT 0,
                branching       TEXT DEFAULT '{}',           -- JSON dictionary of {answer: target_column_index}
                section_header  TEXT DEFAULT ''              -- عنوان الفاصل المقطعي إن وجد
            );

            CREATE TABLE IF NOT EXISTS sessions (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                template_id     INTEGER NOT NULL REFERENCES templates(id),
                name            TEXT NOT NULL,
                created_at      TEXT NOT NULL,
                updated_at      TEXT NOT NULL,
                total_forms     INTEGER NOT NULL DEFAULT 0,
                current_form_index    INTEGER DEFAULT 0,
                current_question_index INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS form_responses (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id  INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
                form_index  INTEGER NOT NULL,
                answers     TEXT NOT NULL DEFAULT '{}',  -- JSON {question_id: answer}
                is_complete INTEGER DEFAULT 0,
                started_at  TEXT,
                completed_at TEXT,
                duration_seconds INTEGER DEFAULT 0,
                UNIQUE(session_id, form_index)
            );

            CREATE TABLE IF NOT EXISTS app_settings (
                key   TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
        """)
        conn.commit()

        # ترقية تلقائية: إضافة عمود branching إن لم يكن موجوداً لقواعد البيانات السابقة
        try:
            conn.execute("SELECT branching FROM questions LIMIT 1")
        except sqlite3.OperationalError:
            try:
                conn.execute("ALTER TABLE questions ADD COLUMN branching TEXT DEFAULT '{}'")
                conn.commit()
            except Exception:
                pass

        # ترقية تلقائية: إضافة عمود section_header إن لم يكن موجوداً لقواعد البيانات السابقة
        try:
            conn.execute("SELECT section_header FROM questions LIMIT 1")
        except sqlite3.OperationalError:
            try:
                conn.execute("ALTER TABLE questions ADD COLUMN section_header TEXT DEFAULT ''")
                conn.commit()
            except Exception:
                pass

    # ─── Templates ────────────────────────────────────────────────────────────

    def save_template(self, template: Template) -> int:
        conn = self._get_conn()
        now = datetime.now().isoformat()
        cur = conn.execute(
            "INSERT INTO templates (name, created_at, updated_at, use_count) VALUES (?,?,?,?)",
            (template.name, now, now, 0)
        )
        template_id = cur.lastrowid

        for scale in template.likert_scales:
            sc = conn.execute(
                "INSERT INTO likert_scales (template_id, name, answers) VALUES (?,?,?)",
                (template_id, scale.name, json.dumps(scale.answers, ensure_ascii=False))
            )
            scale.id = sc.lastrowid

        for q in template.questions:
            likert_id = q.likert_scale_id
            if likert_id == 0 and hasattr(q, '_likert_scale_ref') and q._likert_scale_ref:
                likert_id = q._likert_scale_ref.id
                
            branching_data = {}
            if hasattr(q, "branching_rules") and q.branching_rules:
                for ans, target_q in q.branching_rules.items():
                    if isinstance(target_q, Question):
                        branching_data[ans] = target_q.column_index
                    elif isinstance(target_q, int):
                        branching_data[ans] = target_q

            cur = conn.execute(
                """INSERT INTO questions
                   (template_id, column_index, text, question_type, answers, likert_scale_id, branching, section_header)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (template_id, q.column_index, q.text, int(q.question_type),
                 json.dumps(q.answers, ensure_ascii=False), likert_id,
                 json.dumps(branching_data, ensure_ascii=False),
                 getattr(q, 'section_header', '') or "")
            )
            q.id = cur.lastrowid
        conn.commit()
        return template_id

    def update_template(self, template: Template):
        conn = self._get_conn()
        now = datetime.now().isoformat()
        conn.execute(
            "UPDATE templates SET name=?, updated_at=? WHERE id=?",
            (template.name, now, template.id)
        )
        # حذف وإعادة إدراج الأسئلة والمقاييس
        conn.execute("DELETE FROM questions WHERE template_id=?", (template.id,))
        conn.execute("DELETE FROM likert_scales WHERE template_id=?", (template.id,))

        for scale in template.likert_scales:
            sc = conn.execute(
                "INSERT INTO likert_scales (template_id, name, answers) VALUES (?,?,?)",
                (template.id, scale.name, json.dumps(scale.answers, ensure_ascii=False))
            )
            scale.id = sc.lastrowid

        for q in template.questions:
            likert_id = q.likert_scale_id
            if likert_id == 0 and hasattr(q, '_likert_scale_ref') and q._likert_scale_ref:
                likert_id = q._likert_scale_ref.id

            branching_data = {}
            if hasattr(q, "branching_rules") and q.branching_rules:
                for ans, target_q in q.branching_rules.items():
                    if isinstance(target_q, Question):
                        branching_data[ans] = target_q.column_index
                    elif isinstance(target_q, int):
                        branching_data[ans] = target_q

            cur = conn.execute(
                """INSERT INTO questions
                   (template_id, column_index, text, question_type, answers, likert_scale_id, branching, section_header)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (template.id, q.column_index, q.text, int(q.question_type),
                 json.dumps(q.answers, ensure_ascii=False), likert_id,
                 json.dumps(branching_data, ensure_ascii=False),
                 getattr(q, 'section_header', '') or "")
            )
            q.id = cur.lastrowid
        conn.commit()

    def load_all_templates(self) -> List[Template]:
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM templates ORDER BY updated_at DESC"
        ).fetchall()
        templates = []
        for row in rows:
            t = Template(
                id=row["id"], name=row["name"],
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
                use_count=row["use_count"]
            )
            t.questions = self._load_questions(t.id)
            t.likert_scales = self._load_likert_scales(t.id)
            t.question_count = len(t.questions)
            templates.append(t)
        return templates

    def load_template(self, template_id: int) -> Optional[Template]:
        conn = self._get_conn()
        row = conn.execute(
            "SELECT * FROM templates WHERE id=?", (template_id,)
        ).fetchone()
        if not row:
            return None
        t = Template(
            id=row["id"], name=row["name"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            use_count=row["use_count"]
        )
        t.questions = self._load_questions(t.id)
        t.likert_scales = self._load_likert_scales(t.id)
        t.question_count = len(t.questions)
        return t

    def get_sessions_for_template(self, template_id: int) -> List[Session]:
        """إرجاع قائمة الجلسات المرتبطة بقالب معين"""
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT id, name FROM sessions WHERE template_id=?", (template_id,)
        ).fetchall()
        return [Session(id=row["id"], name=row["name"], template_id=template_id) for row in rows]

    def delete_template(self, template_id: int):
        conn = self._get_conn()
        try:
            # حذف الجلسات المرتبطة أولاً (وبيانات الاستمارات تُحذف تلقائياً بـ CASCADE)
            conn.execute("DELETE FROM sessions WHERE template_id=?", (template_id,))
            conn.execute("DELETE FROM templates WHERE id=?", (template_id,))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise RuntimeError(f"فشل حذف القالب: {e}")

    def increment_template_use(self, template_id: int):
        conn = self._get_conn()
        conn.execute(
            "UPDATE templates SET use_count = use_count + 1 WHERE id=?",
            (template_id,)
        )
        conn.commit()

    def _load_questions(self, template_id: int) -> List[Question]:
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM questions WHERE template_id=? ORDER BY column_index",
            (template_id,)
        ).fetchall()
        questions = []
        for row in rows:
            branching_val = "{}"
            if "branching" in row.keys():
                branching_val = row["branching"] or "{}"

            sec_header = ""
            if "section_header" in row.keys():
                sec_header = row["section_header"] or ""

            q = Question(
                id=row["id"],
                template_id=template_id,
                column_index=row["column_index"],
                text=row["text"],
                question_type=QuestionType(row["question_type"]),
                answers=json.loads(row["answers"]),
                likert_scale_id=row["likert_scale_id"] or 0,
                section_header=sec_header
            )
            q._raw_branching = json.loads(branching_val) if branching_val else {}
            questions.append(q)

        # ربط كائنات الأسئلة المستهدفة
        for q in questions:
            q.branching_rules = {}
            if hasattr(q, "_raw_branching"):
                for ans, target_idx in q._raw_branching.items():
                    target_q = next((t for t in questions if t.column_index == int(target_idx)), None)
                    if target_q:
                        q.branching_rules[ans] = target_q

        return questions

    def _load_likert_scales(self, template_id: int) -> List[LikertScale]:
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM likert_scales WHERE template_id=?", (template_id,)
        ).fetchall()
        return [
            LikertScale(
                id=row["id"], template_id=template_id,
                name=row["name"], answers=json.loads(row["answers"])
            )
            for row in rows
        ]

    # ─── Sessions ─────────────────────────────────────────────────────────────

    def save_session(self, session: Session) -> int:
        conn = self._get_conn()
        now = datetime.now().isoformat()
        cur = conn.execute(
            """INSERT INTO sessions
               (template_id, name, created_at, updated_at, total_forms,
                current_form_index, current_question_index)
               VALUES (?,?,?,?,?,?,?)""",
            (session.template_id, session.name, now, now,
             session.total_forms, session.current_form_index,
             session.current_question_index)
        )
        session.id = cur.lastrowid
        self._save_form_responses(session)
        conn.commit()
        return session.id

    def update_session(self, session: Session):
        conn = self._get_conn()
        now = datetime.now().isoformat()
        conn.execute(
            """UPDATE sessions SET updated_at=?, current_form_index=?,
               current_question_index=? WHERE id=?""",
            (now, session.current_form_index,
             session.current_question_index, session.id)
        )
        self._save_form_responses(session)
        conn.commit()

    def _save_form_responses(self, session: Session):
        conn = self._get_conn()
        for form in session.forms:
            conn.execute(
                """INSERT INTO form_responses
                   (session_id, form_index, answers, is_complete,
                    started_at, completed_at, duration_seconds)
                   VALUES (?,?,?,?,?,?,?)
                   ON CONFLICT(session_id, form_index) DO UPDATE SET
                   answers=excluded.answers, is_complete=excluded.is_complete,
                   started_at=excluded.started_at, completed_at=excluded.completed_at,
                   duration_seconds=excluded.duration_seconds""",
                (session.id, form.form_index,
                 json.dumps(
                     {str(k): v for k, v in form.answers.items()},
                     ensure_ascii=False
                 ),
                 1 if form.is_complete else 0,
                 form.started_at.isoformat() if form.started_at else None,
                 form.completed_at.isoformat() if form.completed_at else None,
                 form.duration_seconds)
            )

    def load_all_sessions(self) -> List[Session]:
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM sessions ORDER BY updated_at DESC"
        ).fetchall()
        sessions = []
        for row in rows:
            s = Session(
                id=row["id"], template_id=row["template_id"],
                name=row["name"],
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
                total_forms=row["total_forms"],
                current_form_index=row["current_form_index"],
                current_question_index=row["current_question_index"]
            )
            s.forms = self._load_form_responses(s.id, s.total_forms)
            sessions.append(s)
        return sessions

    def load_session(self, session_id: int) -> Optional[Session]:
        conn = self._get_conn()
        row = conn.execute(
            "SELECT * FROM sessions WHERE id=?", (session_id,)
        ).fetchone()
        if not row:
            return None
        s = Session(
            id=row["id"], template_id=row["template_id"],
            name=row["name"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            total_forms=row["total_forms"],
            current_form_index=row["current_form_index"],
            current_question_index=row["current_question_index"]
        )
        s.forms = self._load_form_responses(s.id, s.total_forms)
        return s

    def delete_session(self, session_id: int):
        conn = self._get_conn()
        conn.execute("DELETE FROM sessions WHERE id=?", (session_id,))
        conn.commit()

    def _load_form_responses(self, session_id: int, total: int) -> List[FormResponse]:
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM form_responses WHERE session_id=? ORDER BY form_index",
            (session_id,)
        ).fetchall()
        existing = {row["form_index"]: row for row in rows}
        forms = []
        for i in range(total):
            if i in existing:
                row = existing[i]
                raw = json.loads(row["answers"])
                answers = {int(k): v for k, v in raw.items()}
                f = FormResponse(
                    form_index=i,
                    answers=answers,
                    is_complete=bool(row["is_complete"]),
                    started_at=datetime.fromisoformat(row["started_at"]) if row["started_at"] else None,
                    completed_at=datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None,
                    duration_seconds=row["duration_seconds"]
                )
            else:
                f = FormResponse(form_index=i)
            forms.append(f)
        return forms

    # ─── Statistics ───────────────────────────────────────────────────────────

    def get_overall_stats(self) -> dict:
        """إحضار إحصائيات عامة للنظام"""
        conn = self._get_conn()
        stats = {}

        # عدد القوالب
        stats["templates_count"] = conn.execute("SELECT COUNT(*) FROM templates").fetchone()[0]

        # عدد الجلسات
        stats["sessions_count"] = conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]

        # إجمالي الاستمارات
        stats["total_forms"] = conn.execute("SELECT SUM(total_forms) FROM sessions").fetchone()[0] or 0

        # الاستمارات المكتملة
        stats["completed_forms"] = conn.execute(
            "SELECT COUNT(*) FROM form_responses WHERE is_complete = 1"
        ).fetchone()[0]

        # متوسط الوقت لكل استمارة (بالثواني)
        avg_time = conn.execute(
            "SELECT AVG(duration_seconds) FROM form_responses WHERE is_complete = 1 AND duration_seconds > 0"
        ).fetchone()[0]
        stats["avg_form_time"] = round(avg_time, 1) if avg_time else 0

        # القوالب الأكثر استخداماً
        top_templates = conn.execute(
            "SELECT name, use_count FROM templates ORDER BY use_count DESC LIMIT 5"
        ).fetchall()
        stats["top_templates"] = [{"name": r["name"], "count": r["use_count"]} for r in top_templates]

        return stats

    # ─── Backup & Restore ─────────────────────────────────────────────────────

    def backup_database(self, target_path: str):
        """نسخ ملف قاعدة البيانات إلى المسار المحدد"""
        try:
            # التأكد من كتابة كافة البيانات من الـ WAL إلى الملف الرئيسي
            self._get_conn().execute("PRAGMA wal_checkpoint(FULL)")
            shutil.copy2(str(self.db_path), target_path)
        except Exception as e:
            raise RuntimeError(f"فشل النسخ الاحتياطي: {e}")

    def restore_database(self, source_path: str):
        """استعادة قاعدة البيانات من ملف خارجي"""
        try:
            if self._conn:
                self._conn.close()
                self._conn = None

            shutil.copy2(source_path, str(self.db_path))
        except Exception as e:
            raise RuntimeError(f"فشل استعادة البيانات: {e}")

    # ─── Settings ─────────────────────────────────────────────────────────────

    def get_setting(self, key: str, default: str = "") -> str:
        conn = self._get_conn()
        row = conn.execute("SELECT value FROM app_settings WHERE key = ?", (key,)).fetchone()
        if row:
            return row["value"]
        return default

    def set_setting(self, key: str, value: str):
        conn = self._get_conn()
        conn.execute(
            "INSERT INTO app_settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, value)
        )
        conn.commit()

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None
