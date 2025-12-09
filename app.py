from __future__ import annotations

import base64
import json
import os
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from flask import Flask, jsonify, render_template, request, redirect, session, url_for, current_app
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text, func
from sqlalchemy.exc import OperationalError
from werkzeug.security import check_password_hash, generate_password_hash


BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DB_FILE = DATA_DIR / "app.db"
PROJECTS_FILE = DATA_DIR / "projects.json"
STUDENT_UPLOAD_DIR = BASE_DIR / "static" / "uploads" / "students"

DEFAULT_PROJECTS: List[Dict[str, Any]] = [
    {
        "title": "Smart Campus Energy Dashboard",
        "category": "IoT",
        "description": "Building a live dashboard to track campus energy usage.",
        "team_size": 5,
    },
    {
        "title": "AI Study Buddy",
        "category": "AI",
        "description": "Lightweight tutor bot that answers course questions.",
        "team_size": 4,
    },
]

db = SQLAlchemy()


class Student(db.Model):
    __tablename__ = "students"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    email = db.Column(db.String(200), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    photo_url = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def set_password(self, raw: str) -> None:
        self.password_hash = generate_password_hash(raw)

    def check_password(self, raw: str) -> bool:
        return check_password_hash(self.password_hash, raw)


class Mentor(db.Model):
    __tablename__ = "mentors"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    field = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    research_area = db.Column(db.String(120), default="")
    photo = db.Column(db.String(500), default="")
    email = db.Column(db.String(200))
    access_code_hash = db.Column(db.String(255))
    status = db.Column(db.String(20), default="pending")  # pending/approved/rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    workshop_title = db.Column(db.String(200), default="")
    workshop_description = db.Column(db.Text, default="")
    workshop_image = db.Column(db.String(500), default="")
    workshop_links = db.Column(db.Text, default="")
    requests = db.relationship("JoinRequest", back_populates="mentor", lazy="dynamic")

    def to_dict(self) -> Dict[str, Any]:
        pending = self.requests.filter_by(status="pending").count() if self.requests else 0
        total = self.requests.count() if self.requests else 0
        return {
            "id": self.id,
            "name": self.name,
            "field": self.field,
            "description": self.description,
            "research_area": self.research_area,
            "photo": self.photo,
            "status": self.status,
            "pending_requests": pending,
            "total_requests": total,
            "created_at": self.created_at.isoformat(),
            "workshop_title": self.workshop_title,
            "workshop_description": self.workshop_description,
            "workshop_image": self.workshop_image,
            "workshop_links": self.workshop_links,
        }


class Project(db.Model):
    __tablename__ = "projects"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(120), default="")
    description = db.Column(db.Text, default="")
    team_size = db.Column(db.Integer)
    mentor_id = db.Column(db.Integer, db.ForeignKey("mentors.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    mentor = db.relationship("Mentor", backref="projects")
    requests = db.relationship("JoinRequest", back_populates="project", lazy="dynamic")

    def to_dict(self) -> Dict[str, Any]:
        base = {
            "id": self.id,
            "title": self.title,
            "category": self.category,
            "description": self.description,
            "team_size": self.team_size,
            "mentor_id": self.mentor_id,
            "created_at": self.created_at.isoformat(),
        }
        if self.mentor:
            base["mentor_name"] = self.mentor.name
        return base


class JoinRequest(db.Model):
    __tablename__ = "requests"

    id = db.Column(db.Integer, primary_key=True)
    request_type = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default="pending")
    mentor_id = db.Column(db.Integer, db.ForeignKey("mentors.id"))
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"))
    mentor_name = db.Column(db.String(200))
    project_title = db.Column(db.String(200))
    student_name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(120))
    faculty = db.Column(db.String(120))
    skills = db.Column(db.String(200))
    availability = db.Column(db.String(40))
    contact = db.Column(db.String(200))
    interest = db.Column(db.Text)
    intro = db.Column(db.Text)
    message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    mentor = db.relationship("Mentor", back_populates="requests")
    project = db.relationship("Project", back_populates="requests")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "request_type": self.request_type,
            "status": self.status,
            "mentor_id": self.mentor_id,
            "mentor_name": self.mentor_name,
            "project_title": self.project_title,
            "student_name": self.student_name,
            "email": self.email,
            "role": self.role,
            "faculty": self.faculty,
            "skills": self.skills,
            "availability": self.availability,
            "contact": self.contact,
            "interest": self.interest,
            "intro": self.intro,
            "message": self.message,
            "project_id": self.project_id,
            "created_at": self.created_at.isoformat(),
        }


def load_seed_data(path: Path, fallback: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Load seed data from JSON if present; otherwise return fallback."""
    if path.exists():
        try:
            data = json.loads(path.read_text())
            if isinstance(data, list):
                return data
        except Exception:
            pass
    return fallback


def seed_defaults() -> None:
    """Bootstrap the SQLite database with starter projects (mentors start empty)."""
    created = False
    if Project.query.count() == 0:
        projects = []
        for record in load_seed_data(PROJECTS_FILE, DEFAULT_PROJECTS):
            team_size = record.get("team_size")
            try:
                team_size_val = int(team_size) if team_size is not None else None
            except (TypeError, ValueError):
                team_size_val = None
            projects.append(
                Project(
                    title=record.get("title", ""),
                    category=record.get("category", ""),
                    description=record.get("description", ""),
                    team_size=team_size_val,
                )
            )
        db.session.add_all(projects)
        created = True

    if created:
        db.session.commit()


def project_slot_summary() -> Dict[int, Dict[str, int]]:
    """
    Return mapping of project_id -> {"accepted": int}
    Only counts accepted requests.
    """
    rows = db.session.execute(
        text(
            "SELECT project_id, COUNT(*) as c FROM requests "
            "WHERE status = 'accepted' AND project_id IS NOT NULL GROUP BY project_id"
        )
    ).fetchall()
    return {int(row[0]): {"accepted": int(row[1])} for row in rows if row[0] is not None}


def project_capacity(project: Project) -> int:
    """Return capacity for a project, defaulting to 5 if not set."""
    try:
        if project.team_size:
            return int(project.team_size)
    except Exception:
        pass
    return 5


def normalize_email(email: str) -> str:
    return (email or "").strip().lower()


def student_requests(email: str) -> List[JoinRequest]:
    return (
        JoinRequest.query.filter(func.lower(JoinRequest.email) == normalize_email(email))
        .order_by(JoinRequest.created_at.desc())
        .all()
    )


def save_student_photo(photo_data: str) -> str:
    """Save base64-encoded photo to static/uploads/students and return relative URL."""
    header, b64data = photo_data.split(",", 1) if "," in photo_data else ("", photo_data)
    raw = base64.b64decode(b64data)
    STUDENT_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4().hex}.png"
    dest = STUDENT_UPLOAD_DIR / filename
    with open(dest, "wb") as f:
        f.write(raw)
    return f"/static/uploads/students/{filename}"


def init_database(app: Flask) -> None:
    """Configure and initialize the SQLite database."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_FILE}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    # Give SQLite more room to wait for locks; helps when DB is briefly open elsewhere.
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"connect_args": {"timeout": 10}}
    db.init_app(app)

    with app.app_context():
        # Soften locking by using WAL + busy timeout, with a short retry loop.
        for attempt in range(3):
            try:
                db.session.execute(text("PRAGMA journal_mode=WAL"))
                db.session.execute(text("PRAGMA busy_timeout = 5000"))
                db.session.commit()
                break
            except OperationalError:
                db.session.rollback()
                time.sleep(1.0)
        else:
            raise
        for attempt in range(3):
            try:
                db.create_all()
                upgrade_schema()
                seed_defaults()
                break
            except OperationalError:
                db.session.rollback()
                time.sleep(1.0)
        else:
            raise


def add_column_if_missing(table: str, column: str, ddl: str) -> None:
    """Add a column to an existing SQLite table if it does not exist."""
    existing = {row[1] for row in db.session.execute(text(f"PRAGMA table_info({table})"))}
    if column not in existing:
        db.session.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}"))
        db.session.commit()


def upgrade_schema() -> None:
    """Apply lightweight schema upgrades for new features without migrations."""
    add_column_if_missing("mentors", "email", "TEXT")
    add_column_if_missing("mentors", "access_code_hash", "TEXT")
    add_column_if_missing("mentors", "status", "TEXT DEFAULT 'pending'")
    add_column_if_missing("mentors", "workshop_title", "TEXT")
    add_column_if_missing("mentors", "workshop_description", "TEXT")
    add_column_if_missing("mentors", "workshop_image", "TEXT")
    add_column_if_missing("mentors", "workshop_links", "TEXT")
    add_column_if_missing("requests", "status", "TEXT DEFAULT 'pending'")
    add_column_if_missing("requests", "mentor_id", "INTEGER")
    add_column_if_missing("requests", "project_id", "INTEGER")
    add_column_if_missing("projects", "mentor_id", "INTEGER")

    # backfill null statuses to pending for older rows
    db.session.execute(text("UPDATE requests SET status = 'pending' WHERE status IS NULL"))
    db.session.execute(text("UPDATE mentors SET status = 'pending' WHERE status IS NULL OR status = ''"))
    db.session.commit()


def authenticate_mentor(email: str, access_code: str) -> Mentor | None:
    """Return mentor if credentials are valid."""
    if not (email and access_code):
        return None
    mentor = Mentor.query.filter(Mentor.email == email.lower()).first()
    if (
        mentor
        and mentor.access_code_hash
        and mentor.status == "approved"
        and check_password_hash(mentor.access_code_hash, access_code)
    ):
        return mentor
    return None


def create_app() -> Flask:
    """Application factory."""
    app = Flask(__name__)
    app.secret_key = os.getenv("FLASK_SECRET_KEY", "mmu-stem-secret")
    app.config["ADMIN_PASSWORD"] = os.getenv("ADMIN_PASSWORD", "admin123")
    init_database(app)

    # -----------------
    # PAGE ROUTES
    # -----------------
    @app.route("/")
    def home() -> str:
        """
        Main MMU page:
        - Overview, vision/mission, history
        - Live stats: mentors & projects (from SQLite database)
        """
        return render_template(
            "index.html",
            mentor_count=Mentor.query.filter_by(status="approved").count(),
            project_count=Project.query.count(),
        )

    @app.route("/stem")
    def stem_page() -> str:
        """
        STEM portal page:
        - Ebee image
        - Find a mentor, Join a team, Become a mentor, Workshops
        (we will move your existing STEM UI into stem.html)
        """
        return render_template("stem.html")

    @app.route("/contact")
    def contact_page() -> str:
        """Contact page with picture and address."""
        return render_template("contact.html")

    @app.route("/student", methods=["GET", "POST"])
    def student_portal() -> Any:
        student_email = session.get("student_email")
        student_name = session.get("student_name", "")
        student_photo = None
        status_message = None
        if request.method == "POST":
            student_email = normalize_email(request.form.get("email"))
            student_name = request.form.get("student_name", "").strip()
            if student_email:
                session["student_email"] = student_email
                if student_name:
                    session["student_name"] = student_name
            else:
                status_message = "Email is required to view your activity."
        requests_rows = student_requests(student_email) if student_email else []
        student_row = Student.query.filter(func.lower(Student.email) == normalize_email(student_email)).first() if student_email else None
        if student_row:
            student_photo = student_row.photo_url
            if not student_name and student_row.name:
                student_name = student_row.name
                session["student_name"] = student_name
        if not student_name and requests_rows:
            student_name = requests_rows[0].student_name or ""
            session["student_name"] = student_name
        pending = sum(1 for r in requests_rows if (r.status or "pending") == "pending")
        accepted = sum(1 for r in requests_rows if (r.status or "").lower() == "accepted")
        mentors = Mentor.query.filter_by(status="approved").order_by(Mentor.name.asc()).all()
        return render_template(
            "student.html",
            student_email=student_email,
            student_name=student_name,
            student_photo=student_photo,
            requests=requests_rows,
            pending=pending,
            accepted=accepted,
            mentors=mentors,
            status_message=status_message,
        )

    @app.route("/student/logout")
    def student_logout() -> Any:
        session.pop("student_email", None)
        session.pop("student_name", None)
        return redirect(url_for("student_portal"))

    # -----------------
    # Admin routes (simple password)
    # -----------------
    @app.route("/admin", methods=["GET", "POST"])
    def admin_login() -> Any:
        error = None
        if request.method == "POST":
            password = request.form.get("password", "")
            if password == app.config["ADMIN_PASSWORD"]:
                session["is_admin"] = True
                return redirect(url_for("admin_dashboard"))
            error = "Invalid password."
        return render_template("admin_login.html", error=error)

    @app.route("/admin/dashboard")
    def admin_dashboard() -> Any:
        if not session.get("is_admin"):
            return redirect(url_for("admin_login"))
        pending = Mentor.query.filter_by(status="pending").order_by(Mentor.created_at.desc()).all()
        approved = Mentor.query.filter_by(status="approved").order_by(Mentor.created_at.desc()).all()
        rejected = Mentor.query.filter_by(status="rejected").order_by(Mentor.created_at.desc()).all()
        students = Student.query.order_by(Student.created_at.desc()).all()
        return render_template(
            "admin_dashboard.html",
            pending=pending,
            approved=approved,
            rejected=rejected,
            students=students,
        )

    @app.route("/admin/mentors/<int:mentor_id>/<action>", methods=["POST"])
    def admin_moderate_mentor(mentor_id: int, action: str) -> Any:
        if not session.get("is_admin"):
            return redirect(url_for("admin_login"))
        mentor = Mentor.query.filter_by(id=mentor_id).first()
        if mentor is None:
            return redirect(url_for("admin_dashboard"))
        if action == "approve":
            mentor.status = "approved"
        elif action == "reject":
            mentor.status = "rejected"
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
        return redirect(url_for("admin_dashboard"))

    @app.route("/admin/mentors/<int:mentor_id>/delete", methods=["POST"])
    def admin_delete_mentor(mentor_id: int) -> Any:
        if not session.get("is_admin"):
            return redirect(url_for("admin_login"))
        mentor = Mentor.query.filter_by(id=mentor_id).first()
        if mentor:
            try:
                db.session.delete(mentor)
                db.session.commit()
            except Exception:
                db.session.rollback()
        return redirect(url_for("admin_dashboard"))

    @app.route("/admin/students/<int:student_id>/delete", methods=["POST"])
    def admin_delete_student(student_id: int) -> Any:
        if not session.get("is_admin"):
            return redirect(url_for("admin_login"))
        student = Student.query.filter_by(id=student_id).first()
        if student:
            try:
                db.session.delete(student)
                db.session.commit()
            except Exception:
                db.session.rollback()
        return redirect(url_for("admin_dashboard"))

    @app.route("/admin/logout")
    def admin_logout() -> Any:
        session.pop("is_admin", None)
        return redirect(url_for("admin_login"))

    # Optional: keep the old detailed pages if you still use them
    @app.route("/mentors/list")
    def mentors_page() -> str:
        return render_template("mentors.html")

    @app.route("/projects/list")
    def projects_page() -> str:
        return render_template("projects.html")

    @app.route("/mentor/register")
    def register_page() -> str:
        return render_template("register.html")

    # -----------------
    # API ROUTES
    # -----------------
    @app.route("/mentors", methods=["GET"])
    def get_mentors() -> Any:
        mentors = Mentor.query.filter_by(status="approved").order_by(Mentor.created_at.desc()).all()
        return jsonify([mentor.to_dict() for mentor in mentors])

    @app.route("/projects", methods=["GET"])
    def get_projects() -> Any:
        projects = Project.query.order_by(Project.created_at.desc()).all()
        slot_map = project_slot_summary()
        response = []
        for project in projects:
            counts = slot_map.get(project.id, {"accepted": 0})
            capacity = project_capacity(project)
            available = max(capacity - counts["accepted"], 0)
            record = project.to_dict()
            record.update(
                {
                    "accepted": counts["accepted"],
                    "capacity": capacity,
                    "available": available,
                    "is_full": available <= 0,
                }
            )
            response.append(record)
        return jsonify(response)

    @app.route("/api/add_mentor", methods=["POST"])
    def add_mentor() -> Any:
        payload = request.get_json(force=True) or {}
        name = payload.get("name", "").strip()
        field = payload.get("field", "").strip()
        description = payload.get("description", "").strip()
        research_area = payload.get("research_area", "").strip()
        photo = payload.get("photo", "").strip()
        email = payload.get("email", "").strip().lower()
        access_code = payload.get("access_code", "").strip()
        workshop_title = payload.get("workshop_title", "").strip()
        workshop_description = payload.get("workshop_description", "").strip()
        workshop_image = payload.get("workshop_image", "").strip()
        workshop_links = payload.get("workshop_links", "").strip()

        if not (name and field and description and email and access_code):
            return jsonify({"status": "error", "message": "Missing required mentor info."}), 400

        if Mentor.query.filter(Mentor.email == email).first():
            return jsonify({"status": "error", "message": "A mentor with this email already exists."}), 400

        mentor = Mentor(
            name=name,
            field=field,
            description=description,
            research_area=research_area,
            photo=photo,
            email=email,
            access_code_hash=generate_password_hash(access_code),
            status="pending",
            workshop_title=workshop_title,
            workshop_description=workshop_description,
            workshop_image=workshop_image,
            workshop_links=workshop_links,
        )

        try:
            db.session.add(mentor)
            db.session.commit()
        except Exception:
            db.session.rollback()
            return jsonify({"status": "error", "message": "Failed to save mentor."}), 500

        return jsonify(
            {
                "status": "success",
                "mentor": mentor.to_dict(),
                "message": "Mentor submitted. Pending admin approval.",
            }
        )

    @app.route("/api/join_mentor", methods=["POST"])
    def join_mentor() -> Any:
        payload = request.get_json(force=True) or {}
        mentor_name = payload.get("mentor_name", "").strip()
        mentor_id = payload.get("mentor_id")
        email = session.get("student_email")
        if not email:
            return jsonify({"status": "error", "message": "Not authenticated."}), 401
        student_name = session.get("student_name", "").strip() or payload.get("student_name", "").strip()
        interest = payload.get("interest", "").strip()
        message = payload.get("message", "").strip()

        if not (student_name and email):
            return jsonify({"status": "error", "message": "Student name and email required."}), 400

        mentor_obj = None
        if mentor_id is not None:
            mentor_obj = Mentor.query.filter_by(id=mentor_id).first()
        if mentor_obj is None and mentor_name:
            mentor_obj = Mentor.query.filter_by(name=mentor_name).first()

        if mentor_obj is None or mentor_obj.status != "approved":
            return jsonify({"status": "error", "message": "Mentor not found."}), 404

        request_row = JoinRequest(
            request_type="mentor",
            mentor_name=mentor_obj.name,
            mentor_id=mentor_obj.id,
            student_name=student_name,
            email=email,
            interest=interest,
            message=message,
            status="pending",
        )

        try:
            db.session.add(request_row)
            db.session.commit()
        except Exception:
            db.session.rollback()
            return jsonify({"status": "error", "message": "Failed to save request."}), 500

        return jsonify({"status": "success", "message": "Mentorship request sent."})

    @app.route("/api/join_project", methods=["POST"])
    def join_project() -> Any:
        payload = request.get_json(force=True) or {}
        project_title = payload.get("project_title", "").strip()
        project_id_raw = payload.get("project_id")
        email = session.get("student_email")
        if not email:
            return jsonify({"status": "error", "message": "Not authenticated."}), 401
        student_name = session.get("student_name", "").strip() or payload.get("student_name", "").strip()
        role = payload.get("role", "").strip()
        faculty = payload.get("faculty", "").strip()
        skills = payload.get("skills", "").strip()
        availability = payload.get("availability", "").strip()
        contact = payload.get("contact", "").strip()
        intro = payload.get("intro", "").strip()
        mentor_id_raw = payload.get("mentor_id")
        mentor_name = payload.get("mentor_name", "").strip()
        project_obj: Project | None = None

        if not (student_name and email):
            return jsonify({"status": "error", "message": "Student name and email required."}), 400

        mentor_obj = None
        if mentor_id_raw is not None and str(mentor_id_raw).strip() != "":
            try:
                mentor_id_val = int(mentor_id_raw)
                mentor_obj = Mentor.query.filter_by(id=mentor_id_val).first()
            except (TypeError, ValueError):
                mentor_obj = None
        elif mentor_name:
            mentor_obj = Mentor.query.filter_by(name=mentor_name).first()

        if mentor_id_raw and (mentor_obj is None or mentor_obj.status != "approved"):
            return jsonify({"status": "error", "message": "Selected mentor not found."}), 404

        if project_id_raw is not None and str(project_id_raw).strip() != "":
            try:
                project_id_val = int(project_id_raw)
                project_obj = Project.query.filter_by(id=project_id_val).first()
            except (TypeError, ValueError):
                project_obj = None
            if project_obj is None:
                return jsonify({"status": "error", "message": "Project not found."}), 404
            slot_map = project_slot_summary()
            accepted = slot_map.get(project_obj.id, {"accepted": 0})["accepted"]
            capacity = project_capacity(project_obj)
            if accepted >= capacity:
                return jsonify({"status": "error", "message": "Project team is full."}), 400

        request_row = JoinRequest(
            request_type="project",
            project_title=project_title,
            student_name=student_name,
            email=email,
            role=role,
            faculty=faculty,
            skills=skills,
            availability=availability,
            contact=contact,
            intro=intro,
            message=payload.get("message", "").strip(),
            mentor_id=mentor_obj.id if mentor_obj else None,
            mentor_name=mentor_obj.name if mentor_obj else None,
            project_id=project_obj.id if project_obj else None,
            status="pending",
        )

        try:
            db.session.add(request_row)
            db.session.commit()
        except Exception:
            db.session.rollback()
            return jsonify({"status": "error", "message": "Failed to save request."}), 500

        return jsonify({"status": "success", "message": "Project join request sent."})

    @app.route("/api/mentor/login", methods=["POST"])
    def mentor_login() -> Any:
        payload = request.get_json(force=True) or {}
        email = payload.get("email", "").strip().lower()
        access_code = payload.get("access_code", "").strip()
        mentor = authenticate_mentor(email, access_code)
        if mentor is None:
            return jsonify({"status": "error", "message": "Invalid mentor credentials."}), 401

        session["mentor_id"] = mentor.id
        session["mentor_email"] = mentor.email

        requests_rows = (
            JoinRequest.query.filter_by(mentor_id=mentor.id)
            .order_by(JoinRequest.created_at.desc())
            .all()
        )
        return jsonify(
            {
                "status": "success",
                "mentor": mentor.to_dict(),
                "requests": [req.to_dict() for req in requests_rows],
                "redirect": url_for("mentor_dashboard"),
            }
        )

    @app.route("/api/mentor/requests/<int:req_id>/decision", methods=["POST"])
    def mentor_decision(req_id: int) -> Any:
        payload = request.get_json(silent=True) or request.form.to_dict() or {}
        action = (payload.get("action") or "").strip().lower()
        if action not in {"accepted", "rejected"}:
            return (
                jsonify({"status": "error", "message": "Action must be accepted or rejected."}),
                400,
            )

        mentor = None
        # Prefer session auth if available
        if session.get("mentor_id"):
            mentor = Mentor.query.filter_by(id=session["mentor_id"]).first()
        if mentor is None:
            email = (payload.get("email") or "").strip().lower()
            access_code = (payload.get("access_code") or "").strip()
            mentor = authenticate_mentor(email, access_code)
        if mentor is None:
            return (
                jsonify({"status": "error", "message": "Invalid mentor credentials."}),
                401,
            )

        req_row = JoinRequest.query.filter_by(id=req_id, mentor_id=mentor.id).first()
        if req_row is None:
            return (
                jsonify({"status": "error", "message": "Request not found for this mentor."}),
                404,
            )

        req_row.status = action
        created_project: Project | None = None

        if action == "accepted" and req_row.project_id is None:
            title = req_row.project_title or req_row.interest or f"{req_row.student_name} x {mentor.name}"
            base_desc = req_row.message or req_row.intro or "Student proposal accepted by mentor."
            if req_row.student_name:
                base_desc += f" (Proposed by {req_row.student_name})"
            description = f"{base_desc} | Mentor: {mentor.name}"
            created_project = Project(
                title=title,
                category=req_row.role or "Student proposal",
                description=description,
                team_size=5,
                mentor_id=mentor.id,
            )
            try:
                db.session.add(created_project)
                db.session.flush()
                req_row.project_id = created_project.id
            except Exception:
                db.session.rollback()
                return jsonify({"status": "error", "message": "Failed to create project entry."}), 500
        elif action == "accepted" and req_row.project_id:
            project_obj = Project.query.filter_by(id=req_row.project_id).first()
            if project_obj is None:
                return jsonify({"status": "error", "message": "Project not found."}), 404
            capacity = project_capacity(project_obj)
            accepted = project_slot_summary().get(project_obj.id, {"accepted": 0})["accepted"]
            # include this request if it was already accepted? It was pending so count stays.
            if accepted >= capacity:
                return jsonify({"status": "error", "message": "Project is already full."}), 400
            if project_obj.mentor_id is None:
                project_obj.mentor_id = mentor.id

        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            return jsonify({"status": "error", "message": "Failed to update request."}), 500

        # For browsers posting a form, redirect back to dashboard; JSON clients get API data.
        if not request.is_json:
            return redirect(url_for("mentor_dashboard"))
        response = {"status": "success", "request": req_row.to_dict()}
        if created_project:
            response["project"] = created_project.to_dict()
        return jsonify(response)

    @app.route("/api/mentor/requests", methods=["GET"])
    def mentor_requests() -> Any:
        if not session.get("mentor_id"):
            return jsonify({"status": "error", "message": "Not authenticated."}), 401
        mentor = Mentor.query.filter_by(id=session["mentor_id"]).first()
        if mentor is None:
            return jsonify({"status": "error", "message": "Mentor not found."}), 404
        if mentor.status != "approved":
            return jsonify({"status": "error", "message": "Mentor not approved."}), 403
        requests_rows = (
            JoinRequest.query.filter_by(mentor_id=mentor.id)
            .order_by(JoinRequest.created_at.desc())
            .all()
        )
        mentor_projects = Project.query.filter_by(mentor_id=mentor.id).all()
        slot_map = project_slot_summary()
        return jsonify(
            {
                "status": "success",
                "mentor": mentor.to_dict(),
                "requests": [req.to_dict() for req in requests_rows],
                "projects": [
                    dict(
                        **proj.to_dict(),
                        accepted=slot_map.get(proj.id, {"accepted": 0})["accepted"],
                        capacity=project_capacity(proj),
                        available=max(project_capacity(proj) - slot_map.get(proj.id, {"accepted": 0})["accepted"], 0),
                    )
                    for proj in mentor_projects
                ],
            }
        )

    @app.route("/api/mentor/projects", methods=["GET", "POST"])
    def mentor_projects_api() -> Any:
        if not session.get("mentor_id"):
            return jsonify({"status": "error", "message": "Not authenticated."}), 401
        mentor = Mentor.query.filter_by(id=session["mentor_id"]).first()
        if mentor is None:
            return jsonify({"status": "error", "message": "Mentor not found."}), 404

        if request.method == "GET":
            slot_map = project_slot_summary()
            projects = Project.query.filter_by(mentor_id=mentor.id).order_by(Project.created_at.desc()).all()
            response = []
            for proj in projects:
                accepted = slot_map.get(proj.id, {"accepted": 0})["accepted"]
                capacity = project_capacity(proj)
                available = max(capacity - accepted, 0)
                members = (
                    JoinRequest.query.filter(
                        JoinRequest.project_id == proj.id, JoinRequest.status == "accepted"
                    )
                    .order_by(JoinRequest.created_at.asc())
                    .all()
                )
                response.append(
                    {
                        **proj.to_dict(),
                        "accepted": accepted,
                        "capacity": capacity,
                        "available": available,
                        "members": [m.to_dict() for m in members],
                    }
                )
            return jsonify({"status": "success", "projects": response})

        payload = request.get_json(force=True) or {}
        title = payload.get("title", "").strip()
        category = payload.get("category", "").strip()
        description = payload.get("description", "").strip()
        team_size_raw = payload.get("team_size")
        if not title:
            return jsonify({"status": "error", "message": "Project title is required."}), 400
        try:
            team_size_val = int(team_size_raw) if team_size_raw not in (None, "") else 5
            if team_size_val < 1 or team_size_val > 5:
                raise ValueError
        except (TypeError, ValueError):
            team_size_val = 5

        project = Project(
            title=title,
            category=category,
            description=description or "Mentor-created project",
            team_size=team_size_val,
            mentor_id=mentor.id,
        )
        try:
            db.session.add(project)
            db.session.commit()
        except Exception:
            db.session.rollback()
            return jsonify({"status": "error", "message": "Failed to create project."}), 500

        return jsonify(
            {
                "status": "success",
                "project": {
                    **project.to_dict(),
                    "accepted": 0,
                    "capacity": team_size_val,
                    "available": team_size_val,
                },
            }
        )

    @app.route("/api/mentor/projects/<int:project_id>/remove_member", methods=["POST"])
    def mentor_remove_member(project_id: int) -> Any:
        if not session.get("mentor_id"):
            return jsonify({"status": "error", "message": "Not authenticated."}), 401
        mentor = Mentor.query.filter_by(id=session["mentor_id"]).first()
        if mentor is None:
            return jsonify({"status": "error", "message": "Mentor not found."}), 404
        project = Project.query.filter_by(id=project_id, mentor_id=mentor.id).first()
        if project is None:
            return jsonify({"status": "error", "message": "Project not found."}), 404
        payload = request.get_json(force=True) or {}
        req_id = payload.get("request_id")
        member = JoinRequest.query.filter_by(id=req_id, project_id=project.id).first()
        if member is None:
            return jsonify({"status": "error", "message": "Request not found for this project."}), 404
        member.status = "removed"
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            return jsonify({"status": "error", "message": "Failed to remove member."}), 500
        return jsonify({"status": "success", "request": member.to_dict()})

    @app.route("/api/mentor/projects/<int:project_id>/delete", methods=["POST"])
    def mentor_delete_project(project_id: int) -> Any:
        if not session.get("mentor_id"):
            return jsonify({"status": "error", "message": "Not authenticated."}), 401
        mentor = Mentor.query.filter_by(id=session["mentor_id"]).first()
        if mentor is None:
            return jsonify({"status": "error", "message": "Mentor not found."}), 404
        project = Project.query.filter_by(id=project_id, mentor_id=mentor.id).first()
        if project is None:
            return jsonify({"status": "error", "message": "Project not found."}), 404
        try:
            db.session.execute(
                text(
                    "UPDATE requests SET status = 'project_deleted', project_id = NULL WHERE project_id = :pid"
                ),
                {"pid": project.id},
            )
            db.session.delete(project)
            db.session.commit()
        except Exception:
            db.session.rollback()
            return jsonify({"status": "error", "message": "Failed to delete project."}), 500
        return jsonify({"status": "success", "message": "Project removed."})

    @app.route("/api/requests/withdraw", methods=["POST"])
    def request_withdraw() -> Any:
        payload = request.get_json(force=True) or {}
        email = normalize_email(payload.get("email"))
        project_title = (payload.get("project_title") or "").strip()
        project_id_raw = payload.get("project_id")
        if not email:
            return jsonify({"status": "error", "message": "Email is required."}), 400
        query = JoinRequest.query.filter(
            JoinRequest.email == email, JoinRequest.status.in_(["pending", "accepted"])
        )
        if project_id_raw:
            try:
                pid = int(project_id_raw)
                query = query.filter(JoinRequest.project_id == pid)
            except (TypeError, ValueError):
                pass
        elif project_title:
            query = query.filter(JoinRequest.project_title == project_title)
        req_obj = query.order_by(JoinRequest.created_at.desc()).first()
        if req_obj is None:
            return jsonify({"status": "error", "message": "No matching request found."}), 404
        req_obj.status = "withdrawn"
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            return jsonify({"status": "error", "message": "Failed to withdraw request."}), 500
        return jsonify({"status": "success", "request": req_obj.to_dict()})

    @app.route("/api/student/login", methods=["POST"])
    def student_login() -> Any:
        payload = request.get_json(force=True) or {}
        email = normalize_email(payload.get("email"))
        student_name = payload.get("student_name", "").strip()
        password = payload.get("password", "").strip()
        photo_data = payload.get("photo_data")
        if not (email and password):
            return jsonify({"status": "error", "message": "Email and password are required."}), 400

        student = Student.query.filter(func.lower(Student.email) == email).first()
        created = False
        if student is None:
            student = Student(email=email, name=student_name or email.split("@")[0])
            student.set_password(password)
            if photo_data:
                try:
                    student.photo_url = save_student_photo(photo_data)
                except Exception:
                    pass
            db.session.add(student)
            created = True
        else:
            if not student.check_password(password):
                return jsonify({"status": "error", "message": "Invalid credentials."}), 401
            if student_name:
                student.name = student_name
            if photo_data:
                try:
                    student.photo_url = save_student_photo(photo_data)
                except Exception:
                    pass
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            return jsonify({"status": "error", "message": "Failed to save student."}), 500

        session["student_email"] = email
        session["student_name"] = student.name or student_name or ""
        requests_rows = student_requests(email)
        if not student_name and requests_rows:
            student_name = requests_rows[0].student_name or ""
            session["student_name"] = student_name
        pending = sum(1 for r in requests_rows if (r.status or "pending") == "pending")
        accepted = sum(1 for r in requests_rows if (r.status or "").lower() == "accepted")
        return jsonify(
            {
                "status": "success",
                "email": email,
                "student_name": student.name or student_name,
                "photo_url": student.photo_url,
                "created": created,
                "pending": pending,
                "accepted": accepted,
                "requests": [r.to_dict() for r in requests_rows],
            }
        )

    @app.route("/api/student/requests", methods=["GET"])
    def student_requests_api() -> Any:
        email = session.get("student_email")
        if not email:
            return jsonify({"status": "error", "message": "Not authenticated."}), 401
        requests_rows = student_requests(email)
        student_name = session.get("student_name") or (requests_rows[0].student_name if requests_rows else "")
        student_row = Student.query.filter(func.lower(Student.email) == normalize_email(email)).first()
        pending = sum(1 for r in requests_rows if (r.status or "pending") == "pending")
        accepted = sum(1 for r in requests_rows if (r.status or "").lower() == "accepted")
        return jsonify(
            {
                "status": "success",
                "email": email,
                "student_name": student_name,
                "photo_url": student_row.photo_url if student_row else None,
                "pending": pending,
                "accepted": accepted,
                "requests": [r.to_dict() for r in requests_rows],
            }
        )

    @app.route("/api/student/withdraw/<int:req_id>", methods=["POST"])
    def student_withdraw_request(req_id: int) -> Any:
        email = session.get("student_email")
        if not email:
            return (
                redirect(url_for("student_portal"))
                if "text/html" in request.headers.get("Accept", "")
                else (jsonify({"status": "error", "message": "Not authenticated."}), 401)
            )
        req_obj = JoinRequest.query.filter(
            JoinRequest.id == req_id, func.lower(JoinRequest.email) == email
        ).first()
        if req_obj is None:
            return (
                redirect(url_for("student_portal"))
                if "text/html" in request.headers.get("Accept", "")
                else (jsonify({"status": "error", "message": "Request not found."}), 404)
            )
        req_obj.status = "withdrawn"
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            return (
                redirect(url_for("student_portal"))
                if "text/html" in request.headers.get("Accept", "")
                else (jsonify({"status": "error", "message": "Failed to withdraw request."}), 500)
            )
        # If the request came from a browser navigation, send them back to the student portal.
        if "text/html" in request.headers.get("Accept", ""):
            return redirect(url_for("student_portal"))
        return jsonify({"status": "success", "request": req_obj.to_dict()})

    @app.route("/student/withdraw/<int:req_id>", methods=["POST"])
    def student_withdraw_request_form(req_id: int) -> Any:
        email = session.get("student_email")
        if not email:
            return redirect(url_for("student_portal"))
        req_obj = JoinRequest.query.filter(
            JoinRequest.id == req_id, func.lower(JoinRequest.email) == email
        ).first()
        if req_obj:
            req_obj.status = "withdrawn"
            try:
                db.session.commit()
            except Exception:
                db.session.rollback()
        return redirect(url_for("student_portal"))

    @app.route("/api/student/photo", methods=["POST"])
    def student_photo_upload() -> Any:
        payload = request.get_json(force=True) or {}
        email = normalize_email(payload.get("email") or session.get("student_email"))
        photo_data = payload.get("photo_data")
        if not (email and photo_data):
            return jsonify({"status": "error", "message": "Email and photo_data required."}), 400
        student = Student.query.filter(func.lower(Student.email) == email).first()
        if student is None:
            return jsonify({"status": "error", "message": "Student not found."}), 404
        try:
            photo_url = save_student_photo(photo_data)
            student.photo_url = photo_url
            db.session.commit()
            return jsonify({"status": "success", "photo_url": photo_url, "message": "Photo updated."})
        except Exception:
            db.session.rollback()
            return jsonify({"status": "error", "message": "Upload failed."}), 500

    @app.route("/mentor/dashboard")
    def mentor_dashboard() -> Any:
        if not session.get("mentor_id"):
            return redirect(url_for("register_page"))
        mentor = Mentor.query.filter_by(id=session["mentor_id"]).first()
        if mentor is None:
            session.clear()
            return redirect(url_for("register_page"))
        if mentor.status != "approved":
            session.clear()
            return redirect(url_for("register_page"))
        requests_rows = (
            JoinRequest.query.filter_by(mentor_id=mentor.id)
            .order_by(JoinRequest.created_at.desc())
            .all()
        )
        mentor_projects = (
            Project.query.filter_by(mentor_id=mentor.id)
            .order_by(Project.created_at.desc())
            .all()
        )
        slot_map = project_slot_summary()
        project_members = {
            p.id: JoinRequest.query.filter(
                JoinRequest.project_id == p.id, JoinRequest.status == "accepted"
            ).all()
            for p in mentor_projects
        }
        return render_template(
            "mentor_dashboard.html",
            mentor=mentor,
            requests=requests_rows,
            projects=mentor_projects,
            project_members=project_members,
            project_slots=slot_map,
        )

    @app.route("/mentor/logout")
    def mentor_logout() -> Any:
        session.clear()
        return redirect(url_for("register_page"))

    @app.route("/mentor/projects/create", methods=["POST"])
    def mentor_project_create() -> Any:
        if not session.get("mentor_id"):
            return redirect(url_for("register_page"))
        mentor = Mentor.query.filter_by(id=session["mentor_id"]).first()
        if mentor is None:
            return redirect(url_for("register_page"))
        title = request.form.get("title", "").strip()
        category = request.form.get("category", "").strip()
        description = request.form.get("description", "").strip()
        team_size_raw = request.form.get("team_size", "").strip()
        if not title:
            return redirect(url_for("mentor_dashboard"))
        try:
            team_size_val = int(team_size_raw) if team_size_raw else 5
            if team_size_val < 1 or team_size_val > 5:
                team_size_val = 5
        except Exception:
            team_size_val = 5
        project = Project(
            title=title,
            category=category,
            description=description or "Mentor-created project",
            team_size=team_size_val,
            mentor_id=mentor.id,
        )
        try:
            db.session.add(project)
            db.session.commit()
        except Exception:
            db.session.rollback()
        return redirect(url_for("mentor_dashboard"))

    @app.route("/mentor/projects/<int:project_id>/remove_member", methods=["POST"])
    def mentor_project_remove_member(project_id: int) -> Any:
        if not session.get("mentor_id"):
            return redirect(url_for("register_page"))
        mentor = Mentor.query.filter_by(id=session["mentor_id"]).first()
        if mentor is None:
            return redirect(url_for("register_page"))
        req_id = request.form.get("request_id")
        member = (
            JoinRequest.query.filter_by(id=req_id, project_id=project_id, mentor_id=mentor.id)
            .first()
        )
        if member:
            member.status = "removed"
            try:
                db.session.commit()
            except Exception:
                db.session.rollback()
        return redirect(url_for("mentor_dashboard"))

    @app.route("/mentor/projects/<int:project_id>/delete", methods=["POST"])
    def mentor_project_delete(project_id: int) -> Any:
        if not session.get("mentor_id"):
            return redirect(url_for("register_page"))
        mentor = Mentor.query.filter_by(id=session["mentor_id"]).first()
        if mentor is None:
            return redirect(url_for("register_page"))
        project = Project.query.filter_by(id=project_id, mentor_id=mentor.id).first()
        if project is None:
            return redirect(url_for("mentor_dashboard"))
        try:
            db.session.execute(
                text(
                    "UPDATE requests SET status = 'project_deleted', project_id = NULL WHERE project_id = :pid"
                ),
                {"pid": project.id},
            )
            db.session.delete(project)
            db.session.commit()
        except Exception:
            db.session.rollback()
        return redirect(url_for("mentor_dashboard"))

    return app


app = create_app()


if __name__ == "__main__":
    # Enable debug for quick iteration during judging/demo.
    app.run(host="0.0.0.0", port=5000, debug=True)
