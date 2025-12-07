# backend/models.py
from __future__ import annotations

from typing import Any, Dict, List

from backend.db import get_connection


# ---------- MENTORS ----------

def get_all_mentors() -> List[Dict[str, Any]]:
    """Return all mentors as list of dicts."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, name, field, description, research_area, photo "
        "FROM mentors ORDER BY id"
    )
    rows = [dict(row) for row in cur.fetchall()]
    conn.close()
    return rows


def add_mentor(mentor: Dict[str, Any]) -> Dict[str, Any]:
    """Insert a new mentor into the DB."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO mentors (name, field, description, research_area, photo)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            mentor["name"],
            mentor["field"],
            mentor["description"],
            mentor.get("research_area", ""),
            mentor.get("photo", ""),
        ),
    )
    mentor_id = cur.lastrowid
    conn.commit()
    conn.close()
    mentor["id"] = mentor_id
    return mentor


# ---------- PROJECTS ----------

def get_all_projects() -> List[Dict[str, Any]]:
    """Return all projects as list of dicts."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, title, category, description, team_size "
        "FROM projects ORDER BY id"
    )
    rows = [dict(row) for row in cur.fetchall()]
    conn.close()
    return rows


def add_project(project: Dict[str, Any]) -> Dict[str, Any]:
    """Insert a new project into the DB (not used yet, but ready)."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO projects (title, category, description, team_size)
        VALUES (?, ?, ?, ?)
        """,
        (
            project["title"],
            project.get("category", ""),
            project.get("description", ""),
            project.get("team_size", 0),
        ),
    )
    project_id = cur.lastrowid
    conn.commit()
    conn.close()
    project["id"] = project_id
    return project


# ---------- REQUESTS ----------

def record_mentor_request(payload: Dict[str, Any]) -> None:
    """Store a mentor_request in the requests table."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO requests (
            type, mentor_name, student_name, email, interest, message
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            "mentor_request",
            payload.get("mentor_name", ""),
            payload.get("student_name", ""),
            payload.get("email", ""),
            payload.get("interest", ""),
            payload.get("message", ""),
        ),
    )
    conn.commit()
    conn.close()


def record_project_request(payload: Dict[str, Any]) -> None:
    """Store a project_request in the requests table."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO requests (
            type, project_title, student_name, email,
            role, faculty, skills, availability, contact, intro, message
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "project_request",
            payload.get("project_title", ""),
            payload.get("student_name", ""),
            payload.get("email", ""),
            payload.get("role", ""),
            payload.get("faculty", ""),
            payload.get("skills", ""),
            payload.get("availability", ""),
            payload.get("contact", ""),
            payload.get("intro", ""),
            payload.get("message", ""),  # from join form
        ),
    )
    conn.commit()
    conn.close()


# ---------- SEED DATA (DEFAULT MENTORS / PROJECTS) ----------

def ensure_seed_data() -> None:
    """
    If mentors/projects tables are empty, insert your default
    two mentors & two projects (so the UI is not empty).
    """
    conn = get_connection()
    cur = conn.cursor()

    # Seed mentors
    cur.execute("SELECT COUNT(*) FROM mentors")
    mentor_count = cur.fetchone()[0]
    if mentor_count == 0:
        default_mentors = [
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
        for m in default_mentors:
            cur.execute(
                """
                INSERT INTO mentors (name, field, description, research_area, photo)
                VALUES (?, ?, ?, ?, ?)
                """,
                (m["name"], m["field"], m["description"], m["research_area"], m["photo"]),
            )

    # Seed projects
    cur.execute("SELECT COUNT(*) FROM projects")
    proj_count = cur.fetchone()[0]
    if proj_count == 0:
        default_projects = [
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
        for p in default_projects:
            cur.execute(
                """
                INSERT INTO projects (title, category, description, team_size)
                VALUES (?, ?, ?, ?)
                """,
                (p["title"], p["category"], p["description"], p["team_size"]),
            )

    conn.commit()
    conn.close()
