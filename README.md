# Chemical Equipment Parameter Visualizer

A **hybrid Web + Desktop** application for uploading, analyzing, and visualizing chemical equipment CSV data. Both frontends share the same **Django REST** backend.

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend** | Python, Django, Django REST Framework, Pandas, SQLite |
| **Web Frontend** | React, Chart.js, Vite |
| **Desktop Frontend** | PyQt5, Matplotlib |
| **Auth** | HTTP Basic Authentication |

## Features

- **CSV upload** (Web and Desktop) with columns: Equipment Name, Type, Flowrate, Pressure, Temperature
- **Data summary API**: total count, averages (flowrate, pressure, temperature), equipment type distribution
- **Charts**: type distribution and averages (Chart.js on web, Matplotlib on desktop)
- **History**: last 5 uploaded datasets with summary
- **PDF report** generation and download
- **Basic authentication** for all API access

## Project Structure

```
fossee/
├── backend/                 # Django API
│   ├── config/              # Django settings & URLs
│   ├── equipment/           # App: upload, summary, history, PDF
│   ├── manage.py
│   └── requirements.txt
├── frontend-web/            # React + Chart.js
│   ├── src/
│   └── package.json
├── frontend-desktop/        # PyQt5 + Matplotlib
│   ├── main.py
│   ├── api_client.py
│   └── requirements.txt
├── sample_equipment_data.csv
└── README.md
```

## Quick start: run the website

1. **Terminal 1 – Backend:**  
   `cd backend` → activate venv → `pip install -r requirements.txt` → `python manage.py migrate` → `python manage.py create_demo_user` → `python manage.py runserver`

2. **Terminal 2 – Web:**  
   `cd frontend-web` → `npm install` → `npm run dev`

3. **Browser:** Open **http://localhost:5173** and sign in with **admin** / **admin**.

---

## Setup

### 1. Backend (Django)

```bash
cd backend
python -m venv .venv

# Windows
.\.venv\Scripts\Activate.ps1

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
python manage.py migrate
python manage.py create_demo_user
python manage.py runserver
```

- API: **http://localhost:8000/api/**
- Demo user: **admin** / **admin**

### 2. Web Frontend (React)

```bash
cd frontend-web
npm install
npm run dev
```

- App: **http://localhost:5173**
- Vite proxies `/api` to `http://localhost:8000` (ensure backend is running).

### 3. Desktop Frontend (PyQt5)

```bash
cd frontend-desktop
python -m venv .venv

# Windows
.\.venv\Scripts\Activate.ps1

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
python main.py
```

- Backend must be running at **http://localhost:8000** (or set `API_BASE`).

### 4. Sample Data

Use `sample_equipment_data.csv` in the project root for uploads. The file dialog in the desktop app opens in the project root by default.

## API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/api/upload/` | Basic | Upload CSV (`file` form field) |
| `GET` | `/api/summary/<id>/` | Basic | Summary for upload |
| `GET` | `/api/data/<id>/` | Basic | Raw data for upload |
| `GET` | `/api/history/` | Basic | Last 5 uploads |
| `GET` | `/api/report/<id>/pdf/` | Basic | Download PDF report |

## Usage

1. **Sign in** with `admin` / `admin` (or another user you create).
2. **Upload** a CSV with columns: `Equipment Name`, `Type`, `Flowrate`, `Pressure`, `Temperature`.
3. View **summary**, **charts**, and **data table**; use **History** to switch between recent uploads.
4. **Download PDF report** for the selected upload.

## Submission

- **Source**: this repository (backend + both frontends)
- **README**: this file
- **Demo video**: 2–3 minutes
- **Optional**: deployment link for the web version

Submit via: [Google Form](https://forms.gle/bSiKezbM4Ji9xnw66)

## License

MIT.
