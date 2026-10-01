"""
History Manager Module for Smart Agriculture Assistant.
Persists past farm analyses in a local SQLite database for history logging and retrieval.
"""
import sqlite3
import json
import datetime
from typing import Dict, Any, List, Optional
from config import HISTORY_DB_PATH


class HistoryManager:
    """Manages SQLite storage for farm assessments and recommendations."""

    def __init__(self, db_path=HISTORY_DB_PATH):
        self.db_path = str(db_path)
        self._init_db()

    def _get_connection(self):
        """Creates a database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Initializes tables if they do not exist."""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS farm_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    farm_name TEXT,
                    season TEXT,
                    n_val REAL,
                    p_val REAL,
                    k_val REAL,
                    temp REAL,
                    humidity REAL,
                    ph REAL,
                    rainfall REAL,
                    top_crop TEXT NOT NULL,
                    top_crop_score REAL NOT NULL,
                    soil_status TEXT,
                    analysis_json TEXT NOT NULL
                )
            """)
            conn.commit()

    def save_analysis(self, analysis_result: Dict[str, Any], farm_name: str = "My Farm") -> int:
        """Saves a complete farm analysis result."""
        inputs = analysis_result.get("inputs", {})
        primary = analysis_result.get("primary_recommendation", {})
        soil = analysis_result.get("soil_health", {})

        top_crop = primary.get("crop_name", "Unknown")
        top_score = primary.get("suitability_score", 0.0)
        soil_status = soil.get("overall_status", "Moderate")

        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with self._get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO farm_history (
                    timestamp, farm_name, season, n_val, p_val, k_val,
                    temp, humidity, ph, rainfall, top_crop, top_crop_score,
                    soil_status, analysis_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                now_str,
                farm_name or "My Farm",
                inputs.get("season", "All Season"),
                inputs.get("N", 0.0),
                inputs.get("P", 0.0),
                inputs.get("K", 0.0),
                inputs.get("temperature", 0.0),
                inputs.get("humidity", 0.0),
                inputs.get("ph", 6.5),
                inputs.get("rainfall", 0.0),
                top_crop,
                top_score,
                soil_status,
                json.dumps(analysis_result)
            ))
            conn.commit()
            return cursor.lastrowid

    def get_recent_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Retrieves recent farm assessment history summaries."""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT id, timestamp, farm_name, season, n_val, p_val, k_val,
                       temp, humidity, ph, rainfall, top_crop, top_crop_score, soil_status
                FROM farm_history
                ORDER BY id DESC
                LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    def get_analysis_by_id(self, record_id: int) -> Optional[Dict[str, Any]]:
        """Retrieves complete detailed analysis result by record ID."""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT analysis_json FROM farm_history WHERE id = ?
            """, (record_id,))
            row = cursor.fetchone()
            if row and row["analysis_json"]:
                return json.loads(row["analysis_json"])
            return None

    def clear_history(self) -> bool:
        """Deletes all history records."""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM farm_history")
            conn.commit()
            return True


# Global singleton instance
_history_mgr = None

def get_history_manager() -> HistoryManager:
    """Returns singleton HistoryManager instance."""
    global _history_mgr
    if _history_mgr is None:
        _history_mgr = HistoryManager()
    return _history_mgr
