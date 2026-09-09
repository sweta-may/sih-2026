# SmartFreight AI — Task 8 Frontend

React + Vite dashboard connected to the Task 7 FastAPI backend.

## Run

1. Keep FastAPI running:
   `uvicorn app:app --reload`
2. Open this folder in a terminal.
3. Install packages:
   `npm install`
4. Start frontend:
   `npm run dev`
5. Open the Vite URL shown in the terminal, normally:
   `http://localhost:5173`

The frontend calls:
`http://127.0.0.1:8000/forecast`

## Demo flow

Select Capesize / Panamax / Supramax / Handysize and click RUN FORECAST.
The dashboard displays current rate, model, 7/14/30 forecasts, recommended entry window,
and the CHART NOW / WAIT decision.
