import sqlite3

DB_PATH = "students.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_column(cursor, table_name, column_name, definition):
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = {row[1] for row in cursor.fetchall()}
    if column_name not in columns:
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}")


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            admission_date TEXT,
            course TEXT,
            fees_paid REAL DEFAULT 0,
            fees_due REAL DEFAULT 0,
            phone TEXT
        )
        """
    )

    ensure_column(cursor, "students", "admission_date", "TEXT")
    ensure_column(cursor, "students", "course", "TEXT")
    ensure_column(cursor, "students", "fees_paid", "REAL DEFAULT 0")
    ensure_column(cursor, "students", "fees_due", "REAL DEFAULT 0")
    ensure_column(cursor, "students", "phone", "TEXT")

    conn.commit()
    conn.close()


init_db()
