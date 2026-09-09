# SmartFreight AI — Task 7: FastAPI Decision API

## What it does
- Loads the selected Random Forest models for 7/14/30 horizons.
- Loads the engineered KOBC historical dataset.
- Returns current rate, 7/14/30 forecasts, percentage changes, recommended entry window, and CHART NOW/WAIT signal.

## Run locally
```bash
pip install -r requirements.txt
uvicorn app:app --reload
```

Open:
- http://127.0.0.1:8000/
- http://127.0.0.1:8000/docs

## API request
POST `/forecast`

JSON:
```json
{
  "vessel_type": "Capesize"
}
```

## Expected decision logic
The API selects the horizon with the lowest forecast rate:
- If that forecast is below the current rate -> `WAIT`
- Otherwise -> `CHART NOW`

## Important modeling note
The current training targets represent future observations in the KOBC working-day series, so the 7/14/30 horizons are not guaranteed calendar-day intervals. This should be addressed in a future production version by explicitly resampling to calendar-day frequency or defining the horizon as working-day observations.

This API is a decision-support prototype, not a guarantee of future freight prices.
