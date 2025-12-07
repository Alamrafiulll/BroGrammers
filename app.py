from __future__ import annotations

from pathlib import Path
from typing import Any

from flask import Flask, jsonify, render_template, request

from backend.db import init_db
from backend.models import (
    get_all_mentors,
    get_all_projects,
    add_mentor,
    record_mentor_request,
    record_project_request,
    ensure_seed_data,
)

BASE_DIR = Path(__file__).parent


def create_app() -> Flask:
    """Application factory."""
    app = Flask(__name__)

    # --- NEW: initialize SQLite DB and seed default data ---
    init_db()
    ensure_seed_data()

    # -----------------------
    # PAGE ROUTES (TEMPLATES)
    # -----------------------

    @app.route("/")
    def home() -> str:
        """
        Main MMU page:
        - Overview, vision/mission, history
        - Live stats: mentors & projects (from SQLite DB)
        """
        mentors = get_all_mentors()
        projects = get_all_projects()
        return render_template(
            "index.html",
            mentor_count=len(mentors),
            project_count=len(projects),
        )

    @app.route("/stem")
    def stem_page() -> str:
        """
        STEM portal page:
        - Can also show live counts if needed.
        """
        mentors = get_all_mentors()
        projects = get_all_projects()
        return render_template(
            "stem.html",
            mentor_count=len(mentors),
            project_count=len(projects),
        )

    @app.route("/contact")
    def contact_page() -> str:
        """Contact page with picture and address."""
        return render_template("contact.html")

    @app.route("/mentors/list")
    def mentors_page() -> str:
        return render_template("mentors.html")

    @app.route("/projects/list")
    def projects_page() -> str:
        return render_template("projects.html")

    @app.route("/mentor/register")
    def register_page() -> str:
        return render_template("register.html")

    # --------------
    # JSON API ROUTES
    # --------------

    @app.route("/mentors", methods=["GET"])
    def api_get_mentors() -> Any:
        mentors = get_all_mentors()
        return jsonify(mentors)

    @app.route("/projects", methods=["GET"])
    def api_get_projects() -> Any:
        projects = get_all_projects()
        return jsonify(projects)

    @app.route("/api/add_mentor", methods=["POST"])
    def api_add_mentor() -> Any:
        payload = request.get_json(force=True) or {}
        name = (payload.get("name") or "").strip()
        field = (payload.get("field") or "").strip()
        description = (payload.get("description") or "").strip()
        research_area = (payload.get("research_area") or "").strip()
        photo = (payload.get("photo") or "").strip()

        if not (name and field and description):
            return (
                jsonify(
                    {"status": "error", "message": "Missing required mentor info."}
                ),
                400,
            )

        mentor_entry = {
            "name": name,
            "field": field,
            "description": description,
            "research_area": research_area,
            "photo": photo,
        }
        saved = add_mentor(mentor_entry)
        return jsonify({"status": "success", "mentor": saved})

    @app.route("/api/join_mentor", methods=["POST"])
    def api_join_mentor() -> Any:
        payload = request.get_json(force=True) or {}

        # basic validation
        student_name = (payload.get("student_name") or "").strip()
        email = (payload.get("email") or "").strip()
        if not (student_name and email):
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Student name and email required.",
                    }
                ),
                400,
            )

        record_mentor_request(payload)
        return jsonify({"status": "success", "message": "Mentorship request sent."})

    @app.route("/api/join_project", methods=["POST"])
    def api_join_project() -> Any:
        payload = request.get_json(force=True) or {}

        student_name = (payload.get("student_name") or "").strip()
        email = (payload.get("email") or "").strip()
        if not (student_name and email):
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Student name and email required.",
                    }
                ),
                400,
            )

        record_project_request(payload)
        return jsonify({"status": "success", "message": "Project join request sent."})

    return app


app = create_app()

if __name__ == "__main__":
    # debug=True is fine for competition/demo
    app.run(host="0.0.0.0", port=5000, debug=True)
