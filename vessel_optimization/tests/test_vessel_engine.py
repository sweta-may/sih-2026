"""
Comprehensive Test Suite for Vessel Type Optimization Engine
Member 3: Vessel Type Optimization (AI-Powered Bulk Cargo Chartering System)
"""

import math
import unittest
from vessel_optimization.data_loader import DataRepository
from vessel_optimization.engine import VesselOptimizationEngine
from vessel_optimization.models import (
    DimensionCheck,
    OptimizationConfig,
    PortCompatibility,
    PortConstraint,
    PortType,
    RecommendationStatus,
    VesselClass,
    VesselEvaluation,
)


class TestVesselOptimizationEngine(unittest.TestCase):
    """Test suite validating all rule-based and optimization behaviors."""

    def setUp(self):
        self.repo = DataRepository()
        self.engine = VesselOptimizationEngine(self.repo)

    # ------------------------------------------------------------------------
    # 1. Exact Boundary Conditions Test (Equality Passes)
    # ------------------------------------------------------------------------
    def test_exact_boundary_conditions_equality_passes(self):
        """
        Validates:
          vessel.draft == port.max_draft -> PASS
          vessel.loa == port.max_loa -> PASS
          vessel.beam == port.max_beam -> PASS
        Only strictly greater (>) must fail.
        """
        # Test port with exact limits
        test_port = PortConstraint(
            port_id="TEST-BOUNDARY",
            port_name="Boundary Port",
            state="TestState",
            country="TestCountry",
            port_type=PortType.BERTH,
            max_draft_m=14.0,
            max_loa_m=200.0,
            max_beam_m=32.0,
            allowed_cargo_types=["Coal"],
        )

        # Vessel 1: Exact equality on all 3 dimensions
        exact_vessel = VesselClass(
            vessel_id="V-EXACT",
            vessel_class="ExactMatch",
            dwt_mt=50000.0,
            loa_m=200.0,
            beam_m=32.0,
            draft_m=14.0,
        )
        checks = self.engine._check_port_dimensions(exact_vessel, test_port, "Test")
        for chk in checks:
            self.assertTrue(chk.is_pass, f"{chk.metric_name} with exact equality should pass!")
            self.assertEqual(chk.margin_m, 0.0)

        # Vessel 2: Exceeding draft by 0.01m
        over_draft_vessel = VesselClass(
            vessel_id="V-OVER-DRAFT",
            vessel_class="OverDraft",
            dwt_mt=50000.0,
            loa_m=195.0,
            beam_m=30.0,
            draft_m=14.01,
        )
        draft_checks = self.engine._check_port_dimensions(over_draft_vessel, test_port, "Test")
        draft_chk = next(c for c in draft_checks if c.metric_name == "Draft")
        self.assertFalse(draft_chk.is_pass, "Draft exceeding by 0.01m should FAIL!")

        # Vessel 3: Exceeding LOA by 0.1m
        over_loa_vessel = VesselClass(
            vessel_id="V-OVER-LOA",
            vessel_class="OverLOA",
            dwt_mt=50000.0,
            loa_m=200.1,
            beam_m=30.0,
            draft_m=13.0,
        )
        loa_checks = self.engine._check_port_dimensions(over_loa_vessel, test_port, "Test")
        loa_chk = next(c for c in loa_checks if c.metric_name == "LOA")
        self.assertFalse(loa_chk.is_pass, "LOA exceeding by 0.1m should FAIL!")

        # Vessel 4: Exceeding Beam by 0.05m
        over_beam_vessel = VesselClass(
            vessel_id="V-OVER-BEAM",
            vessel_class="OverBeam",
            dwt_mt=50000.0,
            loa_m=190.0,
            beam_m=32.05,
            draft_m=13.0,
        )
        beam_checks = self.engine._check_port_dimensions(over_beam_vessel, test_port, "Test")
        beam_chk = next(c for c in beam_checks if c.metric_name == "Beam")
        self.assertFalse(beam_chk.is_pass, "Beam exceeding by 0.05m should FAIL!")

    # ------------------------------------------------------------------------
    # 2. Dynamic Evaluation Test: Scenario 1 (100,000 MT Coal Australia -> Paradip)
    # ------------------------------------------------------------------------
    def test_dynamic_scenario_1_australia_to_paradip(self):
        """
        Evaluates 100,000 MT Coal Australia -> Paradip:
          - Asserts Capesize fails due to draft 18.2m > 16.5m (Paradip bottleneck).
          - Asserts all candidates are evaluated.
          - Asserts eligible vessels proceed to dynamic voyage calculation.
          - Asserts voyage counts and capacity utilization are calculated correctly.
          - Asserts final recommendation is dynamically derived from data without hardcoding.
        """
        cfg = OptimizationConfig(payload_factor=0.95, max_voyages=3)
        res = self.engine.recommend(
            cargo_quantity_mt=100000.0,
            cargo_type="Coal",
            origin_port_input="Australia",
            dest_port_input="Paradip",
            config=cfg,
        )

        # Recommendation must be feasible
        self.assertEqual(res.status, RecommendationStatus.FEASIBLE_RECOMMENDATION)
        self.assertIsNotNone(res.recommended_vessel)
        self.assertIsNotNone(res.recommended_voyage_plan)

        # Bottleneck attribution verification
        self.assertEqual(res.governing_bottlenecks.governing_draft_m, 16.5)
        self.assertIn("Paradip", res.governing_bottlenecks.draft_bottleneck_port)

        # Candidate evaluation verification
        evals = res.candidate_evaluations
        self.assertIn("Capesize", evals)
        self.assertIn("Panamax", evals)
        self.assertIn("Supramax", evals)
        self.assertIn("Handysize", evals)

        # Capesize must be rejected in Stage 1 due to Paradip draft
        self.assertFalse(evals["Capesize"].is_eligible)
        self.assertTrue(
            any("draft" in r.lower() and "16.5" in r for r in evals["Capesize"].rejection_reasons),
            "Capesize must have explicit draft rejection reason citing Paradip draft limit.",
        )

        # Panamax, Supramax, Handysize should be physically eligible
        self.assertTrue(evals["Panamax"].is_eligible)
        self.assertTrue(evals["Supramax"].is_eligible)
        self.assertTrue(evals["Handysize"].is_eligible)

        # Voyage calculation checks
        # Supramax: DWT 58,328 -> effective payload ~55,411 MT -> 100,000 / 55,411 = 2 voyages
        supra_plan = evals["Supramax"].best_voyage_plan
        self.assertEqual(supra_plan.num_voyages, 2)
        self.assertEqual(supra_plan.cargo_per_voyage_mt, 50000.0)
        self.assertAlmostEqual(
            supra_plan.capacity_utilization_pct,
            (100000.0 / (2 * 58328.0 * 0.95)) * 100.0,
            places=1,
        )

        # Panamax: DWT 82,500 -> effective payload ~78,375 MT -> 100,000 / 78,375 = 2 voyages
        pana_plan = evals["Panamax"].best_voyage_plan
        self.assertEqual(pana_plan.num_voyages, 2)
        self.assertEqual(pana_plan.cargo_per_voyage_mt, 50000.0)

        # Handysize: DWT 38,200 -> effective payload ~36,290 MT -> 100,000 / 36,290 = 3 voyages
        handy_plan = evals["Handysize"].best_voyage_plan
        self.assertEqual(handy_plan.num_voyages, 3)

        # Dynamic winner verification:
        # Supramax and Panamax both take 2 voyages, but Supramax achieves ~90.2% utilization
        # vs Panamax ~63.8% utilization (avoiding oversizing deadfreight).
        self.assertEqual(res.recommended_vessel.vessel_class, "Supramax")
        self.assertEqual(res.recommended_voyage_plan.num_voyages, 2)

    # ------------------------------------------------------------------------
    # 3. Haldia River Port Restrictive Condition Test
    # ------------------------------------------------------------------------
    def test_haldia_river_port_draft_bottleneck(self):
        """
        Haldia max draft is 12.2m.
        Capesize (18.2m), Panamax (14.43m), and Supramax (12.8m) must all fail draft.
        Only Handysize (10.538m) should pass Stage 1 physical eligibility.
        """
        res = self.engine.recommend(
            cargo_quantity_mt=75000.0,
            cargo_type="Coal",
            origin_port_input="Indonesia",
            dest_port_input="Haldia",
            config=OptimizationConfig(payload_factor=0.95, max_voyages=3),
        )

        self.assertEqual(res.governing_bottlenecks.governing_draft_m, 12.2)
        self.assertIn("Haldia", res.governing_bottlenecks.draft_bottleneck_port)

        evals = res.candidate_evaluations
        self.assertFalse(evals["Capesize"].is_eligible)
        self.assertFalse(evals["Panamax"].is_eligible)
        self.assertFalse(evals["Supramax"].is_eligible)
        self.assertTrue(evals["Handysize"].is_eligible)

        # Recommendation should be Handysize
        self.assertEqual(res.status, RecommendationStatus.FEASIBLE_RECOMMENDATION)
        self.assertEqual(res.recommended_vessel.vessel_class, "Handysize")
        # 75,000 MT / (0.95 * 38,200) = 75,000 / 36,290 = 3 voyages
        self.assertEqual(res.recommended_voyage_plan.num_voyages, 3)

    # ------------------------------------------------------------------------
    # 4. Gopalpur Draft Test
    # ------------------------------------------------------------------------
    def test_gopalpur_draft_test(self):
        """
        Gopalpur Draft Test: Verifies that Capesize and Panamax fail the 14.2m draft constraint
        while Supramax passes the draft constraint, after which all eligible vessels proceed
        to dynamic voyage optimization and ranking.
        """
        gopalpur = self.repo.get_port("Gopalpur")
        self.assertIsNotNone(gopalpur)
        self.assertEqual(gopalpur.max_draft_m, 14.2)

        australia = self.repo.get_port("Australia")
        self.assertIsNotNone(australia)

        # Check physical compatibility directly in Stage 1
        cape = self.repo.get_vessel("Capesize")
        pana = self.repo.get_vessel("Panamax")
        supra = self.repo.get_vessel("Supramax")

        compat_cape = self.engine.check_vessel_compatibility(cape, australia, gopalpur, "Iron Ore")
        compat_pana = self.engine.check_vessel_compatibility(pana, australia, gopalpur, "Iron Ore")
        compat_supra = self.engine.check_vessel_compatibility(supra, australia, gopalpur, "Iron Ore")

        # Capesize (18.2m) > 14.2m -> FAIL
        self.assertFalse(compat_cape.is_compatible)
        self.assertTrue(any("14.2" in r and "draft" in r.lower() for r in compat_cape.rejection_reasons))

        # Panamax (14.43m) > 14.2m -> FAIL
        self.assertFalse(compat_pana.is_compatible)
        self.assertTrue(any("14.2" in r and "draft" in r.lower() for r in compat_pana.rejection_reasons))

        # Supramax (12.8m) <= 14.2m -> PASS draft constraint!
        draft_checks_supra = [c for c in compat_supra.dest_checks if c.metric_name == "Draft"]
        self.assertTrue(draft_checks_supra[0].is_pass)

        # Now run the full recommendation engine dynamically
        res = self.engine.recommend(
            cargo_quantity_mt=65000.0,
            cargo_type="Iron Ore",
            origin_port_input="Australia",
            dest_port_input="Gopalpur",
            config=OptimizationConfig(payload_factor=0.95, max_voyages=3),
        )

        # Capesize and Panamax must be recorded as rejected
        self.assertIn("Capesize", res.rejection_diagnostics)
        self.assertIn("Panamax", res.rejection_diagnostics)

        # Engine dynamically evaluates eligible vessels (Supramax & Handysize)
        self.assertEqual(res.status, RecommendationStatus.FEASIBLE_RECOMMENDATION)
        self.assertIn(res.recommended_vessel.vessel_class, ["Supramax", "Handysize"])

    # ------------------------------------------------------------------------
    # 5. Sagar-Sandheads Anchorage / Lighterage Operation Test
    # ------------------------------------------------------------------------
    def test_sagar_sandheads_anchorage_handling(self):
        """
        Tests that Sagar-Sandheads is recognized as ANCHORAGE_LIGHTERAGE,
        and does not impose rigid quay LOA/Beam limits.
        """
        sagar = self.repo.get_port("Sagar-Sandheads")
        self.assertIsNotNone(sagar)
        self.assertEqual(sagar.port_type, PortType.ANCHORAGE_LIGHTERAGE)

        # Calling _check_port_dimensions on an anchorage port should not check LOA or Beam
        cape = self.repo.get_vessel("Capesize")
        checks = self.engine._check_port_dimensions(cape, sagar, "Destination")
        metric_names = [c.metric_name for c in checks]
        self.assertNotIn("LOA", metric_names)
        self.assertNotIn("Beam", metric_names)

    # ------------------------------------------------------------------------
    # 6. Configurable Parameters Test (payload_factor and max_voyages)
    # ------------------------------------------------------------------------
    def test_configurable_parameters(self):
        """
        Tests that changing payload_factor and max_voyages changes the effective payload
        and feasibility boundaries as expected.
        """
        # Test custom payload factor
        cfg_high = OptimizationConfig(payload_factor=0.98, max_voyages=3)
        cfg_low = OptimizationConfig(payload_factor=0.85, max_voyages=3)

        supra = self.repo.get_vessel("Supramax")
        plans_high, _ = self.engine.evaluate_voyage_plans(supra, 50000.0, cfg_high)
        plans_low, _ = self.engine.evaluate_voyage_plans(supra, 50000.0, cfg_low)

        self.assertAlmostEqual(plans_high[0].effective_payload_per_voyage_mt, 58328.0 * 0.98)
        self.assertAlmostEqual(plans_low[0].effective_payload_per_voyage_mt, 58328.0 * 0.85)

        # Test max_voyages constraint triggering NO_FEASIBLE_VESSEL
        # Handysize for 100,000 MT needs 3 voyages. If max_voyages=2 and larger vessels are filtered out:
        cfg_strict = OptimizationConfig(payload_factor=0.95, max_voyages=2)
        res = self.engine.recommend(
            cargo_quantity_mt=100000.0,
            cargo_type="Coal",
            origin_port_input="Australia",
            dest_port_input="Haldia",  # Haldia only allows Handysize
            config=cfg_strict,
        )
        self.assertEqual(res.status, RecommendationStatus.NO_FEASIBLE_VESSEL)
        self.assertIn("Handysize", res.rejection_diagnostics)

    # ------------------------------------------------------------------------
    # 7. Anti-Oversizing Test (Prefer appropriately sized vessel if same voyages)
    # ------------------------------------------------------------------------
    def test_anti_oversizing_logic(self):
        """
        When two vessels can both transport cargo in the same number of voyages (e.g. 1 voyage),
        the engine must prefer the appropriately sized vessel (higher utilization, lower deadfreight)
        rather than defaulting to the larger vessel.
        """
        # 50,000 MT parcel can be carried in 1 voyage by Supramax (effective cap ~55.4k MT)
        # and 1 voyage by Panamax (effective cap ~78.4k MT).
        # Supramax gives ~90% utilization; Panamax gives ~64% utilization.
        # Supramax should win!
        res = self.engine.recommend(
            cargo_quantity_mt=50000.0,
            cargo_type="Coal",
            origin_port_input="Australia",
            dest_port_input="Paradip",
            allowed_vessel_classes=["Supramax", "Panamax"],
            config=OptimizationConfig(payload_factor=0.95, max_voyages=3),
        )

        self.assertEqual(res.status, RecommendationStatus.FEASIBLE_RECOMMENDATION)
        self.assertEqual(res.recommended_vessel.vessel_class, "Supramax")
        self.assertEqual(res.recommended_voyage_plan.num_voyages, 1)

    # ------------------------------------------------------------------------
    # 8. Geared-Vessel Tie-Breaker Logic
    # ------------------------------------------------------------------------
    def test_geared_vessel_tie_breaker(self):
        """
        Verifies:
        "If utilization and voyage count are comparable, use vessel operational flexibility
        as a secondary tie-breaker only when the cargo or port handling requirements make
        that capability beneficial. A geared vessel must not automatically be preferred
        over a gearless vessel when gearing provides no operational advantage."
        """
        # Create two mock vessels with identical DWT, LOA, Beam, Draft; one is geared, one gearless
        gearless = VesselClass(
            vessel_id="V-GEARLESS",
            vessel_class="IdenticalGearless",
            dwt_mt=60000.0,
            loa_m=190.0,
            beam_m=32.0,
            draft_m=12.5,
            is_geared=False,
        )
        geared = VesselClass(
            vessel_id="V-GEARED",
            vessel_class="IdenticalGeared",
            dwt_mt=60000.0,
            loa_m=190.0,
            beam_m=32.0,
            draft_m=12.5,
            is_geared=True,
        )

        # Standard port with full shore cranes and standard Coal cargo
        normal_port = PortConstraint(
            port_id="NORM",
            port_name="Normal Port",
            state="St",
            country="Country",
            port_type=PortType.BERTH,
            max_draft_m=15.0,
            max_loa_m=250.0,
            max_beam_m=40.0,
            allowed_cargo_types=["Coal"],
            has_shore_cranes=True,
        )

        cfg = OptimizationConfig(payload_factor=0.95, max_voyages=3)
        plans1, b1 = self.engine.evaluate_voyage_plans(gearless, 55000.0, cfg)
        plans2, b2 = self.engine.evaluate_voyage_plans(geared, 55000.0, cfg)

        ev1 = VesselEvaluation(vessel_class=gearless, is_eligible=True, port_compatibility=PortCompatibility(), best_voyage_plan=b1)
        ev2 = VesselEvaluation(vessel_class=geared, is_eligible=True, port_compatibility=PortCompatibility(), best_voyage_plan=b2)

        # When gearing provides no benefit (both have shore cranes, standard coal):
        ranked_normal = self.engine.rank_eligible_vessels([ev1, ev2], normal_port, normal_port, "Coal")
        # Gearing bonus should be 0.0, scores must be equal!
        self.assertEqual(ranked_normal[0].ranking_score, ranked_normal[1].ranking_score)

        # When destination is an anchorage or lacks shore cranes:
        anchorage_port = PortConstraint(
            port_id="ANCH",
            port_name="Offshore Anchorage",
            state="St",
            country="Country",
            port_type=PortType.ANCHORAGE_LIGHTERAGE,
            max_draft_m=15.0,
            allowed_cargo_types=["Coal"],
            has_shore_cranes=False,
        )
        ranked_anchorage = self.engine.rank_eligible_vessels([ev1, ev2], normal_port, anchorage_port, "Coal")
        # Geared vessel must receive the flexibility bonus and rank higher!
        self.assertGreater(ranked_anchorage[0].ranking_score, ranked_anchorage[1].ranking_score)
        self.assertEqual(ranked_anchorage[0].vessel_class.vessel_class, "IdenticalGeared")

    # ------------------------------------------------------------------------
    # 9. Explicit NO_FEASIBLE_VESSEL Test
    # ------------------------------------------------------------------------
    def test_explicit_no_feasible_vessel_status(self):
        """
        When all vessels violate constraints, engine must return NO_FEASIBLE_VESSEL
        and provide complete rejection reasons.
        """
        # Shallow restrictive port
        shallow_port = PortConstraint(
            port_id="VERY-SHALLOW",
            port_name="Ultra Shallow River Port",
            state="WB",
            country="India",
            port_type=PortType.BERTH,
            max_draft_m=8.0,  # All 4 bulk benchmark vessels have draft >= 10.538m
            max_loa_m=150.0,
            max_beam_m=25.0,
            allowed_cargo_types=["Coal"],
        )
        self.repo._register_port(shallow_port)

        res = self.engine.recommend(
            cargo_quantity_mt=50000.0,
            cargo_type="Coal",
            origin_port_input="Australia",
            dest_port_input="VERY-SHALLOW",
        )

        self.assertEqual(res.status, RecommendationStatus.NO_FEASIBLE_VESSEL)
        self.assertIsNone(res.recommended_vessel)
        self.assertIsNone(res.recommended_voyage_plan)
        self.assertIn("NO FEASIBLE VESSEL", res.recommendation_summary)

        # Every candidate vessel must be in rejection diagnostics
        self.assertEqual(len(res.rejection_diagnostics), 4)
        for v_name in ["Capesize", "Panamax", "Supramax", "Handysize"]:
            self.assertIn(v_name, res.rejection_diagnostics)


if __name__ == "__main__":
    unittest.main()
