import csv
import json
import os
from pathlib import Path
import urllib.error
import urllib.parse
import urllib.request

from database import get_connection, init_db


init_db()


def load_env_file():
    env_path = Path(".env")
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def to_float(value):
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def normalize_phone(phone):
    return (phone or "").strip().replace(" ", "")


def fetch_students_from_sheet():
    load_env_file()
    csv_url = os.getenv("GOOGLE_SHEET_CSV_URL", "").strip()
    if not csv_url:
        return {
            "ok": False,
            "message": "Google Sheet URL is not set in .env.",
            "students": [],
        }

    try:
        with urllib.request.urlopen(csv_url, timeout=30) as response:
            rows = response.read().decode("utf-8")
    except urllib.error.URLError as exc:
        return {
            "ok": False,
            "message": f"Google Sheet could not be read: {exc}",
            "students": [],
        }

    reader = csv.DictReader(rows.splitlines())
    students = []

    for row in reader:
        students.append(
            {
                "name": (row.get("name") or "").strip(),
                "admission_date": (row.get("date_of_admission") or "").strip(),
                "course": (row.get("course") or "").strip(),
                "fees_paid": to_float(row.get("fees_paid")),
                "fees_due": to_float(row.get("fees_due")),
                "phone": normalize_phone(row.get("phone")),
            }
        )

    return {"ok": True, "message": "Sheet data loaded.", "students": students}


def post_sheet_action(payload):
    load_env_file()
    write_url = os.getenv("GOOGLE_SHEET_WRITE_URL", "").strip()
    if not write_url:
        return {
            "ok": False,
            "message": "Google Sheet write URL is not set. Add GOOGLE_SHEET_WRITE_URL in .env.",
        }

    request = urllib.request.Request(
        write_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        return {
            "ok": False,
            "message": f"Google Sheet write failed: {exc}",
        }
    except json.JSONDecodeError:
        return {
            "ok": False,
            "message": "Google Sheet write failed: invalid JSON response.",
        }

    if not data.get("ok", False):
        return {
            "ok": False,
            "message": data.get("message", "Google Sheet write failed."),
        }

    return {"ok": True, "message": data.get("message", "Google Sheet updated successfully.")}


def add_student_to_google_sheet(student):
    return post_sheet_action({"action": "upsert", "student": student})


def delete_student_from_google_sheet(name, phone):
    return post_sheet_action(
        {
            "action": "delete",
            "student": {
                "name": name,
                "phone": normalize_phone(phone),
            },
        }
    )


def sync_students_from_google_sheet():
    sheet_result = fetch_students_from_sheet()
    if not sheet_result["ok"]:
        return sheet_result

    conn = get_connection()
    cursor = conn.cursor()
    synced_count = 0
    keys = []

    for student in sheet_result["students"]:
        if not student["name"]:
            continue

        key = (student["name"], student["phone"])
        keys.append(key)

        cursor.execute(
            """
            SELECT id FROM students
            WHERE name = ? AND phone = ?
            """,
            (student["name"], student["phone"]),
        )
        existing = cursor.fetchone()

        if existing:
            cursor.execute(
                """
                UPDATE students
                SET admission_date = ?, course = ?, fees_paid = ?, fees_due = ?
                WHERE id = ?
                """,
                (
                    student["admission_date"],
                    student["course"],
                    student["fees_paid"],
                    student["fees_due"],
                    existing["id"],
                ),
            )
        else:
            cursor.execute(
                """
                INSERT INTO students (name, admission_date, course, fees_paid, fees_due, phone)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    student["name"],
                    student["admission_date"],
                    student["course"],
                    student["fees_paid"],
                    student["fees_due"],
                    student["phone"],
                ),
            )

        synced_count += 1

    # Hard delete: remove rows that are absent in the latest sheet
    if keys:
        placeholders = ",".join(["(?, ?)"] * len(keys))
        flat_keys = [item for pair in keys for item in pair]
        cursor.execute(
            f"DELETE FROM students WHERE (name, phone) NOT IN ({placeholders})",
            flat_keys,
        )
        deleted_count = cursor.rowcount
    else:
        cursor.execute("DELETE FROM students")
        deleted_count = cursor.rowcount

    conn.commit()
    conn.close()

    return {
        "ok": True,
        "message": f"{synced_count} students inserted or updated, {deleted_count} deleted.",
    }
