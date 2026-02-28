# AYUSH India AI

An AI-powered Ayurvedic healthcare platform that integrates traditional AYUSH knowledge with modern ML — covering patient registration, AI-driven clinical consultation, treatment planning, and public health surveillance.

---

## 🏗️ Architecture Overview

```
ayush-app/
├── backend/              # Python FastAPI ML Backend
│   ├── main.py           # API entry point (all routes)
│   ├── services/         # Business logic
│   │   ├── ayurgenix_service.py    # AyurGenix treatment recommendation engine
│   │   ├── csv_service.py          # CSV-based data persistence layer
│   │   ├── analytics_service.py    # Public health analytics
│   │   ├── forecast_service.py     # Disease forecasting (ARIMA/trend)
│   │   ├── gnn_service.py          # Spatiotemporal GNN for disease spread
│   │   ├── consultation_agent.py   # Copilot consultation agent router
│   │   ├── registration_agent.py   # Copilot registration agent router
│   │   ├── treatment_agent.py      # Copilot treatment agent router
│   │   └── admin_router.py         # Admin evaluation & accuracy endpoints
│   ├── utils/
│   │   ├── validators.py           # Pydantic v2 request/response schemas
│   │   ├── llm_config.py           # LLM binding selector (OpenAI / vLLM)
│   │   ├── llm_logger.py           # LLM I/O logging (writes to logs/)
│   │   └── agent/                  # AG-UI agent workflow implementation
│   │       ├── AGUIChatWorkflow.py
│   │       └── ag_ui_router.py
│   ├── modal_asr/                  # Modal.run cloud GPU services
│   │   ├── modal_vllm_phi4.py      # vLLM Phi-4 inference (2× L40S GPU)
│   │   ├── app.py                  # AI4Bharat ASR (speech-to-text)
│   │   └── app_translate.py        # AI4Bharat translation (Indic ↔ English)
│   ├── data/                       # CSV data files (source of truth)
│   │   ├── patients.csv
│   │   ├── medical_records.csv
│   │   ├── ayush_treatments.csv
│   │   ├── treatment_feedback.csv
│   │   └── AyurGenixAI_Dataset.csv # Core Ayurvedic knowledge base
│   ├── logs/
│   │   └── model_interactions/     # Timestamped LLM input/output logs
│   ├── docs/
│   │   ├── AyurGenixAI_Model_Report.md
│   │   └── AyurGenixAI_OnePager.md
│   ├── disease_forecaster.py
│   ├── requirements.txt
│   ├── run.sh                      # Quick backend start script
│   └── .env                        # Backend environment variables
│
├── src/                            # Next.js 16 Frontend (App Router)
│   ├── app/
│   │   ├── page.tsx                # Landing page (role selector)
│   │   ├── layout.tsx
│   │   ├── registration/           # Patient registration flow
│   │   ├── patients/               # Patient queue & search
│   │   ├── doctor/                 # Doctor's consultation & diagnosis
│   │   │   └── treatment/[visit_id]/ # AI treatment plan generation
│   │   ├── visits/                 # Visit detail (read-only)
│   │   ├── consultation/           # Consultation copilot
│   │   ├── public-health/          # Command center dashboard
│   │   ├── forecasting/            # Disease forecasting view
│   │   ├── trends/                 # Emerging trends view
│   │   ├── admin/                  # Admin accuracy evaluation
│   │   ├── actions/                # Next.js server actions
│   │   └── api/
│   │       ├── copilotkit/         # CopilotKit runtime endpoint
│   │       ├── transcribe/         # Proxy → Modal ASR
│   │       ├── translate/          # Proxy → Modal Translation
│   │       └── ml/                 # Server-side proxies to FastAPI
│   ├── components/
│   │   ├── VoiceInputButton.tsx    # Voice input with language selector
│   │   ├── LanguageSelector.tsx    # Indian language picker
│   │   ├── charts/                 # Recharts wrappers
│   │   ├── forms/                  # Shared form components
│   │   ├── layout/                 # Navigation & shell
│   │   └── ui/                     # shadcn/ui primitives
│   ├── lib/
│   │   ├── config.ts               # API base URL config (read from env)
│   │   ├── logger.ts
│   │   └── api/
│   ├── types/
│   │   ├── index.ts                # Barrel export
│   │   ├── clinical.ts             # Patient & clinical types
│   │   ├── ml.ts                   # ML recommendation types
│   │   └── public-health.ts        # Analytics & forecasting types
│   └── data/
│
├── package.json
├── next.config.ts
├── tsconfig.json
├── setup.sh                        # Full-stack one-shot setup script
└── .env.local                      # Frontend environment variables
```

---

## 🛠️ Tech Stack

### Backend
| Layer | Technology |
|---|---|
| API Framework | **FastAPI** 0.115 + **uvicorn** |
| Data Validation | **Pydantic v2** |
| Persistence | **PostgreSQL** via SQLAlchemy (`models.py`) |
| ML / Recommendation | **Scikit-learn**, **Pandas**, **NumPy** (AyurGenixAI dataset) |
| Disease Forecasting | **ARIMA**, trend analysis, **NetworkX** GNN |
| Copilot Agents | **CopilotKit** + **AG-UI Protocol** + **LlamaIndex** |
| LLM (default) | **Microsoft Phi-4** via **vLLM** on Modal.run |
| LLM (fallback) | **OpenAI GPT-4o** |
| Speech-to-Text | **AI4Bharat ASR** (multilingual Indic, on Modal.run) |
| Translation | **AI4Bharat IndicTrans** (Indic ↔ English, on Modal.run) |

### Frontend
| Layer | Technology |
|---|---|
| Framework | **Next.js 16** (App Router) + **React 19** |
| Language | **TypeScript** |
| Styling | **Tailwind CSS v4** |
| UI Components | **shadcn/ui** (Radix UI primitives) |
| Charts | **Recharts** |
| Copilot UI | **@copilotkit/react-ui**, **@copilotkit/react-core** |
| Icons | **Lucide React** |

---

## 🚀 Quick Start

### Prerequisites
- **Python 3.10+**
- **Node.js 18+** and npm
- **PostgreSQL** (running locally)

> **Database Required.** Data persistence is handled via PostgreSQL, seeded initially from local CSV files.

---

### 1. Backend Setup

```bash
cd backend

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate        # Mac / Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env            # or create .env manually (see below)

# Set up Database
# Ensure PostgreSQL is installed and running locally.
# Create a database named `ayush_db` (or alter DATABASE_URL in .env)
# Seed the initial data from the CSV files into PostgreSQL:
python migrate_csv_postgres.py

# Start the backend
python main.py
# → Running at http://localhost:8000
# → Docs at   http://localhost:8000/docs
```

**`backend/.env` reference:**
```env
# ── LLM ───────────────────────────────────────────────────────────────
# Binding: "openai" | "vllm"
LLM_BINDING=vllm
LLM_MODEL=microsoft/phi-4

# vLLM endpoint (only used when LLM_BINDING=vllm)
VLLM_API_HOST=https://<your-modal-endpoint>/v1
VLLM_API_KEY=dummy-key

# OpenAI (used when LLM_BINDING=openai or as fallback)
OPENAI_API_KEY=sk-...

# ── Server ─────────────────────────────────────────────────────────────
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000

# ── CORS ───────────────────────────────────────────────────────────────
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001
```

Alternatively, use the convenience script:
```bash
cd backend
./run.sh              # activates venv, checks data files, starts server
./run.sh --port 8080  # custom port
./run.sh --no-reload  # disable hot-reload
```

---

### 2. Frontend Setup

```bash
# From project root
npm install

# Configure environment
# (create .env.local if it doesn't exist)
cat > .env.local << 'EOF'
NEXT_PUBLIC_API_URL=http://localhost:8000
PYTHON_BACKEND_URL=http://localhost:8000
NEXT_PUBLIC_COPILOT_URL=/api/copilotkit

# Modal.run ASR & Translation endpoints
MODAL_ASR_URL=https://<your-modal-asr-endpoint>/transcribe
MODAL_TRANSLATE_URL=https://<your-modal-translate-endpoint>/translate
EOF

npm run dev
# → App running at http://localhost:3000
```

---

### 3. One-shot Setup (first run)

For a fully automated setup of both backend and frontend:

```bash
# From project root
chmod +x setup.sh
./setup.sh
```

This will:
1. Create and populate the Python virtual environment
2. Install Node.js dependencies
3. Create `.env.local` if not present

---

## 🌐 Key API Routes

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `POST` | `/api/patients` | Register a new patient |
| `GET` | `/api/patients` | List all patients (`?status=pending\|completed`) |
| `GET` | `/api/patients/search?q=` | Search patients by name / mobile |
| `GET` | `/api/patients/{id}` | Get patient by ID |
| `GET` | `/api/patients/{id}/history` | Full visit history |
| `POST` | `/api/consultations` | Record a new consultation (visit) |
| `GET` | `/api/consultations/{visit_id}/treatment` | Get visit context for treatment generation |
| `GET` | `/api/visits/{visit_id}` | Full visit details (read-only) |
| `POST` | `/api/recommend` | Get AI treatment recommendation |
| `GET` | `/api/diseases` | List all diseases (`?q=search`) |
| `GET` | `/api/diseases/suggestions?q=` | Fuzzy disease name suggestions |
| `POST` | `/api/prescribe` | Save doctor's final prescription |
| `POST` | `/api/feedback` | Submit feedback for continuous learning |
| `GET` | `/api/forecast` | Disease forecast (`?disease=&months=`) |
| `GET` | `/api/trends` | Emerging disease trends |
| `GET` | `/api/analytics/dashboard` | Public health dashboard summary |
| `GET` | `/api/analytics/trends` | Disease trends over time |
| `GET` | `/api/analytics/hotspots` | Location-based disease hotspots |
| `GET` | `/api/analytics/alerts` | Active outbreak alerts |
| `GET` | `/api/analytics/predictions` | GNN-based spread predictions |
| `POST` | `/api/copilot/consultation/...` | CopilotKit consultation agent |
| `POST` | `/api/copilot/registration/...` | CopilotKit registration agent |
| `POST` | `/api/copilot/treatment/...` | CopilotKit treatment agent |
| `GET` | `/api/admin/accuracy` | Accuracy evaluation (admin) |

Full interactive docs: **[http://localhost:8000/docs](http://localhost:8000/docs)**

---

## 🤖 Copilot Agents

The platform uses three **CopilotKit + AG-UI** agents backed by **LlamaIndex**:

| Agent | Route prefix | Purpose |
|---|---|---|
| **Registration Agent** | `/api/copilot/registration` | Voice + form-driven patient registration |
| **Consultation Agent** | `/api/copilot/consultation` | Clinical assessment & diagnosis guidance |
| **Treatment Agent** | `/api/copilot/treatment` | AI-crafted Ayurvedic treatment plan generation |

LLM selection is controlled by the `LLM_BINDING` environment variable (`vllm` → Phi-4, `openai` → GPT-4o).

---

## 🗣️ Voice & Language Support

Voice input is powered by **AI4Bharat ASR** (AI4Bharat multilingual model, hosted on Modal.run):

- Supported languages include Hindi, Tamil, Telugu, Kannada, Malayalam, Bengali, Gujarati, Marathi, Punjabi, Odia, Urdu, and more.
- Language selection is available in the `LanguageSelector` / `VoiceInputButton` component.
- Translation (Indic ↔ English) is via **AI4Bharat IndicTrans**.

---

## ☁️ Modal.run Cloud Services

Three Modal.run deployments power the cloud-based AI:

| Service | File | GPU |
|---|---|---|
| Phi-4 vLLM Inference | `backend/modal_asr/modal_vllm_phi4.py` | 2× L40S |
| ASR (Speech-to-Text) | `backend/modal_asr/app.py` | — |
| Translation | `backend/modal_asr/app_translate.py` | — |

To deploy:
```bash
modal deploy backend/modal_asr/modal_vllm_phi4.py
modal deploy backend/modal_asr/app.py
modal deploy backend/modal_asr/app_translate.py
```

Update the resulting endpoint URLs in `backend/.env` (`VLLM_API_HOST`) and `.env.local` (`MODAL_ASR_URL`, `MODAL_TRANSLATE_URL`).

---

## 📋 User Roles & Workflows

The app is role-based with three entry points from the landing page:

| Role | URL | Workflows |
|---|---|---|
| **Reception** | `/registration` | Register patients, manage queue |
| **Doctor** | `/doctor` | Diagnose, generate treatment, give feedback |
| **Public Health** | `/public-health/dashboard` | Monitor outbreaks, view forecasts, hotspots |

---

## 📊 Data Files

All runtime data is stored as CSV files in `backend/data/`:

| File | Description |
|---|---|
| `patients.csv` | Patient demographics |
| `medical_records.csv` | Consultation records / diagnoses |
| `ayush_treatments.csv` | Prescribed AYUSH treatment plans |
| `treatment_feedback.csv` | Doctor ratings & feedback (ML loop) |
| `AyurGenixAI_Dataset.csv` | Ayurvedic disease–treatment knowledge base |
| `Codified_Ayurvedic_disease.csv` | National Ayurveda Morbidity Codes mapping |
| `public_health_trends.csv` | Aggregated public health trend data |

---

## 📝 LLM I/O Logging

All model inputs and outputs are automatically logged to timestamped files under:
```
backend/logs/model_interactions/
```
Implemented in `backend/utils/llm_logger.py`.

---

## 📖 Documentation

- [AyurGenix Model Report](backend/docs/AyurGenixAI_Model_Report.md) — detailed ML pipeline documentation
- [AyurGenix One-Pager](backend/docs/AyurGenixAI_OnePager.md) — high-level project overview
