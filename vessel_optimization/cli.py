"""
Vessel Type Optimization Engine - CLI Interface
Command-line runner and demo interface for vessel recommendation.
Member 3: Vessel Type Optimization (AI-Powered Bulk Cargo Chartering System)
"""

import argparse
import json
import sys
from typing import Optional

from vessel_optimization.engine import VesselOptimizationEngine
from vessel_optimization.models import OptimizationConfig, RecommendationStatus


def parse_arguments(args=None):
    parser = argparse.ArgumentParser(
        description="SmartFreight AI - Bulk Vessel Type Optimization Engine (Member 3: Phavithra)",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "--cargo",
        "-c",
        type=float,
        default=100000.0,
        help="Cargo shipment quantity in metric tonnes (MT). Default: 100,000 MT",
    )
    parser.add_argument(
        "--cargo-type",
        "-t",
        type=str,
        default="Coal",
        help="Commodity type (e.g., Coal, Iron Ore, Limestone, Bauxite). Default: Coal",
    )
    parser.add_argument(
        "--origin",
        "-o",
        type=str,
        default="Australia",
        help="Origin / load port or country (e.g., Australia, Newcastle, South Africa, Indonesia). Default: Australia",
    )
    parser.add_argument(
        "--dest",
        "-d",
        type=str,
        default="Paradip",
        help="Destination / discharge port (e.g., Paradip, Haldia, Visakhapatnam, Gangavaram, Gopalpur, Dhamra). Default: Paradip",
    )
    parser.add_argument(
        "--payload-factor",
        "-p",
        type=float,
        default=0.95,
        help="Configurable approximation payload factor (effective_payload = factor * DWT). Default: 0.95",
    )
    parser.add_argument(
        "--max-voyages",
        "-m",
        type=int,
        default=3,
        help="Maximum allowed voyages to split the cargo parcel. Default: 3",
    )
    parser.add_argument(
        "--vessels",
        "-v",
        nargs="+",
        default=None,
        help="Candidate vessel classes to evaluate (e.g., Handysize Supramax Panamax Capesize). Default: All",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output result in pure JSON format for programmatic integration.",
    )
    return parser.parse_args(args)


def run_cli(args=None):
    parsed = parse_arguments(args)

    config = OptimizationConfig(
        payload_factor=parsed.payload_factor,
        max_voyages=parsed.max_voyages,
    )

    engine = VesselOptimizationEngine()

    try:
        result = engine.recommend(
            cargo_quantity_mt=parsed.cargo,
            cargo_type=parsed.cargo_type,
            origin_port_input=parsed.origin,
            dest_port_input=parsed.dest,
            allowed_vessel_classes=parsed.vessels,
            config=config,
        )

        if parsed.json:
            print(json.dumps(result.to_dict(), indent=2))
        else:
            print(result.diagnostic_explanation)
            print("\nSUMMARY:")
            print(result.recommendation_summary)

        return 0 if result.status == RecommendationStatus.FEASIBLE_RECOMMENDATION else 1

    except Exception as e:
        print(f"Error executing recommendation engine: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(run_cli())
