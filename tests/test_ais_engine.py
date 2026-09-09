import unittest
from datetime import datetime, timezone
from smartfreight_ais.vesselfinder_provider import VesselFinderAPIProvider
from smartfreight_ais.eta_engine import haversine_distance_nm, calculate_direct_eta, detect_delay_status
from smartfreight_ais.waiting_time_model import get_waiting_time_predictor
from smartfreight_ais.idle_cost_engine import calculate_idle_cost
from smartfreight_ais.congestion_engine import get_port_congestion_timetable
from smartfreight_ais.status_tracker import IRCTCVesselStatusTracker
from smartfreight_ais.member5_bridge import export_to_member5

class TestAISEngine(unittest.TestCase):

    def test_haversine_distance(self):
        dist = haversine_distance_nm(17.683, 83.216, 20.266, 86.88)
        self.assertTrue(150.0 < dist < 300.0)

    def test_vesselfinder_provider(self):
        provider = VesselFinderAPIProvider()
        pos = provider.get_vessel_position(419000000)
        self.assertEqual(pos["mmsi"], 419000000)
        self.assertIn("lat", pos)
        self.assertIn("lon", pos)
        self.assertTrue(pos["is_simulated"])

    def test_direct_eta_calculation(self):
        eta = calculate_direct_eta(19.0, 85.0, "INPRD", 10.0)
        self.assertGreater(eta["distance_to_port_nm"], 0)
        self.assertGreater(eta["travel_time_hours"], 0)
        self.assertIn("direct_eta_utc", eta)

    def test_waiting_time_ml_model(self):
        predictor = get_waiting_time_predictor()
        res = predictor.predict("INPRD", "Panamax", dwt_mt=82500, cargo_mt=75000)
        self.assertGreaterEqual(res["expected_waiting_time_hours"], 0.5)
        self.assertGreater(res["expected_turnaround_time_hours"], res["expected_waiting_time_hours"])

    def test_idle_cost_calculator(self):
        res = calculate_idle_cost(24.0, "Panamax")
        self.assertEqual(res["waiting_time_days"], 1.0)
        self.assertEqual(res["estimated_idle_cost_usd"], 18500.0)

    def test_port_congestion_timetable(self):
        tt = get_port_congestion_timetable()
        self.assertGreaterEqual(len(tt), 7)
        ports = [p["port_id"] for p in tt]
        self.assertIn("INPRD", ports)
        self.assertIn("INHAL", ports)

    def test_irctc_vessel_status(self):
        status = IRCTCVesselStatusTracker.get_live_status(dist_nm=25.0, speed_knots=10.0, delay_hours=0.5, waiting_time_hours=5.0)
        self.assertIn("current_stage_code", status)
        self.assertEqual(status["total_stages"], 6)

    def test_member5_export_payload(self):
        payload = export_to_member5(419000000, "Panamax", 75000.0)
        self.assertIn("vessel_eta", payload)
        self.assertIn("expected_waiting_time_hours", payload)
        self.assertIn("expected_turnaround_time_hours", payload)
        self.assertIn("delay_status", payload)
        self.assertIn("estimated_idle_cost_usd", payload)
        self.assertGreater(payload["estimated_idle_cost_usd"], 0)

if __name__ == "__main__":
    unittest.main()
