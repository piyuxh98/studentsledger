# Preppers Gurukul Student Desk

A small Flask dashboard for managing student entries and syncing records from Google Sheets.

## Features

- Add, edit, delete, and clear student records from the dashboard
- Sync student data from a public Google Sheet CSV link
- Track admission date, course, fees paid, fees due, and phone number
- Use the real `logo.png` branding in the header

## Project Files

- `app.py` - Flask app and dashboard UI
- `automation.py` - Google Sheet sync logic
- `database.py` - SQLite setup and schema
- `serve.py` - clean local runner for the dashboard
- `run_automation.py` - one-off sheet sync runner
- `students.db` - local SQLite database
- `.env` - environment settings

## Required Environment Variable

Add this to `.env`:

```env
GOOGLE_SHEET_CSV_URL=https://docs.google.com/spreadsheets/d/your-sheet-id/export?format=csv&gid=0
```

## Required Google Sheet Columns

The first row in your sheet must contain:

```text
name,date_of_admission,course,fees_paid,fees_due,phone
```

## Run Locally

Start the dashboard:

```powershell
.\.venv\Scripts\python.exe serve.py
```

Open:

```text
http://127.0.0.1:5000
```

## Sync Sheet Manually

You can sync in either of these ways:

- Use the `Sync from Google Sheet` button in the dashboard
- Run:

```powershell
.\.venv\Scripts\python.exe run_automation.py
```

## Notes

- Dashboard delete/edit actions update the local database
- If you sync again from Google Sheet, the sheet becomes the latest source for imported rows
- Keep the local development server terminal open while using the dashboard

## Deploy On Render

This project is prepared for Render deployment.

Files already added for deployment:

- `requirements.txt`
- `render.yaml`

Steps:

1. Put the project in a GitHub repository
2. Push all files, including `logo.png`
3. Create a new Render account or sign in
4. Click `New` -> `Blueprint`
5. Connect your GitHub repository
6. Render will detect `render.yaml`
7. In Render environment variables, set:

```text
GOOGLE_SHEET_CSV_URL
```

8. Deploy the service

After deploy, Render will give you a public URL your sir can open from anywhere.

## Deployment Note

- `students.db` is a local SQLite file
- on cloud hosting, SQLite data may reset on redeploy or restart depending on the platform
- Google Sheet sync will still let you pull fresh data back into the dashboard
