import pytest
from fastapi.testclient import TestClient
from smartfreight_ais.integrated_pipeline import (
    run_smartfreight_integrated_simulation,
    PORT_CATALOG,
    VESSEL_SPECS,
)
from api.server import app


class TestMember6Integration:
    """
    Test suite for Member 6 Full-Stack and Cross-Module Integration.
    """

    def test_port_catalog_integrity(self):
        assert "INPRD" in PORT_CATALOG
        assert "INHLD" in PORT_CATALOG
        assert "INVTZ" in PORT_CATALOG
        assert "INMAA" in PORT_CATALOG
        for pid, pdata in PORT_CATALOG.items():
            assert "name" in pdata
            assert "lat" in pdata
            assert "lon" in pdata
            assert "max_draft_m" in pdata

    def test_vessel_specs_integrity(self):
        for vclass in ["Handysize", "Supramax", "Panamax", "Capesize"]:
            assert vclass in VESSEL_SPECS
            spec = VESSEL_SPECS[vclass]
            assert spec["nominal_dwt_mt"] > 0
            assert spec["draft_m"] > 0
            assert spec["base_freight_rate_usd_day"] > 0

    def test_end_to_end_simulation_execution(self):
        res = run_smartfreight_integrated_simulation(
            cargo_type="Thermal Coal",
            cargo_quantity_mt=75000.0,
            origin_port_id="INPRD",
            dest_port_id="INHLD",
            urgency="NORMAL",
            contract_duration_preference="MEDIUM_TERM",
            forecast_horizon_days=14,
        )

        assert "executive_summary_card" in res
        assert "vessel_optimization" in res
        assert "freight_forecast" in res
        assert "ais_operations" in res
        assert "charter_decision" in res
        assert "cost_decision" in res
        assert "alerts" in res

        card = res["executive_summary_card"]
        assert card["recommendation"] in ["CHARTER_NOW", "WAIT"]
        assert card["recommended_vessel"] in VESSEL_SPECS
        assert card["charter_now_cost_usd"] > 0
        assert card["expected_wait_cost_usd"] > 0

    def test_fastapi_ports_endpoint(self):
        client = TestClient(app)
        resp = client.get("/api/v1/ports")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "SUCCESS"
        assert len(data["ports"]) >= 5

    def test_fastapi_vessels_specs_endpoint(self):
        client = TestClient(app)
        resp = client.get("/api/v1/vessels/specs")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "SUCCESS"
        assert "Panamax" in data["vessel_specs"]

    def test_fastapi_simulate_post(self):
        client = TestClient(app)
        req_payload = {
            "cargo_type": "Iron Ore",
            "cargo_quantity_mt": 100000.0,
            "origin_port_id": "INVTZ",
            "dest_port_id": "INENR",
            "urgency": "HIGH",
            "contract_duration_preference": "SPOT",
            "forecast_horizon_days": 7,
            "bunker_price_usd_per_mt": 620.0,
        }
        resp = client.post("/api/v1/simulate", json=req_payload)
        assert resp.status_code == 200
        data = resp.json()
        assert "executive_summary_card" in data
        assert data["executive_summary_card"]["recommendation"] in ["CHARTER_NOW", "WAIT"]
