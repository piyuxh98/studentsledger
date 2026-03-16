import base64
from pathlib import Path

from flask import Flask, redirect, render_template_string, request, url_for

from automation import normalize_phone, sync_students_from_google_sheet
from database import get_connection, init_db

app = Flask(__name__)
init_db()


def load_brand_logo_src():
    logo_path = Path("logo.png")
    if not logo_path.exists() or logo_path.stat().st_size == 0:
        return ""
    encoded = base64.b64encode(logo_path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


BRAND_LOGO_SRC = load_brand_logo_src()

DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Preppers Gurukul Student Desk</title>
    <style>
        :root {
            --paper: #f8f2e8;
            --paper-deep: #efe1cb;
            --ink: #1e1b18;
            --muted: #6b6258;
            --brand: #8f2d1f;
            --brand-deep: #5e1f16;
            --gold: #cb9a43;
            --panel: rgba(255, 251, 245, 0.88);
            --line: rgba(61, 39, 24, 0.12);
            --success: #edf8ef;
            --error: #fff0ee;
            --shadow: 0 20px 60px rgba(70, 43, 25, 0.14);
        }

        * { box-sizing: border-box; }

        body {
            margin: 0;
            font-family: Georgia, "Times New Roman", serif;
            color: var(--ink);
            background:
                radial-gradient(circle at top left, rgba(203, 154, 67, 0.22), transparent 32%),
                radial-gradient(circle at bottom right, rgba(143, 45, 31, 0.12), transparent 25%),
                linear-gradient(180deg, #f7f0e4 0%, #f2e4ce 100%);
        }

        .page {
            max-width: 1280px;
            margin: 0 auto;
            padding: 28px 20px 48px;
        }

        .hero {
            position: relative;
            overflow: hidden;
            padding: 28px;
            border: 1px solid var(--line);
            border-radius: 28px;
            background:
                linear-gradient(135deg, rgba(255, 249, 240, 0.98), rgba(245, 228, 205, 0.88)),
                var(--panel);
            box-shadow: var(--shadow);
        }

        .hero::after {
            content: "";
            position: absolute;
            inset: auto -80px -120px auto;
            width: 280px;
            height: 280px;
            border-radius: 999px;
            background: radial-gradient(circle, rgba(143, 45, 31, 0.18), transparent 70%);
        }

        .hero-top {
            display: flex;
            justify-content: space-between;
            gap: 24px;
            align-items: flex-start;
            margin-bottom: 22px;
        }

        .brand-lockup {
            display: flex;
            gap: 18px;
            align-items: flex-start;
            flex-direction: column;
        }

        .brand-logo {
            width: min(420px, 70vw);
            height: auto;
            display: block;
            object-fit: contain;
            mix-blend-mode: multiply;
            filter: contrast(1.08) brightness(0.96);
        }

        .brand-logo-wrap {
            display: inline-flex;
            align-items: center;
            padding: 10px 14px 10px 6px;
            border-radius: 20px;
            background:
                radial-gradient(circle at left center, rgba(248, 242, 232, 0.96), rgba(248, 242, 232, 0.88) 55%, rgba(248, 242, 232, 0.7));
        }

        h1 {
            margin: 0;
            font-size: clamp(2.2rem, 4.2vw, 4.4rem);
            line-height: 0.95;
        }

        .hero-copy {
            max-width: 760px;
            margin: 0;
            color: var(--muted);
            font-size: 1.04rem;
            line-height: 1.7;
        }

        .hero-meta {
            min-width: 250px;
            padding: 18px;
            border: 1px solid var(--line);
            border-radius: 20px;
            background: rgba(255,255,255,0.52);
            backdrop-filter: blur(8px);
        }

        .hero-meta strong,
        .hero-meta span {
            display: block;
        }

        .hero-meta strong {
            font-size: 0.78rem;
            letter-spacing: 0.16em;
            text-transform: uppercase;
            color: var(--brand);
            margin-bottom: 6px;
        }

        .hero-meta span {
            margin-bottom: 16px;
            color: var(--ink);
            line-height: 1.5;
        }

        .stats {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 14px;
            margin-top: 22px;
        }

        .stat {
            padding: 18px;
            border-radius: 20px;
            border: 1px solid var(--line);
            background: rgba(255,255,255,0.66);
        }

        .stat-label {
            display: block;
            font-size: 0.78rem;
            letter-spacing: 0.16em;
            text-transform: uppercase;
            color: var(--muted);
            margin-bottom: 8px;
        }

        .stat-value {
            display: block;
            font-size: clamp(1.6rem, 3vw, 2.4rem);
            color: var(--brand-deep);
        }

        .layout {
            display: grid;
            grid-template-columns: 380px 1fr;
            gap: 20px;
            margin-top: 20px;
        }

        .panel {
            border: 1px solid var(--line);
            border-radius: 26px;
            background: var(--panel);
            box-shadow: var(--shadow);
            padding: 24px;
            backdrop-filter: blur(10px);
        }

        .panel h2 {
            margin: 0 0 10px;
            font-size: 1.45rem;
        }

        .panel p {
            margin: 0 0 18px;
            color: var(--muted);
            line-height: 1.6;
        }

        .message {
            padding: 14px 16px;
            border-radius: 16px;
            margin-bottom: 16px;
            border: 1px solid var(--line);
        }

        .message.ok { background: var(--success); }
        .message.err { background: var(--error); }

        .field-grid {
            display: grid;
            gap: 12px;
        }

        .field-grid.two {
            grid-template-columns: repeat(2, minmax(0, 1fr));
        }

        label {
            display: block;
            margin-bottom: 6px;
            color: var(--brand-deep);
            font-size: 0.84rem;
            letter-spacing: 0.05em;
            text-transform: uppercase;
        }

        input {
            width: 100%;
            border: 1px solid rgba(76, 53, 36, 0.16);
            border-radius: 16px;
            background: rgba(255,255,255,0.9);
            padding: 14px 15px;
            color: var(--ink);
            font: inherit;
        }

        input:focus {
            outline: 2px solid rgba(203, 154, 67, 0.38);
            border-color: rgba(143, 45, 31, 0.22);
        }

        .button-row {
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
            margin-top: 16px;
        }

        button {
            border: none;
            cursor: pointer;
            border-radius: 999px;
            padding: 13px 20px;
            font: inherit;
            font-weight: 700;
            transition: transform 160ms ease, box-shadow 160ms ease, opacity 160ms ease;
        }

        button:hover {
            transform: translateY(-1px);
        }

        .primary {
            color: #fff7ef;
            background: linear-gradient(135deg, var(--brand), var(--brand-deep));
            box-shadow: 0 12px 24px rgba(94, 31, 22, 0.22);
        }

        .secondary {
            background: linear-gradient(135deg, #d7ab58, #c69037);
            color: #2a1c11;
        }

        .danger {
            color: #fff7ef;
            background: linear-gradient(135deg, #b43a2a, #7b2017);
            box-shadow: 0 12px 24px rgba(123, 32, 23, 0.18);
        }

        .ghost {
            color: var(--brand-deep);
            background: rgba(255, 255, 255, 0.75);
            border: 1px solid rgba(61, 39, 24, 0.12);
        }

        .table-shell {
            overflow: hidden;
            border-radius: 20px;
            border: 1px solid var(--line);
            background: rgba(255,255,255,0.56);
        }

        table {
            width: 100%;
            border-collapse: collapse;
        }

        th, td {
            padding: 16px 14px;
            text-align: left;
            border-bottom: 1px solid rgba(61, 39, 24, 0.08);
            font-size: 0.98rem;
        }

        th {
            background: rgba(143, 45, 31, 0.06);
            color: var(--brand-deep);
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.12em;
        }

        tbody tr:hover {
            background: rgba(203, 154, 67, 0.08);
        }

        .badge {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 8px 12px;
            border-radius: 999px;
            font-size: 0.84rem;
        }

        .badge.gold {
            color: #6d4815;
            background: rgba(203, 154, 67, 0.18);
        }

        .badge.green {
            color: #215535;
            background: rgba(77, 152, 98, 0.14);
        }

        .empty {
            padding: 28px;
            text-align: center;
            color: var(--muted);
        }

        .footer-note {
            margin-top: 18px;
            color: var(--muted);
            font-size: 0.95rem;
        }

        @media (max-width: 1080px) {
            .hero-top,
            .layout,
            .stats {
                grid-template-columns: 1fr;
                display: grid;
            }

            .hero-meta {
                min-width: 0;
            }
        }

        @media (max-width: 760px) {
            .page { padding: 16px; }
            .hero, .panel { padding: 18px; border-radius: 20px; }
            .field-grid.two { grid-template-columns: 1fr; }
            .table-shell { overflow-x: auto; }
            table { min-width: 760px; }
        }
    </style>
</head>
<body>
    <div class="page">
        <section class="hero">
            <div class="hero-top">
                <div>
                    <div class="brand-lockup">
                        <div>
                            <div class="brand-logo-wrap">
                                <img class="brand-logo" src="{{ brand_logo_src }}" alt="Prepper Gurukul logo">
                            </div>
                            <h1>Student Desk</h1>
                        </div>
                    </div>
                    <p class="hero-copy">
                        A focused desk for coaching operations: admissions, course mapping, fee tracking, and Google Sheet sync.
                        Inspired by Gurukul's "course of life" philosophy, while staying fast and practical for the admin team.
                    </p>
                </div>
                <aside class="hero-meta">
                    <strong>Campus</strong>
                    <span>Nagpur, Maharashtra</span>
                    <strong>Focus Areas</strong>
                    <span>Commerce, ACCA, CA, CIMA, BBA and entrance prep</span>
                    <strong>Contact Style</strong>
                    <span>High-touch, mentor-led, joyful learning operations</span>
                </aside>
            </div>

            <div class="stats">
                <div class="stat">
                    <span class="stat-label">Students</span>
                    <span class="stat-value">{{ stats.total_students }}</span>
                </div>
                <div class="stat">
                    <span class="stat-label">Courses Active</span>
                    <span class="stat-value">{{ stats.total_courses }}</span>
                </div>
                <div class="stat">
                    <span class="stat-label">Fees Collected</span>
                    <span class="stat-value">Rs. {{ "%.0f"|format(stats.total_paid) }}</span>
                </div>
                <div class="stat">
                    <span class="stat-label">Fees Due</span>
                    <span class="stat-value">Rs. {{ "%.0f"|format(stats.total_due) }}</span>
                </div>
            </div>
        </section>

        <div class="layout">
            <section class="panel">
                <h2>{{ "Edit Student" if edit_student else "Add Student" }}</h2>
                <p>
                    {{ "Update the selected student record below." if edit_student else "Add fresh admissions here or sync with Google Sheet to keep records updated." }}
                </p>
                <p class="footer-note">The dashboard tries to pull the latest data from Google Sheet on every refresh.</p>

                {% if message %}
                <div class="message ok">{{ message }}</div>
                {% endif %}

                {% if error %}
                <div class="message err">{{ error }}</div>
                {% endif %}

                <form action="{{ '/update/' ~ edit_student['id'] if edit_student else '/add' }}" method="post">
                    <div class="field-grid">
                        <div>
                            <label for="name">Student Name</label>
                            <input id="name" name="name" type="text" placeholder="Rahul Sharma" value="{{ edit_student['name'] if edit_student else '' }}" required>
                        </div>
                        <div>
                            <label for="admission_date">Admission Date</label>
                            <input id="admission_date" name="admission_date" type="date" value="{{ edit_student['admission_date'] if edit_student else '' }}" required>
                        </div>
                        <div>
                            <label for="course">Course</label>
                            <input id="course" name="course" type="text" placeholder="ACCA / BBA / CLAT" value="{{ edit_student['course'] if edit_student else '' }}" required>
                        </div>
                    </div>

                    <div class="field-grid two" style="margin-top: 12px;">
                        <div>
                            <label for="fees_paid">Fees Paid</label>
                            <input id="fees_paid" name="fees_paid" type="number" step="0.01" min="0" placeholder="5000" value="{{ edit_student['fees_paid'] if edit_student else '' }}" required>
                        </div>
                        <div>
                            <label for="fees_due">Fees Due</label>
                            <input id="fees_due" name="fees_due" type="number" step="0.01" min="0" placeholder="10000" value="{{ edit_student['fees_due'] if edit_student else '' }}" required>
                        </div>
                    </div>

                    <div style="margin-top: 12px;">
                        <label for="phone">Phone Number</label>
                        <input id="phone" name="phone" type="text" placeholder="919876543210" value="{{ edit_student['phone'] if edit_student else '' }}" required>
                    </div>

                    <div class="button-row">
                        <button class="primary" type="submit">{{ "Update Student" if edit_student else "Save Student" }}</button>
                        {% if edit_student %}
                        <a href="/" style="text-decoration: none;">
                            <button class="ghost" type="button">Cancel Edit</button>
                        </a>
                        {% endif %}
                    </div>
                </form>

                <div class="button-row">
                    <form action="/sync-sheet" method="post">
                        <button class="secondary" type="submit">Sync from Google Sheet</button>
                    </form>
                    <form action="/clear" method="post" onsubmit="return confirm('Clear the entire dashboard ledger?');">
                        <button class="danger" type="submit">Clear Ledger</button>
                    </form>
                </div>

                <p class="footer-note">Sheet columns: <strong>name</strong>, <strong>date_of_admission</strong>, <strong>course</strong>, <strong>fees_paid</strong>, <strong>fees_due</strong>, <strong>phone</strong></p>
            </section>

            <section class="panel">
                <h2>Admissions Ledger</h2>
                <p>Latest student records, course alignment, and fee visibility in one premium desk view.</p>

                {% if students %}
                <div class="table-shell">
                    <table>
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Student</th>
                                <th>Admission</th>
                                <th>Course</th>
                                <th>Paid</th>
                                <th>Due</th>
                                <th>Phone</th>
                                <th>Action</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for student in students %}
                            <tr>
                                <td>{{ student[0] }}</td>
                                <td>
                                    <strong>{{ student[1] }}</strong><br>
                                    {% if student[5] > 0 %}
                                    <span class="badge gold">Pending Dues</span>
                                    {% else %}
                                    <span class="badge green">Cleared</span>
                                    {% endif %}
                                </td>
                                <td>{{ student[2] or "-" }}</td>
                                <td>{{ student[3] or "-" }}</td>
                                <td>Rs. {{ "%.0f"|format(student[4] or 0) }}</td>
                                <td>Rs. {{ "%.0f"|format(student[5] or 0) }}</td>
                                <td>{{ student[6] or "-" }}</td>
                                <td>
                                    <form action="/delete/{{ student[0] }}" method="post" onsubmit="return confirm('Delete this student row?');">
                                        <button class="danger" type="submit">Delete</button>
                                    </form>
                                    <a href="/?edit_id={{ student[0] }}" style="text-decoration: none; display: inline-block; margin-top: 8px;">
                                        <button class="ghost" type="button">Edit</button>
                                    </a>
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
                {% else %}
                <div class="empty">No students have been added yet.</div>
                {% endif %}
            </section>
        </div>
    </div>
</body>
</html>
"""


def get_db():
    return get_connection()


def to_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


@app.route("/")
def dashboard():
    conn = get_db()
    cursor = conn.cursor()
    edit_student = None

    edit_id = request.args.get("edit_id", type=int)
    if edit_id is not None:
        cursor.execute(
            """
            SELECT id, name, admission_date, course, fees_paid, fees_due, phone
            FROM students
            WHERE id = ?
            """,
            (edit_id,),
        )
        edit_student = cursor.fetchone()

    cursor.execute(
        """
        SELECT id, name, admission_date, course, fees_paid, fees_due, phone
        FROM students
        ORDER BY id DESC
        """
    )
    students = cursor.fetchall()
    cursor.execute(
        """
        SELECT
            COUNT(*) AS total_students,
            COUNT(DISTINCT COALESCE(NULLIF(course, ''), '')) AS total_courses,
            COALESCE(SUM(fees_paid), 0) AS total_paid,
            COALESCE(SUM(fees_due), 0) AS total_due
        FROM students
        """
    )
    stats = cursor.fetchone()
    conn.close()

    return render_template_string(
        DASHBOARD_TEMPLATE,
        brand_logo_src=BRAND_LOGO_SRC,
        students=students,
        stats=stats,
        edit_student=edit_student,
        message=request.args.get("message", ""),
        error=request.args.get("error", ""),
    )


@app.route("/add", methods=["POST"])
def add_student():
    name = request.form.get("name", "").strip()
    admission_date = request.form.get("admission_date", "").strip()
    phone = normalize_phone(request.form.get("phone", ""))
    course = request.form.get("course", "").strip()
    fees_paid = to_float(request.form.get("fees_paid", 0))
    fees_due = to_float(request.form.get("fees_due", 0))

    if not admission_date:
        admission_date = request.form.get("date_of_admission", "").strip()

    fees_status = request.form.get("fees_status", "").strip().lower()
    if "paid" == fees_status and fees_due == 0:
        fees_paid = fees_paid or 1
    elif fees_status == "pending" and fees_due == 0:
        fees_due = 1

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO students (name, admission_date, course, fees_paid, fees_due, phone)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (name, admission_date, course, fees_paid, fees_due, phone),
    )
    conn.commit()
    conn.close()
    return redirect(url_for("dashboard", message="Student added successfully."))


@app.route("/update/<int:student_id>", methods=["POST"])
def update_student(student_id):
    name = request.form.get("name", "").strip()
    admission_date = request.form.get("admission_date", "").strip()
    phone = normalize_phone(request.form.get("phone", ""))
    course = request.form.get("course", "").strip()
    fees_paid = to_float(request.form.get("fees_paid", 0))
    fees_due = to_float(request.form.get("fees_due", 0))

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE students
        SET name = ?, admission_date = ?, course = ?, fees_paid = ?, fees_due = ?, phone = ?
        WHERE id = ?
        """,
        (name, admission_date, course, fees_paid, fees_due, phone, student_id),
    )
    updated = cursor.rowcount
    conn.commit()
    conn.close()

    if updated:
        return redirect(url_for("dashboard", message="Student updated successfully."))
    return redirect(url_for("dashboard", error="Student could not be found."))


@app.route("/sync-sheet", methods=["POST"])
def sync_sheet():
    result = sync_students_from_google_sheet()
    if result["ok"]:
        return redirect(url_for("dashboard", message=result["message"]))
    return redirect(url_for("dashboard", error=result["message"]))


@app.route("/delete/<int:student_id>", methods=["POST"])
def delete_student(student_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM students WHERE id = ?", (student_id,))
    deleted = cursor.rowcount
    conn.commit()
    conn.close()

    if deleted:
        return redirect(url_for("dashboard", message="Student deleted successfully."))
    return redirect(url_for("dashboard", error="Student could not be found."))


@app.route("/clear", methods=["POST"])
def clear_students():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM students")
    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    return redirect(url_for("dashboard", message=f"Ledger cleared. {deleted} student records removed."))


if __name__ == "__main__":
    app.run(debug=True)
