from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import os
from flask import Flask, jsonify, render_template, request, redirect, session, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from werkzeug.security import check_password_hash, generate_password_hash


BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DB_FILE = DATA_DIR / "app.db"
PROJECTS_FILE = DATA_DIR / "projects.json"

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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
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
            "pending_requests": pending,
            "total_requests": total,
            "created_at": self.created_at.isoformat(),
        }


class Project(db.Model):
    __tablename__ = "projects"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(120), default="")
    description = db.Column(db.Text, default="")
    team_size = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "category": self.category,
            "description": self.description,
            "team_size": self.team_size,
            "created_at": self.created_at.isoformat(),
        }


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
    project = db.relationship("Project")

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


def init_database(app: Flask) -> None:
    """Configure and initialize the SQLite database."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_FILE}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)

    with app.app_context():
        db.create_all()
        upgrade_schema()
        seed_defaults()


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
    add_column_if_missing("requests", "status", "TEXT DEFAULT 'pending'")
    add_column_if_missing("requests", "mentor_id", "INTEGER")
    add_column_if_missing("requests", "project_id", "INTEGER")

    # backfill null statuses to pending for older rows
    db.session.execute(text("UPDATE requests SET status = 'pending' WHERE status IS NULL"))
    db.session.commit()


def authenticate_mentor(email: str, access_code: str) -> Mentor | None:
    """Return mentor if credentials are valid."""
    if not (email and access_code):
        return None
    mentor = Mentor.query.filter(Mentor.email == email.lower()).first()
    if mentor and mentor.access_code_hash and check_password_hash(mentor.access_code_hash, access_code):
        return mentor
    return None


def create_app() -> Flask:
    """Application factory."""
    app = Flask(__name__)
    app.secret_key = os.getenv("FLASK_SECRET_KEY", "mmu-stem-secret")
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
            mentor_count=Mentor.query.count(),
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
        mentors = Mentor.query.order_by(Mentor.created_at.desc()).all()
        return jsonify([mentor.to_dict() for mentor in mentors])

    @app.route("/projects", methods=["GET"])
    def get_projects() -> Any:
        projects = Project.query.order_by(Project.created_at.desc()).all()
        return jsonify([project.to_dict() for project in projects])

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
        )

        try:
            db.session.add(mentor)
            db.session.commit()
        except Exception:
            db.session.rollback()
            return jsonify({"status": "error", "message": "Failed to save mentor."}), 500

        return jsonify({"status": "success", "mentor": mentor.to_dict()})

    @app.route("/api/join_mentor", methods=["POST"])
    def join_mentor() -> Any:
        payload = request.get_json(force=True) or {}
        mentor_name = payload.get("mentor_name", "").strip()
        mentor_id = payload.get("mentor_id")
        student_name = payload.get("student_name", "").strip()
        email = payload.get("email", "").strip()
        interest = payload.get("interest", "").strip()
        message = payload.get("message", "").strip()

        if not (student_name and email):
            return jsonify({"status": "error", "message": "Student name and email required."}), 400

        mentor_obj = None
        if mentor_id is not None:
            mentor_obj = Mentor.query.filter_by(id=mentor_id).first()
        if mentor_obj is None and mentor_name:
            mentor_obj = Mentor.query.filter_by(name=mentor_name).first()

        if mentor_obj is None:
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
        student_name = payload.get("student_name", "").strip()
        email = payload.get("email", "").strip()
        role = payload.get("role", "").strip()
        faculty = payload.get("faculty", "").strip()
        skills = payload.get("skills", "").strip()
        availability = payload.get("availability", "").strip()
        contact = payload.get("contact", "").strip()
        intro = payload.get("intro", "").strip()

        if not (student_name and email):
            return jsonify({"status": "error", "message": "Student name and email required."}), 400

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
        payload = request.get_json(force=True) or {}
        action = payload.get("action", "").strip().lower()
        if action not in {"accepted", "rejected"}:
            return jsonify({"status": "error", "message": "Action must be accepted or rejected."}), 400

        mentor = None
        # Prefer session auth if available
        if session.get("mentor_id"):
            mentor = Mentor.query.filter_by(id=session["mentor_id"]).first()
        if mentor is None:
            email = payload.get("email", "").strip().lower()
            access_code = payload.get("access_code", "").strip()
            mentor = authenticate_mentor(email, access_code)
        if mentor is None:
            return jsonify({"status": "error", "message": "Invalid mentor credentials."}), 401

        req_row = JoinRequest.query.filter_by(id=req_id, mentor_id=mentor.id).first()
        if req_row is None:
            return jsonify({"status": "error", "message": "Request not found for this mentor."}), 404

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
                team_size=None,
            )
            try:
                db.session.add(created_project)
                db.session.flush()
                req_row.project_id = created_project.id
            except Exception:
                db.session.rollback()
                return jsonify({"status": "error", "message": "Failed to create project entry."}), 500

        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            return jsonify({"status": "error", "message": "Failed to update request."}), 500

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
            }
        )

    @app.route("/mentor/dashboard")
    def mentor_dashboard() -> Any:
        if not session.get("mentor_id"):
            return redirect(url_for("register_page"))
        mentor = Mentor.query.filter_by(id=session["mentor_id"]).first()
        if mentor is None:
            session.clear()
            return redirect(url_for("register_page"))
        requests_rows = (
            JoinRequest.query.filter_by(mentor_id=mentor.id)
            .order_by(JoinRequest.created_at.desc())
            .all()
        )
        return render_template(
            "mentor_dashboard.html",
            mentor=mentor,
            requests=requests_rows,
        )

    @app.route("/mentor/logout")
    def mentor_logout() -> Any:
        session.clear()
        return redirect(url_for("register_page"))

    return app


app = create_app()


if __name__ == "__main__":
    # Enable debug for quick iteration during judging/demo.
    app.run(host="0.0.0.0", port=5000, debug=True)
