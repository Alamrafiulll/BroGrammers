# MMU STEM Portal

Flask + SQLite prototype to connect students, mentors, and admin approvals in one place.

## Quick start
1) Install Python 3.10+ and create a virtualenv (optional):
   ```
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   source .venv/bin/activate  # macOS/Linux
   ```
2) Install deps:
   ```
   pip install -r requirements.txt
   ```
3) Run the app:
   ```
   python app.py
   ```
   The server starts on http://127.0.0.1:5000

## Configuration
- `FLASK_SECRET_KEY` (optional): session signing key. Defaults to `mmu-stem-secret`.
- `ADMIN_PASSWORD` (optional): admin dashboard password. Defaults to `admin123`.
- Data is stored in `data/app.db` (SQLite). First run seeds starter projects.

## Roles & flows
- **Visitor**
  - Views the STEM portal: mentors, projects, stories.
  - Can’t submit requests until they register as a student.

- **Student**
  - Registers/Login via the “Join” form (email + password, optional name).
  - Requests mentorship, joins projects, and sees status in `Student` page.
  - Needs an accepted mentor before submitting a project idea.
  - Can withdraw requests from the student portal.

- **Mentor**
  - Registers via `Mentor Registration` (name, field, description, email, access code).
  - Must be **approved by admin** before logging in.
  - After login (`Mentor Login`), can accept/reject student requests, create projects, and manage team members.

- **Admin**
  - Login at `/admin` with `ADMIN_PASSWORD`.
  - Dashboard lists pending mentors (approve/reject), approved mentors, and student list (can remove students).

## Notes
- Student photos are saved under `static/uploads/students/`.
- If schema changes are missed, delete `data/app.db` (and WAL/shm) then rerun to recreate fresh.
- The app uses server-side sessions; clearing browser cookies logs out users/mentors/admin.
