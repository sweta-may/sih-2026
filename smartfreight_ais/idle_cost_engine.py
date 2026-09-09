VESSEL_DEMURRAGE_RATES_PD = {
    "Capesize": 28000.0,
    "Panamax": 18500.0,
    "Supramax": 15000.0,
    "Handysize": 12000.0,
}

def calculate_idle_cost(waiting_time_hours: float, vessel_class: str,
                        custom_demurrage_rate_pd: float = None) -> dict:
    """
    Calculates estimated idle demurrage cost and anchorage bunker consumption cost.
    """
    rate_pd = custom_demurrage_rate_pd or VESSEL_DEMURRAGE_RATES_PD.get(vessel_class, 16000.0)
    waiting_days = waiting_time_hours / 24.0

    idle_cost_usd = round(waiting_days * rate_pd, 2)

    # Anchorage bunker consumption (~2.5 MT/day @ $600/MT)
    bunker_idle_cost_usd = round(waiting_days * 2.5 * 600.0, 2)
    total_idle_impact_usd = round(idle_cost_usd + bunker_idle_cost_usd, 2)

    return {
        "waiting_time_hours": round(waiting_time_hours, 2),
        "waiting_time_days": round(waiting_days, 2),
        "vessel_class": vessel_class,
        "demurrage_rate_usd_per_day": rate_pd,
        "estimated_idle_cost_usd": idle_cost_usd,
        "bunker_idle_cost_usd": bunker_idle_cost_usd,
        "total_idle_impact_usd": total_idle_impact_usd
    }
