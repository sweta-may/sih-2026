"""
Vessel Type Optimization Engine - Core Logic
Two-Stage Rule-Based & Optimization Engine for Dry Bulk Vessel Recommendation.
Member 3: Vessel Type Optimization (AI-Powered Bulk Cargo Chartering System)
"""

import math
from typing import Dict, List, Optional, Tuple

from vessel_optimization.models import (
    DimensionCheck,
    GoverningBottlenecks,
    OptimizationConfig,
    PortCompatibility,
    PortConstraint,
    PortType,
    RecommendationResult,
    RecommendationStatus,
    VesselClass,
    VesselEvaluation,
    VoyagePlan,
)
from vessel_optimization.data_loader import DataRepository


class VesselOptimizationEngine:
    """
    Core engine for vessel recommendation in dry bulk chartering.
    Implements strict two-stage evaluation:
      Stage 1: Physical & operational port constraint screening.
      Stage 2: Voyage splitting, capacity utilization, and anti-oversizing optimization.
    """

    def __init__(self, repository: Optional[DataRepository] = None):
        self.repo = repository or DataRepository()

    def resolve_port_bottlenecks(
        self, origin: PortConstraint, dest: PortConstraint
    ) -> GoverningBottlenecks:
        """
        Compare origin and destination ports to identify the governing restrictions
        and attribute the specific bottleneck port responsible for each dimension.
        """
        # Governing Draft
        if origin.max_draft_m is not None and dest.max_draft_m is not None:
            if origin.max_draft_m < dest.max_draft_m:
                gov_draft = origin.max_draft_m
                draft_port = origin.port_name
            elif dest.max_draft_m < origin.max_draft_m:
                gov_draft = dest.max_draft_m
                draft_port = dest.port_name
            else:
                gov_draft = origin.max_draft_m
                draft_port = f"{origin.port_name} & {dest.port_name} (Tied)"
        elif origin.max_draft_m is not None:
            gov_draft = origin.max_draft_m
            draft_port = origin.port_name
        elif dest.max_draft_m is not None:
            gov_draft = dest.max_draft_m
            draft_port = dest.port_name
        else:
            gov_draft = None
            draft_port = "None (Open / Unrestricted)"

        # Governing LOA
        if origin.max_loa_m is not None and dest.max_loa_m is not None:
            if origin.max_loa_m < dest.max_loa_m:
                gov_loa = origin.max_loa_m
                loa_port = origin.port_name
            elif dest.max_loa_m < origin.max_loa_m:
                gov_loa = dest.max_loa_m
                loa_port = dest.port_name
            else:
                gov_loa = origin.max_loa_m
                loa_port = f"{origin.port_name} & {dest.port_name} (Tied)"
        elif origin.max_loa_m is not None:
            gov_loa = origin.max_loa_m
            loa_port = origin.port_name
        elif dest.max_loa_m is not None:
            gov_loa = dest.max_loa_m
            loa_port = dest.port_name
        else:
            gov_loa = None
            loa_port = "None (Open / Unrestricted)"

        # Governing Beam
        if origin.max_beam_m is not None and dest.max_beam_m is not None:
            if origin.max_beam_m < dest.max_beam_m:
                gov_beam = origin.max_beam_m
                beam_port = origin.port_name
            elif dest.max_beam_m < origin.max_beam_m:
                gov_beam = dest.max_beam_m
                beam_port = dest.port_name
            else:
                gov_beam = origin.max_beam_m
                beam_port = f"{origin.port_name} & {dest.port_name} (Tied)"
        elif origin.max_beam_m is not None:
            gov_beam = origin.max_beam_m
            beam_port = origin.port_name
        elif dest.max_beam_m is not None:
            gov_beam = dest.max_beam_m
            beam_port = dest.port_name
        else:
            gov_beam = None
            beam_port = "None (Open / Unrestricted)"

        return GoverningBottlenecks(
            governing_draft_m=gov_draft,
            draft_bottleneck_port=draft_port,
            governing_loa_m=gov_loa,
            loa_bottleneck_port=loa_port,
            governing_beam_m=gov_beam,
            beam_bottleneck_port=beam_port,
        )

    def _check_port_dimensions(
        self, vessel: VesselClass, port: PortConstraint, role: str
    ) -> List[DimensionCheck]:
        """
        Evaluate vessel dimensions against a specific port.
        Boundary rule: vessel <= port is PASS. Equality passes.
        If port is ANCHORAGE_LIGHTERAGE, rigid quay LOA/beam restrictions do not apply.
        """
        checks = []

        # Draft check (applies to all ports including anchorages)
        if port.max_draft_m is not None:
            margin = port.max_draft_m - vessel.draft_m
            # Equality passes
            is_pass = vessel.draft_m <= port.max_draft_m
            note = f"Clearance: +{margin:.2f}m" if is_pass else f"Exceeded by {abs(margin):.2f}m"
            checks.append(
                DimensionCheck(
                    metric_name="Draft",
                    vessel_value=vessel.draft_m,
                    port_limit=port.max_draft_m,
                    bottleneck_port=f"{port.port_name} ({role})",
                    is_pass=is_pass,
                    margin_m=margin,
                    note=note,
                )
            )

        # LOA and Beam checks
        # If anchorage/lighterage, open-water mooring applies rather than berth constraints
        is_anchorage = port.port_type == PortType.ANCHORAGE_LIGHTERAGE

        if port.max_loa_m is not None and not is_anchorage:
            margin = port.max_loa_m - vessel.loa_m
            is_pass = vessel.loa_m <= port.max_loa_m
            note = f"Clearance: +{margin:.2f}m" if is_pass else f"Exceeded by {abs(margin):.2f}m"
            checks.append(
                DimensionCheck(
                    metric_name="LOA",
                    vessel_value=vessel.loa_m,
                    port_limit=port.max_loa_m,
                    bottleneck_port=f"{port.port_name} ({role})",
                    is_pass=is_pass,
                    margin_m=margin,
                    note=note,
                )
            )

        if port.max_beam_m is not None and not is_anchorage:
            margin = port.max_beam_m - vessel.beam_m
            is_pass = vessel.beam_m <= port.max_beam_m
            note = f"Clearance: +{margin:.2f}m" if is_pass else f"Exceeded by {abs(margin):.2f}m"
            checks.append(
                DimensionCheck(
                    metric_name="Beam",
                    vessel_value=vessel.beam_m,
                    port_limit=port.max_beam_m,
                    bottleneck_port=f"{port.port_name} ({role})",
                    is_pass=is_pass,
                    margin_m=margin,
                    note=note,
                )
            )

        return checks

    def check_vessel_compatibility(
        self,
        vessel: VesselClass,
        origin: PortConstraint,
        dest: PortConstraint,
        cargo_type: str,
    ) -> PortCompatibility:
        """
        Stage 1: Determine physical and operational compatibility for both ports.
        Returns PortCompatibility with exact pass/fail diagnostics.
        """
        compat = PortCompatibility()
        compat.origin_checks = self._check_port_dimensions(vessel, origin, "Origin")
        compat.dest_checks = self._check_port_dimensions(vessel, dest, "Destination")

        # Collect dimension failures
        for chk in compat.origin_checks:
            if not chk.is_pass:
                compat.rejection_reasons.append(
                    f"{vessel.vessel_class} {chk.metric_name} ({chk.vessel_value:.2f}m) exceeds "
                    f"Origin ({origin.port_name}) limit ({chk.port_limit:.2f}m) by {abs(chk.margin_m):.2f}m"
                )

        for chk in compat.dest_checks:
            if not chk.is_pass:
                compat.rejection_reasons.append(
                    f"{vessel.vessel_class} {chk.metric_name} ({chk.vessel_value:.2f}m) exceeds "
                    f"Destination ({dest.port_name}) limit ({chk.port_limit:.2f}m) by {abs(chk.margin_m):.2f}m"
                )

        # Cargo Handling Compatibility
        # Both ports must support the requested bulk cargo type
        norm_cargo = cargo_type.strip().lower()
        orig_allowed = [c.lower() for c in origin.allowed_cargo_types]
        dest_allowed = [c.lower() for c in dest.allowed_cargo_types]

        cargo_supported_orig = any(norm_cargo in c or c in norm_cargo for c in orig_allowed) if orig_allowed else True
        cargo_supported_dest = any(norm_cargo in c or c in norm_cargo for c in dest_allowed) if dest_allowed else True

        if not cargo_supported_orig:
            compat.cargo_handling_pass = False
            compat.rejection_reasons.append(
                f"Origin port '{origin.port_name}' does not support cargo type '{cargo_type}'."
            )
        if not cargo_supported_dest:
            compat.cargo_handling_pass = False
            compat.rejection_reasons.append(
                f"Destination port '{dest.port_name}' does not support cargo type '{cargo_type}'."
            )

        # Gear Requirement Check
        # If either port requires geared vessels and the candidate is gearless
        orig_requires_gear = origin.requires_geared_vessel or (not origin.has_shore_cranes and origin.port_type == PortType.BERTH)
        dest_requires_gear = dest.requires_geared_vessel or (not dest.has_shore_cranes and dest.port_type == PortType.BERTH)

        if (orig_requires_gear or dest_requires_gear) and not vessel.is_geared:
            compat.gear_requirement_pass = False
            port_name = origin.port_name if orig_requires_gear else dest.port_name
            compat.rejection_reasons.append(
                f"{vessel.vessel_class} is Gearless, but {port_name} lacks shore cranes and requires a geared vessel."
            )

        compat.is_compatible = len(compat.rejection_reasons) == 0
        return compat

    def evaluate_voyage_plans(
        self,
        vessel: VesselClass,
        cargo_quantity_mt: float,
        config: OptimizationConfig,
    ) -> Tuple[List[VoyagePlan], Optional[VoyagePlan]]:
        """
        Stage 2: For an eligible vessel, calculate voyage splitting options and capacity utilization.
        effective_payload = payload_factor * DWT (configurable approximation).
        """
        effective_payload = config.payload_factor * vessel.dwt_mt
        min_required_voyages = math.ceil(cargo_quantity_mt / effective_payload)

        plans: List[VoyagePlan] = []
        best_plan: Optional[VoyagePlan] = None

        # Evaluate voyage counts from min_required_voyages up to max_voyages
        # Note: if min_required_voyages > max_voyages, vessel cannot service the parcel under current threshold
        if min_required_voyages <= config.max_voyages:
            # We evaluate possible voyage counts
            for n in range(min_required_voyages, config.max_voyages + 1):
                cargo_per_voyage = cargo_quantity_mt / n
                total_capacity = n * effective_payload
                utilization = (cargo_quantity_mt / total_capacity) * 100.0
                deadfreight = total_capacity - cargo_quantity_mt

                plan = VoyagePlan(
                    num_voyages=n,
                    cargo_per_voyage_mt=cargo_per_voyage,
                    total_cargo_mt=cargo_quantity_mt,
                    effective_payload_per_voyage_mt=effective_payload,
                    total_capacity_mt=total_capacity,
                    capacity_utilization_pct=utilization,
                    deadfreight_mt=deadfreight,
                    is_within_max_voyages=True,
                    note=f"{n} voyage(s) @ {cargo_per_voyage:,.0f} MT/voyage ({utilization:.1f}% utilization)",
                )
                plans.append(plan)

            # In maritime chartering, the minimum required voyage count for a given vessel
            # minimizes turnaround days, canal/port dues, and total charter duration.
            best_plan = plans[0] if plans else None
        else:
            # Requires more voyages than max_voyages
            cargo_per_voyage = cargo_quantity_mt / min_required_voyages
            total_capacity = min_required_voyages * effective_payload
            utilization = (cargo_quantity_mt / total_capacity) * 100.0
            deadfreight = total_capacity - cargo_quantity_mt

            exceeded_plan = VoyagePlan(
                num_voyages=min_required_voyages,
                cargo_per_voyage_mt=cargo_per_voyage,
                total_cargo_mt=cargo_quantity_mt,
                effective_payload_per_voyage_mt=effective_payload,
                total_capacity_mt=total_capacity,
                capacity_utilization_pct=utilization,
                deadfreight_mt=deadfreight,
                is_within_max_voyages=False,
                note=f"Requires {min_required_voyages} voyages, exceeding max_voyages limit of {config.max_voyages}",
            )
            plans.append(exceeded_plan)
            best_plan = None

        return plans, best_plan

    def rank_eligible_vessels(
        self,
        evaluations: List[VesselEvaluation],
        origin: PortConstraint,
        dest: PortConstraint,
        cargo_type: str,
    ) -> List[VesselEvaluation]:
        """
        Multi-Factor Dynamic Ranking Logic:
          1. Physical and operational feasibility (already screened in Stage 1).
          2. Voyage count minimization: fewer voyages are preferred to avoid extra port calls and delays.
          3. Appropriate capacity utilization & Anti-Oversizing:
             - Avoid selecting an excessively large vessel when a smaller feasible vessel
               can transport the cargo with the SAME number of voyages.
             - Prefer higher capacity utilization (avoiding deadfreight).
          4. Secondary Context-Specific Flexibility:
             - If utilization and voyage counts are comparable, use geared capability as a tie-breaker
               ONLY when beneficial to port/cargo handling requirements (e.g. berth without shore cranes).
               A geared vessel is NOT automatically preferred over gearless if gearing provides no advantage.
        """
        feasible_evals = [e for e in evaluations if e.is_eligible and e.best_voyage_plan is not None]

        # Determine if geared capability provides an actual operational benefit
        # Benefit exists if:
        # - Port has limited shore crane facilities, OR
        # - Transshipment / anchorage operation, OR
        # - Minor bulk cargo often requiring grab discharge
        geared_is_beneficial = (
            not origin.has_shore_cranes
            or not dest.has_shore_cranes
            or origin.port_type == PortType.ANCHORAGE_LIGHTERAGE
            or dest.port_type == PortType.ANCHORAGE_LIGHTERAGE
            or cargo_type.lower() in ["fertilizer", "general bulk", "bauxite"]
        )

        for ev in feasible_evals:
            plan = ev.best_voyage_plan
            # Base score components:
            # - Voyages penalty: each extra voyage adds massive operational overhead (port turnaround, port dues)
            voyage_penalty = plan.num_voyages * 100.0

            # - Utilization reward: higher utilization is better (0 to 100)
            utilization_reward = plan.capacity_utilization_pct

            # - Anti-oversizing penalty: penalize oversized vessels when smaller vessel does same voyages
            # Ratio of DWT to cargo per voyage.
            # If DWT is 180k for a 40k cargo, ratio is 4.5 (heavily oversized).
            # If DWT is 58k for a 50k cargo, ratio is 1.16 (well matched).
            oversizing_ratio = ev.vessel_class.dwt_mt / plan.cargo_per_voyage_mt
            oversizing_penalty = max(0.0, oversizing_ratio - 1.2) * 20.0

            # - Contextual flexibility bonus
            flexibility_bonus = 5.0 if (ev.vessel_class.is_geared and geared_is_beneficial) else 0.0

            # Net suitability score (higher is better)
            # Ranking objective: Minimize voyages first, then maximize utilization, penalize oversizing
            score = (500.0 - voyage_penalty) + (utilization_reward * 0.8) - oversizing_penalty + flexibility_bonus
            ev.ranking_score = score

            ev.rank_rationale = (
                f"Voyages: {plan.num_voyages}, Utilization: {plan.capacity_utilization_pct:.1f}%, "
                f"Cargo/Voyage: {plan.cargo_per_voyage_mt:,.0f} MT, Deadfreight: {plan.deadfreight_mt:,.0f} MT "
                f"(Oversize Penalty: {oversizing_penalty:.1f}, Flexibility Bonus: +{flexibility_bonus:.1f})"
            )

        # Sort descending by score
        feasible_evals.sort(key=lambda x: x.ranking_score, reverse=True)
        return feasible_evals

    def recommend(
        self,
        cargo_quantity_mt: float,
        cargo_type: str,
        origin_port_input: str,
        dest_port_input: str,
        allowed_vessel_classes: Optional[List[str]] = None,
        config: Optional[OptimizationConfig] = None,
    ) -> RecommendationResult:
        """
        Master recommendation entry point.
        Executes two-stage evaluation pipeline and generates comprehensive diagnostic output.
        """
        cfg = config or OptimizationConfig()

        # 1. Resolve Ports
        origin_port = self.repo.get_port(origin_port_input)
        dest_port = self.repo.get_port(dest_port_input)

        if not origin_port:
            raise ValueError(f"Origin port '{origin_port_input}' not found in port database.")
        if not dest_port:
            raise ValueError(f"Destination port '{dest_port_input}' not found in port database.")

        # 2. Identify Governing Bottlenecks
        bottlenecks = self.resolve_port_bottlenecks(origin_port, dest_port)

        # 3. Select Candidate Vessel Classes
        all_vessels = self.repo.get_all_vessels()
        if allowed_vessel_classes:
            allowed_set = {v.strip().lower() for v in allowed_vessel_classes}
            candidates = [v for v in all_vessels if v.vessel_class.lower() in allowed_set]
        else:
            candidates = all_vessels

        # 4. Stage 1: Port Compatibility Screening
        evaluations_dict: Dict[str, VesselEvaluation] = {}
        eligible_evaluations: List[VesselEvaluation] = []
        rejection_diagnostics: Dict[str, List[str]] = {}

        for v in candidates:
            compat = self.check_vessel_compatibility(v, origin_port, dest_port, cargo_type)
            ev = VesselEvaluation(
                vessel_class=v,
                is_eligible=compat.is_compatible,
                port_compatibility=compat,
                rejection_reasons=list(compat.rejection_reasons),
            )
            evaluations_dict[v.vessel_class] = ev

            if compat.is_compatible:
                eligible_evaluations.append(ev)
            else:
                rejection_diagnostics[v.vessel_class] = list(compat.rejection_reasons)

        # 5. Check if Any Vessel Passed Stage 1
        if not eligible_evaluations:
            # Status: NO_FEASIBLE_VESSEL
            summary = (
                f"NO FEASIBLE VESSEL: All candidate vessel classes violate physical or operational constraints "
                f"between {origin_port.port_name} and {dest_port.port_name}."
            )
            diag_lines = [
                f"Cargo: {cargo_quantity_mt:,.0f} MT ({cargo_type})",
                f"Route: {origin_port.port_name} ({origin_port.country}) -> {dest_port.port_name} ({dest_port.country})",
                f"Governing Draft: {bottlenecks.governing_draft_m}m [Bottleneck: {bottlenecks.draft_bottleneck_port}]",
                f"Governing LOA: {bottlenecks.governing_loa_m}m [Bottleneck: {bottlenecks.loa_bottleneck_port}]",
                f"Governing Beam: {bottlenecks.governing_beam_m}m [Bottleneck: {bottlenecks.beam_bottleneck_port}]",
                "",
                "Rejection Diagnostics:",
            ]
            for v_name, reasons in rejection_diagnostics.items():
                diag_lines.append(f"  • {v_name}:")
                for r in reasons:
                    diag_lines.append(f"      - {r}")

            return RecommendationResult(
                status=RecommendationStatus.NO_FEASIBLE_VESSEL,
                cargo_quantity_mt=cargo_quantity_mt,
                cargo_type=cargo_type,
                origin_port=origin_port,
                dest_port=dest_port,
                governing_bottlenecks=bottlenecks,
                config=cfg,
                recommended_vessel=None,
                recommended_voyage_plan=None,
                candidate_evaluations=evaluations_dict,
                rejection_diagnostics=rejection_diagnostics,
                recommendation_summary=summary,
                diagnostic_explanation="\n".join(diag_lines),
            )

        # 6. Stage 2: Voyage Splitting & Optimization for Eligible Vessels
        feasible_with_voyages: List[VesselEvaluation] = []
        for ev in eligible_evaluations:
            plans, best_plan = self.evaluate_voyage_plans(ev.vessel_class, cargo_quantity_mt, cfg)
            ev.voyage_plans = plans
            ev.best_voyage_plan = best_plan

            if best_plan is None:
                # Exceeded max voyages
                ev.is_eligible = False
                reason = (
                    f"Requires more voyages than allowable limit ({cfg.max_voyages}) "
                    f"due to vessel DWT ({ev.vessel_class.dwt_mt:,.0f} MT)."
                )
                ev.rejection_reasons.append(reason)
                rejection_diagnostics[ev.vessel_class.vessel_class] = [reason]
            else:
                feasible_with_voyages.append(ev)

        # If all eligible vessels exceeded max voyages
        if not feasible_with_voyages:
            summary = (
                f"NO FEASIBLE VESSEL: Physically eligible vessels cannot carry {cargo_quantity_mt:,.0f} MT "
                f"within the maximum allowed voyage limit of {cfg.max_voyages}."
            )
            diag_lines = [
                f"Cargo: {cargo_quantity_mt:,.0f} MT ({cargo_type})",
                f"Route: {origin_port.port_name} -> {dest_port.port_name}",
                f"Max Allowed Voyages: {cfg.max_voyages}",
                "",
                "Rejection Diagnostics:",
            ]
            for v_name, reasons in rejection_diagnostics.items():
                diag_lines.append(f"  • {v_name}:")
                for r in reasons:
                    diag_lines.append(f"      - {r}")

            return RecommendationResult(
                status=RecommendationStatus.NO_FEASIBLE_VESSEL,
                cargo_quantity_mt=cargo_quantity_mt,
                cargo_type=cargo_type,
                origin_port=origin_port,
                dest_port=dest_port,
                governing_bottlenecks=bottlenecks,
                config=cfg,
                recommended_vessel=None,
                recommended_voyage_plan=None,
                candidate_evaluations=evaluations_dict,
                rejection_diagnostics=rejection_diagnostics,
                recommendation_summary=summary,
                diagnostic_explanation="\n".join(diag_lines),
            )

        # 7. Rank Eligible Vessels
        ranked_evals = self.rank_eligible_vessels(feasible_with_voyages, origin_port, dest_port, cargo_type)
        winner_eval = ranked_evals[0]
        recommended_vessel = winner_eval.vessel_class
        recommended_plan = winner_eval.best_voyage_plan

        # 8. Build Comprehensive Diagnostic Explanation
        summary = (
            f"RECOMMENDED: {recommended_vessel.vessel_class} ({recommended_plan.num_voyages} voyage"
            f"{'s' if recommended_plan.num_voyages > 1 else ''} of {recommended_plan.cargo_per_voyage_mt:,.0f} MT, "
            f"{recommended_plan.capacity_utilization_pct:.1f}% capacity utilization)"
        )

        diag_lines = [
            "=" * 70,
            "🚢 SMARTFREIGHT AI - BULK VESSEL RECOMMENDATION REPORT",
            "=" * 70,
            f"Cargo Quantity     : {cargo_quantity_mt:,.0f} MT",
            f"Commodity Type     : {cargo_type}",
            f"Origin Port (Load) : {origin_port.port_name} ({origin_port.country}) [{origin_port.port_type.value}]",
            f"Destination (Disch): {dest_port.port_name} ({dest_port.country}) [{dest_port.port_type.value}]",
            f"Config Settings    : Payload Factor = {cfg.payload_factor:.2f} (approx), Max Voyages = {cfg.max_voyages}",
            "-" * 70,
            "GOVERNING PORT BOTTLENECKS:",
            f"  • Draft : {bottlenecks.governing_draft_m} m -> Bottleneck Port: {bottlenecks.draft_bottleneck_port}",
            f"  • LOA   : {bottlenecks.governing_loa_m} m -> Bottleneck Port: {bottlenecks.loa_bottleneck_port}",
            f"  • Beam  : {bottlenecks.governing_beam_m} m -> Bottleneck Port: {bottlenecks.beam_bottleneck_port}",
            "-" * 70,
            "STAGE 1: PHYSICAL & OPERATIONAL SCREENING RESULTS:",
        ]

        for v in candidates:
            ev = evaluations_dict[v.vessel_class]
            status_tag = "[ELIGIBLE]" if ev.is_eligible else "[REJECTED]"
            diag_lines.append(f"  • {v.vessel_class:<10} ({v.dwt_mt:,.0f} DWT, Draft {v.draft_m}m, LOA {v.loa_m}m): {status_tag}")
            if not ev.is_eligible:
                for reason in ev.rejection_reasons:
                    diag_lines.append(f"      ↳ Reason: {reason}")

        diag_lines.extend([
            "-" * 70,
            "STAGE 2: FEASIBLE VOYAGE PLANNING & DYNAMIC RANKING:",
        ])

        for rank_idx, ev in enumerate(ranked_evals, 1):
            p = ev.best_voyage_plan
            is_winner = "★★★ WINNER ★★★" if rank_idx == 1 else f"Rank #{rank_idx}"
            diag_lines.append(
                f"  {is_winner:<16}: {ev.vessel_class.vessel_class} "
                f"-> {p.num_voyages} voyage(s) @ {p.cargo_per_voyage_mt:,.0f} MT | "
                f"Util: {p.capacity_utilization_pct:.1f}% | Deadfreight: {p.deadfreight_mt:,.0f} MT | "
                f"Score: {ev.ranking_score:.1f}"
            )

        diag_lines.extend([
            "-" * 70,
            "EXECUTIVE RATIONALE FOR SELECTION:",
            f"  1. Port Feasibility: {recommended_vessel.vessel_class} fully satisfies the governing restrictions "
            f"     (Draft {recommended_vessel.draft_m}m <= {bottlenecks.governing_draft_m}m governed by {bottlenecks.draft_bottleneck_port}).",
            f"  2. Voyage Planning: Cargo of {cargo_quantity_mt:,.0f} MT is split into {recommended_plan.num_voyages} voyage(s) "
            f"     at {recommended_plan.cargo_per_voyage_mt:,.0f} MT per voyage.",
            f"  3. Capacity Match: Delivers {recommended_plan.capacity_utilization_pct:.1f}% capacity utilization with minimal deadfreight.",
        ])

        if len(ranked_evals) > 1:
            runner_up = ranked_evals[1]
            diag_lines.append(
                f"  4. Competitive Comparison: Outperformed {runner_up.vessel_class.vessel_class} "
                f"(Rank #2: {runner_up.best_voyage_plan.num_voyages} voyages, {runner_up.best_voyage_plan.capacity_utilization_pct:.1f}% util) "
                f"by avoiding excessive vessel oversizing and optimizing hold utilization."
            )

        if rejection_diagnostics:
            diag_lines.append("  5. Ineligible Classes: Disqualified due to hard physical bottlenecks: " +
                              ", ".join([f"{k} ({len(v)} violation{'s' if len(v)>1 else ''})" for k, v in rejection_diagnostics.items() if k in [c.vessel_class for c in candidates if not evaluations_dict[c.vessel_class].is_eligible]]))

        diag_lines.append("=" * 70)

        return RecommendationResult(
            status=RecommendationStatus.FEASIBLE_RECOMMENDATION,
            cargo_quantity_mt=cargo_quantity_mt,
            cargo_type=cargo_type,
            origin_port=origin_port,
            dest_port=dest_port,
            governing_bottlenecks=bottlenecks,
            config=cfg,
            recommended_vessel=recommended_vessel,
            recommended_voyage_plan=recommended_plan,
            candidate_evaluations=evaluations_dict,
            rejection_diagnostics=rejection_diagnostics,
            recommendation_summary=summary,
            diagnostic_explanation="\n".join(diag_lines),
        )
