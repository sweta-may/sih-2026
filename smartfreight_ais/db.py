from pathlib import Path

_current = Path(__file__).resolve().parent
_candidates = [
    _current.parent / "SmartFreight_POPULATED_Data_Layer",
    _current.parent.parent / "SmartFreight_POPULATED_Data_Layer",
    Path(r"c:\Users\ADL\Desktop\sih\SmartFreight_POPULATED_Data_Layer"),
]
DATA_DIR = str(next((p for p in _candidates if p.exists()), _candidates[0]))
DB_PATH = os.path.join(DATA_DIR, "smartfreight_populated.db")

def get_connection():
    if os.path.exists(DB_PATH):
        return sqlite3.connect(DB_PATH)
    return None

def load_ports():
    conn = get_connection()
    if conn:
        try:
            df = pd.read_sql("SELECT * FROM port_data", conn)
            conn.close()
            return df
        except Exception:
            pass
    csv_p = os.path.join(DATA_DIR, "port_data.csv")
    if os.path.exists(csv_p):
        return pd.read_csv(csv_p)
    return pd.DataFrame()

def load_vessels():
    conn = get_connection()
    if conn:
        try:
            df = pd.read_sql("SELECT * FROM vessel_data", conn)
            conn.close()
            return df
        except Exception:
            pass
    csv_v = os.path.join(DATA_DIR, "vessel_data.csv")
    if os.path.exists(csv_v):
        return pd.read_csv(csv_v)
    return pd.DataFrame()

def load_ais_positions():
    conn = get_connection()
    if conn:
        try:
            df = pd.read_sql("SELECT * FROM ais_positions", conn)
            conn.close()
            return df
        except Exception:
            pass
    csv_a = os.path.join(DATA_DIR, "ais_positions.csv")
    if os.path.exists(csv_a):
        return pd.read_csv(csv_a)
    return pd.DataFrame()

def load_port_calls():
    conn = get_connection()
    if conn:
        try:
            df = pd.read_sql("SELECT * FROM port_calls", conn)
            conn.close()
            return df
        except Exception:
            pass
    csv_pc = os.path.join(DATA_DIR, "port_calls.csv")
    if os.path.exists(csv_pc):
        return pd.read_csv(csv_pc)
    return pd.DataFrame()

def load_congestion():
    conn = get_connection()
    if conn:
        try:
            df = pd.read_sql("SELECT * FROM congestion_data", conn)
            conn.close()
            return df
        except Exception:
            pass
    csv_c = os.path.join(DATA_DIR, "congestion_data.csv")
    if os.path.exists(csv_c):
        return pd.read_csv(csv_c)
    return pd.DataFrame()
