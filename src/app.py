"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import os
from pathlib import Path
import sqlite3

current_dir = Path(__file__).parent
database_path = os.getenv("DATABASE_PATH", str(current_dir / "activities.db"))

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

SEED_ACTIVITIES = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"]
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"]
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"]
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"]
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"]
    }
}


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(database_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def initialize_database() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT NOT NULL,
                schedule TEXT NOT NULL,
                max_participants INTEGER NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS registrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                activity_id INTEGER NOT NULL,
                student_id INTEGER NOT NULL,
                UNIQUE(activity_id, student_id),
                FOREIGN KEY(activity_id) REFERENCES activities(id) ON DELETE CASCADE,
                FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE
            )
            """
        )

        existing_activity_count = conn.execute(
            "SELECT COUNT(*) as count FROM activities"
        ).fetchone()["count"]

        if existing_activity_count == 0:
            seed_database(conn)


def seed_database(conn: sqlite3.Connection) -> None:
    for activity_name, details in SEED_ACTIVITIES.items():
        activity_cursor = conn.execute(
            """
            INSERT INTO activities (name, description, schedule, max_participants)
            VALUES (?, ?, ?, ?)
            """,
            (
                activity_name,
                details["description"],
                details["schedule"],
                details["max_participants"],
            ),
        )
        activity_id = activity_cursor.lastrowid

        for email in details["participants"]:
            conn.execute(
                "INSERT OR IGNORE INTO students (email) VALUES (?)",
                (email,),
            )
            student_id = conn.execute(
                "SELECT id FROM students WHERE email = ?",
                (email,),
            ).fetchone()["id"]
            conn.execute(
                """
                INSERT OR IGNORE INTO registrations (activity_id, student_id)
                VALUES (?, ?)
                """,
                (activity_id, student_id),
            )


def fetch_activity(activity_name: str, conn: sqlite3.Connection) -> sqlite3.Row | None:
    return conn.execute(
        """
        SELECT id, name, description, schedule, max_participants
        FROM activities
        WHERE name = ?
        """,
        (activity_name,),
    ).fetchone()


@app.on_event("startup")
def on_startup() -> None:
    initialize_database()


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    try:
        with get_connection() as conn:
            activity_rows = conn.execute(
                """
                SELECT id, name, description, schedule, max_participants
                FROM activities
                ORDER BY name
                """
            ).fetchall()

            registrations = conn.execute(
                """
                SELECT r.activity_id, s.email
                FROM registrations r
                JOIN students s ON s.id = r.student_id
                ORDER BY s.email
                """
            ).fetchall()

            participants_by_activity: dict[int, list[str]] = {}
            for registration in registrations:
                participants_by_activity.setdefault(
                    registration["activity_id"], []).append(registration["email"])

            activities: dict[str, dict[str, str | int | list[str]]] = {}
            for activity in activity_rows:
                activities[activity["name"]] = {
                    "description": activity["description"],
                    "schedule": activity["schedule"],
                    "max_participants": activity["max_participants"],
                    "participants": participants_by_activity.get(activity["id"], []),
                }

            return activities
    except sqlite3.Error:
        raise HTTPException(status_code=500, detail="Database error while loading activities")


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str):
    """Sign up a student for an activity"""
    try:
        with get_connection() as conn:
            activity = fetch_activity(activity_name, conn)
            if activity is None:
                raise HTTPException(status_code=404, detail="Activity not found")

            conn.execute("INSERT OR IGNORE INTO students (email) VALUES (?)", (email,))
            student = conn.execute(
                "SELECT id FROM students WHERE email = ?",
                (email,),
            ).fetchone()

            existing_registration = conn.execute(
                """
                SELECT id
                FROM registrations
                WHERE activity_id = ? AND student_id = ?
                """,
                (activity["id"], student["id"]),
            ).fetchone()

            if existing_registration:
                raise HTTPException(
                    status_code=400,
                    detail="Student is already signed up"
                )

            conn.execute(
                """
                INSERT INTO registrations (activity_id, student_id)
                VALUES (?, ?)
                """,
                (activity["id"], student["id"]),
            )
            return {"message": f"Signed up {email} for {activity_name}"}
    except sqlite3.Error:
        raise HTTPException(status_code=500, detail="Database error while signing up")


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, email: str):
    """Unregister a student from an activity"""
    try:
        with get_connection() as conn:
            activity = fetch_activity(activity_name, conn)
            if activity is None:
                raise HTTPException(status_code=404, detail="Activity not found")

            student = conn.execute(
                "SELECT id FROM students WHERE email = ?",
                (email,),
            ).fetchone()

            if student is None:
                raise HTTPException(
                    status_code=400,
                    detail="Student is not signed up for this activity"
                )

            deletion = conn.execute(
                """
                DELETE FROM registrations
                WHERE activity_id = ? AND student_id = ?
                """,
                (activity["id"], student["id"]),
            )

            if deletion.rowcount == 0:
                raise HTTPException(
                    status_code=400,
                    detail="Student is not signed up for this activity"
                )

            return {"message": f"Unregistered {email} from {activity_name}"}
    except sqlite3.Error:
        raise HTTPException(status_code=500, detail="Database error while unregistering")
