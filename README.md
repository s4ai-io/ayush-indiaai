# AYUSH India AI — ML Integration & Database Setup

Complete integration of Python ML pipeline (FastAPI + PostgreSQL) with Next.js frontend.

## 🚀 Quick Start Guide

### Prerequisites
- **Python 3.10+**
- **Node.js 18+**
- **PostgreSQL 14+** (Running locally on port 5432)

---

### 1. Database Setup (PostgreSQL)

1.  Start PostgreSQL (if not running):
    ```bash
    brew services start postgresql
    # OR manually start your postgres server
    ```

2.  Create the database and user:
    ```bash
    psql postgres
    ```
    Inside the `psql` shell:
    ```sql
    CREATE DATABASE ayush_db;
    CREATE USER utsav WITH PASSWORD 'postgres';
    GRANT ALL PRIVILEGES ON DATABASE ayush_db TO utsav;
    \q
    ```

---

### 2. Backend Setup (Python/FastAPI)

1.  **Navigate to backend directory**:
    ```bash
    cd backend
    ```

2.  **Create and activate virtual environment**:
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # Mac/Linux
    # venv\Scripts\activate   # Windows
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment**:
    Create a `.env` file in `backend/` with:
    ```env
    DATABASE_URL=postgresql://utsav:postgres@localhost/ayush_db
    OPENAI_API_KEY=your_openai_key_here
    ```

5.  **Run Migrations & Seed Data**:
    This script creates the 8 tables and imports data from `registrations.json`, CSVs, and GNN service.
    ```bash
    python migrate_data.py
    ```
    *Expected Output:*
    ```
    ✓ All 8 tables created
    ✓ registrations.json → ...
    ✓ health_records.csv → ...
    ...
    Migration Complete!
    ```

6.  **Start the Backend Server**:
    ```bash
    uvicorn main:app --reload --port 8000
    ```
    *Server is running at `http://localhost:8000`*

---

### 3. Frontend Setup (Next.js)

1.  **Navigate to project root** (in a new terminal):
    ```bash
    cd ..
    # or cd /path/to/ayush-indiaai
    ```

2.  **Install dependencies**:
    ```bash
    npm install
    ```

3.  **Configure Environment**:
    Ensure `.env.local` exists with:
    ```env
    NEXT_PUBLIC_API_URL=http://localhost:8000
    PYTHON_BACKEND_URL=http://localhost:8000
    ```

4.  **Start the Frontend**:
    ```bash
    npm run dev
    ```
    *App is running at `http://localhost:3000`*

---

### 4. Verification

1.  **Check API Health**:
    Open [http://localhost:8000/health](http://localhost:8000/health)
    Should return: `{"status": "healthy", "database": "connected", ...}`

2.  **View Analytics Dashboard**:
    Open [http://localhost:8000/api/analytics/dashboard](http://localhost:8000/api/analytics/dashboard)
    Should show aggregated stats (e.g., 800+ patients).

3.  **Test Patient Registration**:
    Go to **Registration Page** on frontend ([http://localhost:3000/registration](http://localhost:3000/registration)).
    Fill the form and submit. It will save directly to the PostgreSQL database.

---

## 📂 Project Structure

```
ayush-indiaai/
├── backend/                  # FastAPI Backend
│   ├── main.py               # API Entry point
│   ├── models_db.py          # SQLAlchemy Models (8 tables)
│   ├── database.py           # DB Connection
│   ├── migrate_data.py       # Data Migration Script
│   ├── services/
│   │   ├── db_service.py     # Database CRUD
│   │   ├── analytics_service.py # Analytics logic (DB-backed)
│   │   ├── ml_service.py     # Treatment Recommendations
│   │   └── ...
│   └── data/                 # Raw CSV/JSON data sources
│
├── src/                      # Next.js Frontend
│   ├── app/                  # App Router Pages
│   ├── components/           # UI Components
│   └── lib/                  # Utilities
└── README.md                 # This file
```

## 🛠 Tech Stack

- **Backend**: Python, FastAPI, PostgreSQL, SQLAlchemy, Pandas, Scikit-learn
- **Frontend**: Next.js 14, TypeScript, Tailwind CSS
- **AI/ML**: Custom ML Pipeline, GNN (Graph Neural Network) for Disease Spread
