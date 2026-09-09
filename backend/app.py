from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import pandas as pd
import joblib
from pathlib import Path


# ============================================================
# PATH CONFIGURATION
# ============================================================

BASE = Path(__file__).resolve().parent

DATA_FILE = BASE / "freight_feature_engineered_full.csv"


# ============================================================
# LOAD FEATURE-ENGINEERED DATA
# ============================================================

try:
    DATA = pd.read_csv(DATA_FILE)
    DATA["date"] = pd.to_datetime(DATA["date"])
except Exception as e:
    raise RuntimeError(f"Could not load dataset: {e}")


# ============================================================
# LOAD RANDOM FOREST MODELS
# ============================================================

try:

    MODELS = {
        7: joblib.load(BASE / "random_forest_7d.pkl"),
        14: joblib.load(BASE / "random_forest_14d.pkl"),
        30: joblib.load(BASE / "random_forest_30d.pkl")
    }

except Exception as e:
    raise RuntimeError(f"Could not load Random Forest models: {e}")


# ============================================================
# VESSEL TYPE ENCODING
# ============================================================

VESSEL_CODE = {

    "Handysize": 0,
    "Supramax": 1,
    "Panamax": 2,
    "Capesize": 3

}


# ============================================================
# FEATURES USED BY THE RANDOM FOREST MODEL
# ============================================================

FEATURES = [

    "vessel_type_code",

    "freight_rate_usd_day",

    "lag_1",
    "lag_3",
    "lag_7",
    "lag_14",

    "rolling_mean_7",
    "rolling_mean_14",
    "rolling_mean_30",

    "rolling_std_7",
    "rolling_std_14",

    "day_of_week",
    "month",
    "quarter",
    "day_of_month",

    "rate_change_1d",
    "rate_change_7d",

    "rate_pct_change_1d",
    "rate_pct_change_7d"

]


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(

    title="SmartFreight AI - Freight Forecasting API",

    version="1.0.0",

    description=(
        "AI-powered dry-bulk freight forecasting "
        "and market-entry decision engine."
    )

)


# ============================================================
# CORS CONFIGURATION
# ============================================================

app.add_middleware(

    CORSMiddleware,

    allow_origins=[

        "http://localhost:5173",

        "http://127.0.0.1:5173"

    ],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"]

)


# ============================================================
# REQUEST MODEL
# ============================================================

class ForecastRequest(BaseModel):

    vessel_type: str = Field(

        ...,

        description=(
            "Vessel type: "
            "Handysize, Supramax, Panamax, or Capesize"
        )

    )


# ============================================================
# ROOT ENDPOINT
# ============================================================

@app.get("/")
def root():

    return {

        "project": "SmartFreight AI",

        "status": "running",

        "message": "Freight Forecasting API is working",

        "endpoints": [

            "/health",

            "/vessels",

            "/forecast"

        ],

        "docs": "/docs"

    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health():

    return {

        "status": "healthy",

        "data_last_date":
            str(DATA["date"].max().date()),

        "models_loaded": True

    }


# ============================================================
# AVAILABLE VESSEL TYPES
# ============================================================

@app.get("/vessels")
def vessels():

    return {

        "vessel_types": list(VESSEL_CODE.keys())

    }


# ============================================================
# CREATE MODEL INPUT
# ============================================================

def make_feature_row(vessel_type):

    # --------------------------------------------------------
    # Validate vessel type
    # --------------------------------------------------------

    if vessel_type not in VESSEL_CODE:

        raise HTTPException(

            status_code=400,

            detail=(
                "Invalid vessel_type. "
                "Choose Handysize, Supramax, "
                "Panamax, or Capesize."
            )

        )


    # --------------------------------------------------------
    # Filter data for selected vessel
    # --------------------------------------------------------

    vessel_data = DATA[

        DATA["vessel_type"] == vessel_type

    ].sort_values("date").copy()


    # --------------------------------------------------------
    # Check sufficient history
    # --------------------------------------------------------

    if len(vessel_data) < 31:

        raise HTTPException(

            status_code=500,

            detail="Insufficient historical data."

        )


    # --------------------------------------------------------
    # Latest available observation
    # --------------------------------------------------------

    latest_row = vessel_data.iloc[-1]


    # --------------------------------------------------------
    # Create model input
    # --------------------------------------------------------

    X = vessel_data.iloc[[-1]].copy()


    # --------------------------------------------------------
    # IMPORTANT FIX
    #
    # The dataset contains vessel_type but the ML model
    # requires vessel_type_code.
    # --------------------------------------------------------

    X["vessel_type_code"] = VESSEL_CODE[vessel_type]


    # --------------------------------------------------------
    # Check required columns
    # --------------------------------------------------------

    missing_columns = [

        column

        for column in FEATURES

        if column not in X.columns

    ]


    if missing_columns:

        raise HTTPException(

            status_code=500,

            detail=f"Missing feature columns: {missing_columns}"

        )


    # --------------------------------------------------------
    # Keep only model features
    # --------------------------------------------------------

    X = X[FEATURES]


    return latest_row, X


# ============================================================
# FORECAST ENDPOINT
# ============================================================

@app.post("/forecast")
def forecast(request: ForecastRequest):

    # --------------------------------------------------------
    # Get latest data and feature row
    # --------------------------------------------------------

    current_row, X = make_feature_row(

        request.vessel_type

    )


    # --------------------------------------------------------
    # Current freight rate
    # --------------------------------------------------------

    current_rate = float(

        current_row["freight_rate_usd_day"]

    )


    # --------------------------------------------------------
    # Generate forecasts
    # --------------------------------------------------------

    forecasts = {}


    for horizon, model in MODELS.items():

        prediction = float(

            model.predict(X)[0]

        )


        # Percentage change from current rate

        percentage_change = (

            (prediction - current_rate)

            / current_rate

        ) * 100


        forecasts[f"{horizon}_days"] = {

            "forecast_rate_usd_day":
                round(prediction, 2),

            "change_percent_vs_current":
                round(percentage_change, 2)

        }


    # ========================================================
    # FIND BEST ENTRY WINDOW
    # ========================================================

    best_horizon = min(

        forecasts,

        key=lambda h:
            forecasts[h]["forecast_rate_usd_day"]

    )


    best_forecast = forecasts[

        best_horizon

    ]["forecast_rate_usd_day"]


    # ========================================================
    # MARKET ENTRY DECISION
    # ========================================================

    if best_forecast < current_rate:

        market_signal = "WAIT"

    else:

        market_signal = "CHART NOW"


    # ========================================================
    # FINAL RESPONSE
    # ========================================================

    return {

        "vessel_type":
            request.vessel_type,

        "current_date":
            str(current_row["date"].date()),

        "current_rate_usd_day":
            current_rate,

        "forecast":
            forecasts,

        "recommended_entry_window":
            best_horizon,

        "market_entry_signal":
            market_signal,

        "model":
            "Random Forest"

    }