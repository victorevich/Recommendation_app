import sqlite3
import numpy as np
import json

class PreferenceStore:
    def __init__(self, db_path="data/preferences.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS profiles (
                browser_id TEXT PRIMARY KEY,
                global_vector TEXT,
                liked_count INTEGER DEFAULT 0
            )
        """)
        self.conn.commit()

    def update(self, browser_id: str, episode_vector: list[float]):
        row = self.conn.execute(
            "SELECT global_vector, liked_count FROM profiles WHERE browser_id=?",
            (browser_id,)
        ).fetchone()

        if row:
            old_vec = np.array(json.loads(row[0]))
            count = row[1]
            new_vec = (old_vec * count + np.array(episode_vector)) / (count + 1)
            self.conn.execute(
                "UPDATE profiles SET global_vector=?, liked_count=? WHERE browser_id=?",
                (json.dumps(new_vec.tolist()), count + 1, browser_id)
            )
        else:
            self.conn.execute(
                "INSERT INTO profiles VALUES (?, ?, 1)",
                (browser_id, json.dumps(episode_vector), )
            )
        self.conn.commit()

    def get_global_vector(self, browser_id: str) -> list[float] | None:
        row = self.conn.execute(
            "SELECT global_vector FROM profiles WHERE browser_id=?",
            (browser_id,)
        ).fetchone()
        return json.loads(row[0]) if row else None