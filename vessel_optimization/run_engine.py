"""
Vessel Type Optimization Engine - Benchmark Demonstrator
Runs and displays test scenarios highlighting key maritime optimization behaviors.
Member 3: Vessel Type Optimization (AI-Powered Bulk Cargo Chartering System)
"""

import sys
import os

# Add parent directory to Python path so module can be imported directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from vessel_optimization.engine import VesselOptimizationEngine
from vessel_optimization.models import OptimizationConfig, RecommendationStatus


def print_banner(title: str):
    print("\n" + "#" * 80)
    print(f"### {title.upper()}")
    print("#" * 80 + "\n")


def run_scenarios():
    engine = VesselOptimizationEngine()

    scenarios = [
        {
            "id": 1,
            "title": "Scenario 1: User Benchmark Example (100,000 MT Coal: Australia -> Paradip)",
            "cargo": 100000.0,
            "cargo_type": "Coal",
            "origin": "Australia",
            "dest": "Paradip",
            "config": OptimizationConfig(payload_factor=0.95, max_voyages=3),
            "description": (
                "Tests Paradip draft bottleneck (16.5m) rejecting Capesize (18.2m draft). "
                "Dynamically ranks eligible vessels (Supramax, Panamax, Handysize) with voyage splits and capacity utilization."
            )
        },
        {
            "id": 2,
            "title": "Scenario 2: Critical River Port Draft Bottleneck (75,000 MT Coal: Indonesia -> Haldia)",
            "cargo": 75000.0,
            "cargo_type": "Coal",
            "origin": "Indonesia",
            "dest": "Haldia",
            "config": OptimizationConfig(payload_factor=0.95, max_voyages=3),
            "description": (
                "Tests Haldia river port shallow draft constraint (12.2m). Capesize (18.2m), Panamax (14.43m), "
                "and Supramax (12.8m) are all physically disqualified. Only Handysize (10.54m draft) can berth."
            )
        },
        {
            "id": 3,
            "title": "Scenario 3: Gopalpur Intermediate Draft Screening (65,000 MT Iron Ore: Australia -> Gopalpur)",
            "cargo": 65000.0,
            "cargo_type": "Iron Ore",
            "origin": "Australia",
            "dest": "Gopalpur",
            "config": OptimizationConfig(payload_factor=0.95, max_voyages=3),
            "description": (
                "Tests Gopalpur max draft limit (14.2m). Capesize (18.2m) and Panamax (14.43m) fail draft screening, "
                "while Supramax (12.8m) and Handysize (10.54m) pass to dynamic voyage optimization."
            )
        },
        {
            "id": 4,
            "title": "Scenario 4: Single Voyage Parcel Fit (50,000 MT Limestone: South Africa -> Paradip)",
            "cargo": 50000.0,
            "cargo_type": "Limestone",
            "origin": "South Africa",
            "dest": "Paradip",
            "config": OptimizationConfig(payload_factor=0.95, max_voyages=3),
            "description": (
                "Tests anti-oversizing rule: Both Supramax (58k DWT) and Panamax (82k DWT) can complete the shipment "
                "in a single voyage. Engine prefers the appropriately sized Supramax with ~90% utilization over oversized Panamax (~64% util)."
            )
        },
        {
            "id": 5,
            "title": "Scenario 5: No Feasible Vessel Trigger (250,000 MT Bulk: Australia -> Haldia, max_voyages=3)",
            "cargo": 250000.0,
            "cargo_type": "Coal",
            "origin": "Australia",
            "dest": "Haldia",
            "config": OptimizationConfig(payload_factor=0.95, max_voyages=3),
            "description": (
                "Tests NO_FEASIBLE_VESSEL status: Larger vessels fail Haldia 12.2m draft, while Handysize cannot "
                "transport 250,000 MT within 3 voyages (would require 7 voyages). Engine returns status NO_FEASIBLE_VESSEL."
            )
        },
    ]

    for sc in scenarios:
        print_banner(f"{sc['title']}")
        print(f"Objective: {sc['description']}\n")
        res = engine.recommend(
            cargo_quantity_mt=sc["cargo"],
            cargo_type=sc["cargo_type"],
            origin_port_input=sc["origin"],
            dest_port_input=sc["dest"],
            config=sc["config"],
        )
        print(res.diagnostic_explanation)
        print("\nRESULT SUMMARY:")
        print(res.recommendation_summary)
        print("\n" + "=" * 80 + "\n")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] != "--all":
        from vessel_optimization.cli import run_cli
        sys.exit(run_cli())
    else:
        run_scenarios()
