# AYUSH ML Pipeline Integration

Complete integration of Python ML pipeline with Next.js frontend using FastAPI.

## 🚀 Quick Start

### Option 1: Automated Setup (Recommended)

```bash
# Run the setup script
./setup.sh

# Then start both servers:

# Terminal 1 - Python Backend
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
uvicorn main:app --reload --port 8000

# Terminal 2 - Next.js Frontend
npm run dev
```

### Option 2: Manual Setup

#### Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy ML models (if not already trained)
cp ../ayush_calude/*.pkl models/
cp ../ayush_calude/public_health_trends.csv data/

# Start backend
uvicorn main:app --reload --port 8000
```

#### Frontend Setup

```bash
# Install dependencies
npm install

# Start frontend
npm run dev
```

## 📋 What's Been Implemented

### ✅ Backend (Python/FastAPI)

- **Refactored ML Pipeline** (`backend/ayush_ml_pipeline.py`)
  - Fixed hardcoded file paths
  - Added model loading functionality
  - Created API-friendly wrapper methods
  - Input validation

- **Disease Forecaster** (`backend/disease_forecaster.py`)
  - Refactored with relative paths
  - API-ready methods

- **FastAPI Application** (`backend/main.py`)
  - `POST /api/recommend` - Get ML-powered treatment recommendations
  - `GET /api/forecast` - Get disease forecasts
  - `GET /api/trends` - Get emerging disease trends
  - `GET /health` - Health check endpoint
  - CORS configured for Next.js
  - Automatic service initialization on startup

- **Service Wrappers**
  - `services/ml_service.py` - ML recommendation service
  - `services/forecast_service.py` - Disease forecasting service

- **Pydantic Validators** (`utils/validators.py`)
  - Type-safe request/response models
  - Input validation

### ✅ Frontend (Next.js/TypeScript)

- **API Client** (`src/lib/api/ml-client.ts`)
  - TypeScript interfaces for all API types
  - Error handling with custom `MLAPIError` class
  - Validation utilities
  - Functions: `getMLRecommendation()`, `getDiseaseForecast()`, `getEmergingTrends()`

- **Next.js API Routes** (`src/app/api/ml/`)
  - `/api/ml/recommend` - Proxies to Python backend
  - `/api/ml/forecast` - Proxies forecast requests
  - `/api/ml/trends` - Proxies trends requests
  - `/api/ml/health` - Health check proxy
  - Proper error handling and status codes

- **Updated ConsultationForm** (`src/components/forms/ConsultationForm.tsx`)
  - **New Fields:**
    - Age input (0-120)
    - Gender selection (Male/Female)
    - BMI calculator (height + weight → BMI)
    - Severity slider (1-10)
    - Prakriti selection (7 options)
    - Vikriti selection (6 options)
  - **ML Integration:**
    - Calls `getMLRecommendation()` API
    - Displays predicted improvement percentage
    - Shows recommended treatment duration
    - Loading states with spinner
    - Error handling with user-friendly messages
  - **Enhanced UI:**
    - Detailed herb recommendations with dosage and benefits
    - Yoga practices with duration and benefits
    - Diet guidelines as bullet points
    - Lifestyle modifications
    - ML prediction cards

## 🎯 Features

### ML-Powered Recommendations
- Personalized treatment based on patient profile
- Dosha-specific herb recommendations
- Yoga and pranayama practices
- Dietary guidelines
- Lifestyle modifications
- Predicted improvement percentage (ML-based)
- Recommended treatment duration

### Disease Forecasting
- Forecast disease cases for next N months
- Trend analysis (increasing/decreasing/stable)
- Risk level assessment (low/moderate/high)

### Emerging Trends Detection
- Identify diseases with increasing case rates
- Growth rate calculation
- Risk scoring
- Alert levels (low/medium/high/critical)

## 📁 Project Structure

```
ayush-app/
├── backend/                          # Python FastAPI backend
│   ├── main.py                       # FastAPI application
│   ├── ayush_ml_pipeline.py          # Refactored ML pipeline
│   ├── disease_forecaster.py         # Refactored forecaster
│   ├── requirements.txt              # Python dependencies
│   ├── services/
│   │   ├── ml_service.py            # ML service wrapper
│   │   └── forecast_service.py      # Forecast service wrapper
│   ├── utils/
│   │   └── validators.py            # Pydantic models
│   ├── models/                       # Trained ML models (.pkl)
│   └── data/                         # Training/trend data
│
├── src/
│   ├── app/
│   │   ├── api/ml/                  # Next.js API routes
│   │   │   ├── recommend/route.ts
│   │   │   ├── forecast/route.ts
│   │   │   ├── trends/route.ts
│   │   │   └── health/route.ts
│   │   ├── page.tsx                 # Dashboard
│   │   ├── triage/                  # Symptom checker
│   │   └── recommendations/         # Treatment recommendations
│   ├── components/
│   │   └── forms/
│   │       └── ConsultationForm.tsx # Updated with ML integration
│   └── lib/
│       └── api/
│           └── ml-client.ts         # TypeScript API client
│
├── .env.local                        # Environment variables
├── setup.sh                          # Automated setup script
└── README.md                         # This file
```

## 🧪 Testing

### Test Backend Independently

```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload --port 8000

# Open Swagger UI
open http://localhost:8000/docs

# Test health endpoint
curl http://localhost:8000/health

# Test recommendation endpoint
curl -X POST http://localhost:8000/api/recommend \
  -H "Content-Type: application/json" \
  -d '{
    "age": 35,
    "gender": "Male",
    "prakriti": "Vata",
    "vikriti": "Vata",
    "disease": "Anxiety",
    "severity": 7,
    "bmi": 24.5
  }'
```

### Test Full Integration

1. Start both servers (backend on 8000, frontend on 3000)
2. Navigate to http://localhost:3000
3. Click "Start Health Check" or go to recommendations page
4. Fill out the consultation form with all fields
5. Click "Generate Treatment Protocol"
6. Verify ML-powered recommendations appear with:
   - Predicted improvement percentage
   - Recommended duration
   - Detailed herb, yoga, diet, and lifestyle recommendations

## 🔧 Configuration

### Environment Variables

**`.env.local`** (Next.js):
```env
PYTHON_BACKEND_URL=http://localhost:8000
NEXT_PUBLIC_API_URL=http://localhost:3000
```

For production, update `PYTHON_BACKEND_URL` to your deployed backend URL.

## 📝 API Documentation

### POST /api/recommend

**Request:**
```json
{
  "age": 35,
  "gender": "Male",
  "prakriti": "Vata",
  "vikriti": "Vata",
  "disease": "Anxiety",
  "severity": 7,
  "bmi": 24.5
}
```

**Response:**
```json
{
  "herbs": [
    {
      "name": "Ashwagandha",
      "dosage": "500mg twice daily",
      "benefits": "Reduces anxiety, improves sleep"
    }
  ],
  "yoga": [...],
  "diet": [...],
  "lifestyle": [...],
  "predicted_improvement": 72.5,
  "recommended_duration_weeks": 8
}
```

### GET /api/forecast?disease=Diabetes&months=3

**Response:**
```json
{
  "disease": "Diabetes",
  "forecast_months": 3,
  "forecast_data": [
    {
      "month": "Month 1",
      "predicted_cases": 150.5
    }
  ],
  "trend": "increasing",
  "risk_level": "moderate"
}
```

## 🚨 Troubleshooting

### Backend not starting
- Ensure Python 3.8+ is installed
- Activate virtual environment
- Check if port 8000 is available

### Models not found
- Copy models from `ayush_calude/` to `backend/models/`
- Or train models: `cd backend && python ayush_ml_pipeline.py`

### Frontend can't connect to backend
- Verify backend is running on port 8000
- Check `.env.local` has correct `PYTHON_BACKEND_URL`
- Check browser console for CORS errors

### "ML service is currently unavailable"
- Ensure Python backend is running
- Check backend logs for errors
- Verify models are loaded (check `/health` endpoint)

## 🎉 Next Steps

### Remaining Tasks (Optional)
- [ ] Update forecasting page with real ML data
- [ ] Update dashboard with ML metrics
- [ ] Add caching for ML predictions (Redis)
- [ ] Add user authentication
- [ ] Deploy backend to cloud (Railway, Render, AWS)
- [ ] Deploy frontend to Vercel

### Future Enhancements
- Real-time predictions as user types
- Historical patient data tracking
- A/B testing for model improvements
- Integration with electronic health records
- Mobile app version

## 📚 Documentation

- **Backend API Docs:** http://localhost:8000/docs (Swagger UI)
- **Backend README:** `backend/README.md`
- **Implementation Plan:** See artifacts in `.gemini/antigravity/brain/`

## 🤝 Contributing

This integration bridges Python ML with Next.js frontend. Key principles:
- Backend handles all ML logic
- Frontend focuses on UX
- API routes act as proxy layer
- Type safety throughout with TypeScript and Pydantic

---

**Built with:** FastAPI, Next.js, scikit-learn, pandas, TypeScript, React
