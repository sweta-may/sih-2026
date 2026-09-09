"""
Vessel Type Optimization Engine - Data Loader & Repository
Loads and normalizes vessel specifications and port constraints.
Member 3: Vessel Type Optimization (AI-Powered Bulk Cargo Chartering System)
"""

import csv
import os
from typing import Dict, List, Optional
from vessel_optimization.models import VesselClass, PortConstraint, PortType

# Default path to the SmartFreight data layer. The collaborative repository
# keeps the data layer in a nested directory, while the standalone package
# keeps it at the repository root.
_REPOSITORY_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_NESTED_DATA_DIR = os.path.join(_REPOSITORY_ROOT, "SmartFreight_POPULATED_Data_Layer")
DEFAULT_DATA_DIR = (
    _NESTED_DATA_DIR
    if os.path.exists(os.path.join(_NESTED_DATA_DIR, "port_data.csv"))
    else _REPOSITORY_ROOT
)


# Built-in fallback vessels (matches Baltic benchmark specs in vessel_data.csv)
FALLBACK_VESSELS = [
    VesselClass(
        vessel_id="BALTIC-CAPESIZE",
        vessel_class="Capesize",
        dwt_mt=180000.0,
        loa_m=290.0,
        beam_m=45.0,
        draft_m=18.2,
        is_geared=False,
        cranes_info="Gearless (requires shore-based ship loader/unloader gantries)",
        reference_note="Baltic benchmark Capesize (180,000 DWT standard)",
        source="Baltic Exchange",
        data_status="REFERENCE_ACTUAL"
    ),
    VesselClass(
        vessel_id="BALTIC-PANAMAX",
        vessel_class="Panamax",
        dwt_mt=82500.0,
        loa_m=229.0,
        beam_m=32.25,
        draft_m=14.43,
        is_geared=False,
        cranes_info="Gearless (requires shore-based cranes or conveyors)",
        reference_note="Baltic benchmark Kamsarmax/Panamax (82,500 DWT standard)",
        source="Baltic Exchange",
        data_status="REFERENCE_ACTUAL"
    ),
    VesselClass(
        vessel_id="BALTIC-SUPRAMAX",
        vessel_class="Supramax",
        dwt_mt=58328.0,
        loa_m=189.99,
        beam_m=32.26,
        draft_m=12.8,
        is_geared=True,
        cranes_info="Geared: 4 x 30 MT deck cranes with grabs",
        reference_note="Baltic benchmark Supramax (58,328 DWT standard workhorse)",
        source="Baltic Exchange",
        data_status="REFERENCE_ACTUAL"
    ),
    VesselClass(
        vessel_id="BALTIC-HANDYSIZE",
        vessel_class="Handysize",
        dwt_mt=38200.0,
        loa_m=180.0,
        beam_m=29.8,
        draft_m=10.538,
        is_geared=True,
        cranes_info="Geared: 4 x 30 MT deck cranes with grabs",
        reference_note="Baltic benchmark Handysize (38,200 DWT standard)",
        source="Baltic Exchange",
        data_status="REFERENCE_ACTUAL"
    ),
]

# Pragmatic international bulk export origins frequently shipping to East Coast India
INTERNATIONAL_ORIGIN_PORTS = [
    PortConstraint(
        port_id="AU-BENCHMARK",
        port_name="Australia (Bulk Terminal Benchmark)",
        state="Queensland / NSW",
        country="Australia",
        port_type=PortType.BERTH,
        max_draft_m=19.5,
        max_loa_m=350.0,
        max_beam_m=55.0,
        allowed_cargo_types=["Coal", "Iron Ore", "Bauxite", "General Bulk"],
        requires_geared_vessel=False,
        has_shore_cranes=True,
        constraint_note="Benchmark coal terminal (e.g. Hay Point / Dalrymple Bay / Newcastle). Accommodates fully laden Capesize.",
        source="Australian Bulk Terminals Reference",
        data_status="REFERENCE_ACTUAL"
    ),
    PortConstraint(
        port_id="AUHPT",
        port_name="Hay Point / DBCT",
        state="Queensland",
        country="Australia",
        port_type=PortType.BERTH,
        max_draft_m=19.5,
        max_loa_m=350.0,
        max_beam_m=55.0,
        allowed_cargo_types=["Coal"],
        requires_geared_vessel=False,
        has_shore_cranes=True,
        constraint_note="Major coal terminal; accommodates Capesize.",
        source="DBCT Terminal Information",
        data_status="REFERENCE_ACTUAL"
    ),
    PortConstraint(
        port_id="AUNCW",
        port_name="Newcastle",
        state="New South Wales",
        country="Australia",
        port_type=PortType.BERTH,
        max_draft_m=15.2,
        max_loa_m=300.0,
        max_beam_m=50.0,
        allowed_cargo_types=["Coal"],
        requires_geared_vessel=False,
        has_shore_cranes=True,
        constraint_note="World largest coal export port; channel max draft 15.2m restricts fully laden Capesize without tide/partial.",
        source="Port of Newcastle handbook",
        data_status="REFERENCE_ACTUAL"
    ),
    PortConstraint(
        port_id="AUGLD",
        port_name="Gladstone",
        state="Queensland",
        country="Australia",
        port_type=PortType.BERTH,
        max_draft_m=17.5,
        max_loa_m=315.0,
        max_beam_m=50.0,
        allowed_cargo_types=["Coal", "Bauxite"],
        requires_geared_vessel=False,
        has_shore_cranes=True,
        constraint_note="RGT / Barney Point bulk terminals.",
        source="Gladstone Ports Corp",
        data_status="REFERENCE_ACTUAL"
    ),
    PortConstraint(
        port_id="ZA-BENCHMARK",
        port_name="South Africa (Richards Bay Benchmark)",
        state="KwaZulu-Natal",
        country="South Africa",
        port_type=PortType.BERTH,
        max_draft_m=17.5,
        max_loa_m=314.0,
        max_beam_m=47.25,
        allowed_cargo_types=["Coal", "Iron Ore", "General Bulk"],
        requires_geared_vessel=False,
        has_shore_cranes=True,
        constraint_note="RBCT benchmark bulk terminal. Handles Capesize and Panamax.",
        source="Transnet National Ports Authority",
        data_status="REFERENCE_ACTUAL"
    ),
    PortConstraint(
        port_id="ZARCB",
        port_name="Richards Bay",
        state="KwaZulu-Natal",
        country="South Africa",
        port_type=PortType.BERTH,
        max_draft_m=17.5,
        max_loa_m=314.0,
        max_beam_m=47.25,
        allowed_cargo_types=["Coal", "Iron Ore", "General Bulk"],
        requires_geared_vessel=False,
        has_shore_cranes=True,
        constraint_note="RBCT terminal limits.",
        source="Transnet National Ports Authority",
        data_status="REFERENCE_ACTUAL"
    ),
    PortConstraint(
        port_id="ID-BENCHMARK",
        port_name="Indonesia (Bulk Coal Benchmark)",
        state="Kalimantan",
        country="Indonesia",
        port_type=PortType.BERTH,
        max_draft_m=15.0,
        max_loa_m=250.0,
        max_beam_m=38.0,
        allowed_cargo_types=["Coal", "Bauxite", "General Bulk"],
        requires_geared_vessel=False,
        has_shore_cranes=True,
        constraint_note="Benchmark Indonesian coal export loading (e.g. Taboneo / Tanjung Bara).",
        source="Indonesian Directorate of Sea Transportation",
        data_status="REFERENCE_ACTUAL"
    ),
    PortConstraint(
        port_id="IDTAB",
        port_name="Taboneo",
        state="South Kalimantan",
        country="Indonesia",
        port_type=PortType.ANCHORAGE_LIGHTERAGE,
        max_draft_m=15.5,
        max_loa_m=280.0,
        max_beam_m=45.0,
        allowed_cargo_types=["Coal"],
        requires_geared_vessel=False,
        has_shore_cranes=False,
        constraint_note="Anchorage / floating crane transfer point. Supramax/Panamax dominant.",
        source="Indonesian Port Guidelines",
        data_status="REFERENCE_ACTUAL"
    ),
    PortConstraint(
        port_id="IDTJB",
        port_name="Tanjung Bara",
        state="East Kalimantan",
        country="Indonesia",
        port_type=PortType.BERTH,
        max_draft_m=17.5,
        max_loa_m=310.0,
        max_beam_m=50.0,
        allowed_cargo_types=["Coal"],
        requires_geared_vessel=False,
        has_shore_cranes=True,
        constraint_note="Deepwater coal terminal operated by KPC.",
        source="KPC Terminal Information",
        data_status="REFERENCE_ACTUAL"
    ),
]


class DataRepository:
    """Loads and caches vessel and port data for the optimization engine."""

    def __init__(self, data_dir: Optional[str] = None):
        self.data_dir = data_dir or DEFAULT_DATA_DIR
        self.vessels: Dict[str, VesselClass] = {}
        self.ports: Dict[str, PortConstraint] = {}
        self._load_vessels()
        self._load_ports()

    def _load_vessels(self) -> None:
        """Load vessel classes from vessel_data.csv, falling back to benchmarks."""
        vessel_csv = os.path.join(self.data_dir, "vessel_data.csv")
        loaded = False
        if os.path.exists(vessel_csv):
            try:
                with open(vessel_csv, mode="r", encoding="utf-8-sig") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        v_class = row.get("vessel_class", "").strip()
                        if not v_class:
                            continue
                        dwt = float(row.get("dwt_mt", 0))
                        loa = float(row.get("loa_m", 0))
                        beam = float(row.get("beam_m", 0))
                        draft = float(row.get("draft_m", 0))
                        v_id = row.get("vessel_id", f"BALTIC-{v_class.upper()}")
                        note = row.get("reference_note", "")

                        # Determine geared capability based on bulk carrier industry standard
                        # Handysize & Supramax are almost universally geared; Panamax & Capesize gearless
                        is_geared = v_class.lower() in ["handysize", "supramax", "ultramax", "handymax"]
                        cranes = "4 x 30 MT deck cranes with grabs" if is_geared else "Gearless"

                        vessel = VesselClass(
                            vessel_id=v_id,
                            vessel_class=v_class,
                            dwt_mt=dwt,
                            loa_m=loa,
                            beam_m=beam,
                            draft_m=draft,
                            is_geared=is_geared,
                            cranes_info=cranes,
                            reference_note=note,
                            source=row.get("source", "Baltic Exchange"),
                            data_status=row.get("data_status", "REFERENCE_ACTUAL")
                        )
                        self.vessels[v_class.lower()] = vessel
                loaded = len(self.vessels) > 0
            except Exception as e:
                print(f"Warning: Failed reading vessel_data.csv: {e}. Using fallback vessels.")

        if not loaded:
            for v in FALLBACK_VESSELS:
                self.vessels[v.vessel_class.lower()] = v

    def _load_ports(self) -> None:
        """Load East Coast Indian ports from port_data.csv and merge international benchmarks."""
        port_csv = os.path.join(self.data_dir, "port_data.csv")
        if os.path.exists(port_csv):
            try:
                with open(port_csv, mode="r", encoding="utf-8-sig") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        p_id = row.get("port_id", "").strip()
                        name = row.get("port_name", "").strip()
                        if not p_id and not name:
                            continue

                        raw_port_type = row.get("port_type", "").strip()
                        # Handle Sagar-Sandheads as ANCHORAGE_LIGHTERAGE
                        if "anchorage" in raw_port_type.lower() or "sagar" in name.lower():
                            p_type = PortType.ANCHORAGE_LIGHTERAGE
                        else:
                            p_type = PortType.BERTH

                        draft = float(row["max_draft_m"]) if row.get("max_draft_m") else None
                        loa = float(row["max_loa_m"]) if row.get("max_loa_m") else None
                        beam = float(row["max_beam_m"]) if row.get("max_beam_m") else None
                        cap = float(row["cargo_capacity_mmtpa"]) if row.get("cargo_capacity_mmtpa") else None

                        port = PortConstraint(
                            port_id=p_id,
                            port_name=name,
                            state=row.get("state", ""),
                            country=row.get("country", "India"),
                            port_type=p_type,
                            max_draft_m=draft,
                            max_loa_m=loa,
                            max_beam_m=beam,
                            cargo_capacity_mmtpa=cap,
                            constraint_note=row.get("constraint_note", ""),
                            source=row.get("source", ""),
                            data_status=row.get("data_status", "REFERENCE_ACTUAL")
                        )
                        self._register_port(port)
            except Exception as e:
                print(f"Warning: Failed reading port_data.csv: {e}.")

        # Register international origin ports
        for p in INTERNATIONAL_ORIGIN_PORTS:
            self._register_port(p)

    def _register_port(self, port: PortConstraint) -> None:
        """Store port under normalized lookup keys (ID, name, country)."""
        self.ports[port.port_id.lower()] = port
        self.ports[port.port_name.lower()] = port

    def get_vessel(self, name: str) -> Optional[VesselClass]:
        """Lookup vessel by class name (e.g. 'Panamax', 'supramax')."""
        return self.vessels.get(name.strip().lower())

    def get_all_vessels(self) -> List[VesselClass]:
        """Return list of standard candidate vessel classes."""
        order = ["handysize", "supramax", "panamax", "capesize"]
        result = []
        for key in order:
            if key in self.vessels:
                result.append(self.vessels[key])
        for key, v in self.vessels.items():
            if key not in order and v not in result:
                result.append(v)
        return result

    def get_port(self, query: str) -> Optional[PortConstraint]:
        """
        Fuzzy / alias port lookup.
        Supports Port ID (e.g. 'INPRD'), Port Name (e.g. 'Paradip'),
        and Country / Region (e.g. 'Australia', 'South Africa', 'Indonesia').
        """
        q = query.strip().lower()
        if q in self.ports:
            return self.ports[q]

        # Alias mappings
        aliases = {
            "australia": "AU-BENCHMARK",
            "aus": "AU-BENCHMARK",
            "dbct": "AUHPT",
            "hay point": "AUHPT",
            "haypoint": "AUHPT",
            "newcastle": "AUNCW",
            "gladstone": "AUGLD",
            "south africa": "ZA-BENCHMARK",
            "sa": "ZA-BENCHMARK",
            "richards bay": "ZARCB",
            "indonesia": "ID-BENCHMARK",
            "indo": "ID-BENCHMARK",
            "taboneo": "IDTAB",
            "tanjung bara": "IDTJB",
            "paradip": "INPRD",
            "visakhapatnam": "INVTZ",
            "vizag": "INVTZ",
            "gangavaram": "INGGV",
            "gopalpur": "INGPR",
            "dhamra": "INDHM",
            "haldia": "INHAL",
            "sagar": "INSAG",
            "sagar-sandheads": "INSAG",
            "sandheads": "INSAG",
        }

        alias_target = aliases.get(q)
        if alias_target and alias_target.lower() in self.ports:
            return self.ports[alias_target.lower()]

        # Substring search in name or country
        for key, port in self.ports.items():
            if q in port.port_name.lower() or q in port.country.lower() or q in port.port_id.lower():
                return port

        return None
