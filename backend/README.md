# AYUSH ML Backend

FastAPI backend for the AYUSH ML Pipeline.

## Setup

1. Create virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Ensure ML models are trained:
```bash
# If models don't exist in models/ directory, train them:
cd ..
python ayush_calude/ayush_ml_pipeline.py
# This will generate .pkl files, copy them to backend/models/
cp ayush_calude/*.pkl backend/models/
```

4. Copy trend data:
```bash
cp ayush_calude/public_health_trends.csv backend/data/
```

## Running the Server

```bash
# Development mode with auto-reload
uvicorn main:app --reload --port 8000

# Or using Python directly
python main.py
```

The API will be available at:
- API: http://localhost:8000
- Swagger Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### Health Check
- `GET /health` - Check API health status

### ML Recommendations
- `POST /api/recommend` - Get personalized treatment recommendation
  - Request body: PatientProfile (age, gender, prakriti, vikriti, disease, severity, bmi)
  - Response: TreatmentRecommendation (herbs, yoga, diet, lifestyle, predictions)

### Disease Forecasting
- `GET /api/forecast?disease={disease}&months={months}` - Get disease forecast
  - Query params: disease (optional), months (default: 3)
  - Response: ForecastResponse (forecast data, trend, risk level)

- `GET /api/trends` - Get emerging disease trends
  - Response: TrendsResponse (list of emerging trends with risk scores)

## Testing

Test the API using the Swagger UI at http://localhost:8000/docs or use curl:

```bash
# Health check
curl http://localhost:8000/health

# Get recommendation
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

# Get forecast
curl "http://localhost:8000/api/forecast?disease=Diabetes&months=3"

# Get emerging trends
curl http://localhost:8000/api/trends
```

## Directory Structure

```
backend/
├── main.py                    # FastAPI application
├── ayush_ml_pipeline.py       # Refactored ML pipeline
├── disease_forecaster.py      # Refactored forecaster
├── requirements.txt           # Python dependencies
├── services/
│   ├── ml_service.py         # ML service wrapper
│   └── forecast_service.py   # Forecast service wrapper
├── utils/
│   └── validators.py         # Pydantic models
├── models/                    # Trained ML models (.pkl files)
└── data/                      # Training/trend data
```

## Notes

- The backend runs independently from the Next.js frontend
- CORS is configured to allow requests from localhost:3000
- Models are loaded once on startup for better performance
- If models are not found, the service will use rule-based recommendations
