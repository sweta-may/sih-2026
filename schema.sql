CREATE TABLE freight_data (
 index_code TEXT, vessel_class TEXT, route_code TEXT, unit TEXT,
 route_description TEXT, source TEXT, data_status TEXT
);

CREATE TABLE vessel_data (
 vessel_id TEXT PRIMARY KEY, vessel_class TEXT, dwt_mt REAL, loa_m REAL,
 beam_m REAL, draft_m REAL, reference_note TEXT, source TEXT
);

CREATE TABLE port_data (
 port_id TEXT PRIMARY KEY, port_name TEXT, state TEXT, country TEXT,
 port_type TEXT, max_draft_m REAL, max_loa_m REAL, max_beam_m REAL,
 cargo_capacity_mmtpa REAL, constraint_note TEXT, source TEXT
);

CREATE TABLE port_calls (
 port_call_id TEXT PRIMARY KEY, imo INTEGER, mmsi INTEGER, locode TEXT,
 port_id TEXT, event TEXT, timestamp_utc TEXT, arrival_lat REAL,
 arrival_lon REAL, departure_lat REAL, departure_lon REAL,
 last_port TEXT, last_port_departure_utc TEXT, source TEXT, quality_flag TEXT
);

CREATE TABLE congestion_data (
 port_id TEXT, period_start TEXT, period_end TEXT, vessel_class TEXT,
 cargo_segment TEXT, waiting_hours REAL, berth_time_hours REAL,
 total_port_time_hours REAL, ships_observed INTEGER,
 berth_occupancy_pct REAL, source TEXT, quality_flag TEXT
);

CREATE TABLE commodity_data (
 month TEXT, trade_type TEXT, state_name TEXT, state_code TEXT, port TEXT,
 country TEXT, hs2_code TEXT, commodity TEXT, units TEXT, quantity REAL,
 dollars_value REAL, inr_value REAL, source TEXT, quality_flag TEXT
);
