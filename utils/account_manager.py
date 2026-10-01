"""SQLite-backed farmer accounts, farm profiles, reports, and sensor readings."""
import sqlite3
from typing import Any, Dict, List, Optional
from werkzeug.security import check_password_hash, generate_password_hash

from config import HISTORY_DB_PATH


class AccountManager:
    PROFILE_FIELDS = ("full_name", "mobile", "email", "address", "village", "district",
                      "state", "pincode", "preferred_language")
    FARM_FIELDS = ("name", "location", "village", "district", "state", "pincode", "size",
                   "size_unit", "farming_type", "irrigation_source", "current_crop", "soil_type",
                   "sowing_date", "expected_harvest_date", "previous_crop")

    def __init__(self, db_path=HISTORY_DB_PATH):
        self.db_path = str(db_path)
        self.init_db()

    def connection(self):
        conn = sqlite3.connect(self.db_path, timeout=8)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def init_db(self):
        with self.connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS farmers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    full_name TEXT NOT NULL,
                    mobile TEXT NOT NULL UNIQUE,
                    email TEXT COLLATE NOCASE UNIQUE,
                    password_hash TEXT NOT NULL,
                    address TEXT, village TEXT, district TEXT, state TEXT, pincode TEXT,
                    preferred_language TEXT NOT NULL DEFAULT 'English',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS farms (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    farmer_id INTEGER NOT NULL REFERENCES farmers(id) ON DELETE CASCADE,
                    name TEXT NOT NULL, location TEXT, village TEXT, district TEXT, state TEXT,
                    pincode TEXT, size REAL, size_unit TEXT, farming_type TEXT,
                    irrigation_source TEXT, current_crop TEXT, soil_type TEXT,
                    sowing_date TEXT, expected_harvest_date TEXT, previous_crop TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS idx_farms_farmer ON farms(farmer_id, id);
                CREATE TABLE IF NOT EXISTS soil_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    farmer_id INTEGER NOT NULL REFERENCES farmers(id) ON DELETE CASCADE,
                    farm_id INTEGER REFERENCES farms(id) ON DELETE SET NULL,
                    filename TEXT NOT NULL, stored_path TEXT NOT NULL,
                    extracted_json TEXT NOT NULL, verified INTEGER NOT NULL DEFAULT 0,
                    uploaded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS idx_reports_farmer ON soil_reports(farmer_id, id DESC);
                CREATE TABLE IF NOT EXISTS sensor_readings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    farmer_id INTEGER NOT NULL REFERENCES farmers(id) ON DELETE CASCADE,
                    farm_id INTEGER REFERENCES farms(id) ON DELETE SET NULL,
                    device_id TEXT, source TEXT NOT NULL,
                    reading_json TEXT NOT NULL,
                    captured_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
            """)

    @staticmethod
    def _row(row):
        return dict(row) if row else None

    def create_farmer(self, fields: Dict[str, Any], password: str) -> int:
        with self.connection() as conn:
            cur = conn.execute("""
                INSERT INTO farmers (full_name, mobile, email, password_hash, address, village,
                    district, state, pincode, preferred_language)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (fields["full_name"], fields["mobile"], fields.get("email") or None,
                  generate_password_hash(password), fields.get("address"), fields.get("village"),
                  fields.get("district"), fields.get("state"), fields.get("pincode"),
                  fields.get("preferred_language") or "English"))
            return cur.lastrowid

    def authenticate(self, login: str, password: str) -> Optional[Dict[str, Any]]:
        with self.connection() as conn:
            row = conn.execute("""SELECT * FROM farmers WHERE mobile = ? OR email = ? COLLATE NOCASE""",
                               (login, login)).fetchone()
        if row and check_password_hash(row["password_hash"], password):
            result = self._row(row)
            result.pop("password_hash", None)
            return result
        return None

    def get_farmer(self, farmer_id: int) -> Optional[Dict[str, Any]]:
        with self.connection() as conn:
            row = conn.execute("SELECT * FROM farmers WHERE id = ?", (farmer_id,)).fetchone()
        result = self._row(row)
        if result:
            result.pop("password_hash", None)
        return result

    def update_profile(self, farmer_id: int, fields: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        assignments = ", ".join(f"{name} = ?" for name in self.PROFILE_FIELDS)
        values = [fields.get(name) or None for name in self.PROFILE_FIELDS]
        with self.connection() as conn:
            conn.execute(f"UPDATE farmers SET {assignments} WHERE id = ?", (*values, farmer_id))
        return self.get_farmer(farmer_id)

    def list_farms(self, farmer_id: int) -> List[Dict[str, Any]]:
        with self.connection() as conn:
            rows = conn.execute("SELECT * FROM farms WHERE farmer_id = ? ORDER BY id", (farmer_id,)).fetchall()
        return [dict(row) for row in rows]

    def get_farm(self, farmer_id: int, farm_id: int) -> Optional[Dict[str, Any]]:
        with self.connection() as conn:
            row = conn.execute("SELECT * FROM farms WHERE id = ? AND farmer_id = ?", (farm_id, farmer_id)).fetchone()
        return self._row(row)

    def save_farm(self, farmer_id: int, fields: Dict[str, Any], farm_id: Optional[int] = None) -> int:
        values = [fields.get(name) or None for name in self.FARM_FIELDS]
        with self.connection() as conn:
            if farm_id:
                cursor = conn.execute(f"UPDATE farms SET {', '.join(f'{name} = ?' for name in self.FARM_FIELDS)} "
                                      "WHERE id = ? AND farmer_id = ?", (*values, farm_id, farmer_id))
                if cursor.rowcount != 1:
                    raise LookupError("Farm not found.")
                return farm_id
            cursor = conn.execute(f"INSERT INTO farms (farmer_id, {', '.join(self.FARM_FIELDS)}) "
                                  f"VALUES (?, {', '.join('?' for _ in self.FARM_FIELDS)})", (farmer_id, *values))
            return cursor.lastrowid

    def delete_farm(self, farmer_id: int, farm_id: int) -> bool:
        with self.connection() as conn:
            cur = conn.execute("DELETE FROM farms WHERE id = ? AND farmer_id = ?", (farm_id, farmer_id))
            return cur.rowcount == 1

    def save_report(self, farmer_id: int, farm_id: Optional[int], filename: str,
                    stored_path: str, extracted: Dict[str, Any]) -> int:
        import json
        with self.connection() as conn:
            cur = conn.execute("""INSERT INTO soil_reports
                (farmer_id, farm_id, filename, stored_path, extracted_json) VALUES (?, ?, ?, ?, ?)""",
                (farmer_id, farm_id, filename, stored_path, json.dumps(extracted)))
            return cur.lastrowid

    def list_reports(self, farmer_id: int) -> List[Dict[str, Any]]:
        import json
        with self.connection() as conn:
            rows = conn.execute("""SELECT r.id, r.farm_id, r.filename, r.extracted_json, r.verified,
                r.uploaded_at, f.name AS farm_name FROM soil_reports r
                LEFT JOIN farms f ON f.id = r.farm_id WHERE r.farmer_id = ? ORDER BY r.id DESC""",
                                (farmer_id,)).fetchall()
        reports = []
        for row in rows:
            record = dict(row)
            record["values"] = json.loads(record.pop("extracted_json"))
            reports.append(record)
        return reports

    def verify_report(self, farmer_id: int, report_id: int, extracted: Optional[Dict[str, Any]] = None) -> bool:
        import json
        with self.connection() as conn:
            if extracted is None:
                cur = conn.execute("UPDATE soil_reports SET verified = 1 WHERE id = ? AND farmer_id = ?",
                                   (report_id, farmer_id))
            else:
                serialized = {field: {"value": extracted.get(field), "unit": "kg/ha" if field in {"N", "P", "K"} else "",
                                      "source": "soil_report", "status": "verified" if extracted.get(field) is not None else "not_detected"}
                              for field in ("N", "P", "K", "ph")}
                cur = conn.execute("UPDATE soil_reports SET verified = 1, extracted_json = ? WHERE id = ? AND farmer_id = ?",
                                   (json.dumps(serialized), report_id, farmer_id))
            return cur.rowcount == 1

    def save_sensor_reading(self, farmer_id: int, farm_id: Optional[int], device_id: str,
                            source: str, reading: Dict[str, Any]) -> int:
        import json
        with self.connection() as conn:
            cur = conn.execute("""INSERT INTO sensor_readings
                (farmer_id, farm_id, device_id, source, reading_json) VALUES (?, ?, ?, ?, ?)""",
                (farmer_id, farm_id, device_id, source, json.dumps(reading)))
            return cur.lastrowid
