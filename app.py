from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from flask import Flask, jsonify, render_template, request


BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
MENTORS_FILE = DATA_DIR / "mentors.json"
PROJECTS_FILE = DATA_DIR / "projects.json"
REQUESTS_FILE = DATA_DIR / "requests.json"


def ensure_data_files() -> None:
    """Ensure JSON storage files exist with starter content."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if not MENTORS_FILE.exists():
        default_mentors: List[Dict[str, Any]] = [
            {
                "name": "Dr. Aisha Rahman",
                "field": "Artificial Intelligence",
                "description": "Focus on ethical AI and applied machine learning projects.",
                "research_area": "AI Ethics",
                "photo": "https://images.unsplash.com/photo-1524504388940-b1c1722653e1?auto=format&fit=crop&w=240&h=240&q=80",
            },
            {
                "name": "Engr. Kelvin Lim",
                "field": "Robotics",
                "description": "Guides students on robotics competitions and ROS basics.",
                "research_area": "Autonomous Systems",
                "photo": "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&w=240&h=240&q=80",
            },
        ]
        MENTORS_FILE.write_text(json.dumps(default_mentors, indent=2))

    if not PROJECTS_FILE.exists():
        default_projects: List[Dict[str, Any]] = [
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
        PROJECTS_FILE.write_text(json.dumps(default_projects, indent=2))

    if not REQUESTS_FILE.exists():
        REQUESTS_FILE.write_text(json.dumps([], indent=2))


def read_json(path: Path) -> List[Dict[str, Any]]:
    """Read JSON file into a list."""
    try:
        return json.loads(path.read_text())  # type: ignore[no-any-return]
    except Exception:
        return []


def append_to_json(path: Path, entry: Dict[str, Any]) -> None:
    """Append an entry to a JSON list file."""
    data = read_json(path)
    data.append(entry)
    path.write_text(json.dumps(data, indent=2))


def create_app() -> Flask:
    """Application factory."""
    ensure_data_files()
    app = Flask(__name__)

    @app.route("/")
    def home() -> str:
        return render_template("index.html")

    @app.route("/mentors/list")
    def mentors_page() -> str:
        return render_template("mentors.html")

    @app.route("/projects/list")
    def projects_page() -> str:
        return render_template("projects.html")

    @app.route("/mentor/register")
    def register_page() -> str:
        return render_template("register.html")

    # API routes
    @app.route("/mentors", methods=["GET"])
    def get_mentors() -> Any:
        mentors = read_json(MENTORS_FILE)
        return jsonify(mentors)

    @app.route("/projects", methods=["GET"])
    def get_projects() -> Any:
        projects = read_json(PROJECTS_FILE)
        return jsonify(projects)

    @app.route("/api/add_mentor", methods=["POST"])
    def add_mentor() -> Any:
        payload = request.get_json(force=True) or {}
        name = payload.get("name", "").strip()
        field = payload.get("field", "").strip()
        description = payload.get("description", "").strip()
        research_area = payload.get("research_area", "").strip()

        if not (name and field and description):
            return jsonify({"status": "error", "message": "Missing required mentor info."}), 400

        mentor_entry = {
            "name": name,
            "field": field,
            "description": description,
            "research_area": research_area,
        }
        append_to_json(MENTORS_FILE, mentor_entry)
        return jsonify({"status": "success", "mentor": mentor_entry})

    @app.route("/api/join_mentor", methods=["POST"])
    def join_mentor() -> Any:
        payload = request.get_json(force=True) or {}
        entry = {
            "type": "mentor_request",
            "mentor_name": payload.get("mentor_name", "").strip(),
            "student_name": payload.get("student_name", "").strip(),
            "email": payload.get("email", "").strip(),
            "interest": payload.get("interest", "").strip(),
            "message": payload.get("message", "").strip(),
        }
        if not (entry["student_name"] and entry["email"]):
            return jsonify({"status": "error", "message": "Student name and email required."}), 400

        append_to_json(REQUESTS_FILE, entry)
        return jsonify({"status": "success", "message": "Mentorship request sent."})

    @app.route("/api/join_project", methods=["POST"])
    def join_project() -> Any:
        payload = request.get_json(force=True) or {}
        entry = {
            "type": "project_request",
            "project_title": payload.get("project_title", "").strip(),
            "student_name": payload.get("student_name", "").strip(),
            "email": payload.get("email", "").strip(),
            "role": payload.get("role", "").strip(),
            "faculty": payload.get("faculty", "").strip(),
            "skills": payload.get("skills", "").strip(),
            "availability": payload.get("availability", "").strip(),
            "contact": payload.get("contact", "").strip(),
            "intro": payload.get("intro", "").strip(),
        }
        if not (entry["student_name"] and entry["email"]):
            return jsonify({"status": "error", "message": "Student name and email required."}), 400

        append_to_json(REQUESTS_FILE, entry)
        return jsonify({"status": "success", "message": "Project join request sent."})

    return app


app = create_app()


if __name__ == "__main__":
    # Enable debug for quick iteration during judging/demo.
    app.run(host="0.0.0.0", port=5000, debug=True)
