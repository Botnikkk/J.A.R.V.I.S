import json
import os
import time
from datetime import datetime, timezone
from types import SimpleNamespace


class MessageStore:
    """Accumulates messages locally over time so analytics don't depend on
    a single deep live fetch (which Instagram caps server-side)."""

    def __init__(self, path="message_log.jsonl", sort_interval_hours=6):
        self.path = path
        self.seen_ids = set()
        self.sort_interval_seconds = sort_interval_hours * 3600
        self._sort_marker_path = path + ".last_sort"
        self._last_sort_time = self._load_last_sort_time()

        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    msg = json.loads(line)
                    self.seen_ids.add(msg["id"])

    def append_new(self, messages, user_mapping, exclude_user_id=None):
        """Appends new, real text messages. Normalizes all timestamps to UTC."""
        exclude_user_id = str(exclude_user_id) if exclude_user_id is not None else None
        new_count = 0
        with open(self.path, "a", encoding="utf-8") as f:
            for msg in messages:
                if getattr(msg, "item_type", None) != "text":
                    continue

                text = getattr(msg, "text", None)
                if not text:
                    continue

                user_id = str(msg.user_id)
                if exclude_user_id and user_id == exclude_user_id:
                    continue

                msg_id = getattr(msg, "id", None)
                if not msg_id or msg_id in self.seen_ids:
                    continue

                self.seen_ids.add(msg_id)

                ts = msg.timestamp
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                else:
                    ts = ts.astimezone(timezone.utc)

                f.write(json.dumps({
                    "id": msg_id,
                    "user_id": user_id,
                    "username": user_mapping.get(user_id, "Unknown"),
                    "text": text,
                    "timestamp": ts.isoformat(),
                }) + "\n")
                new_count += 1
        return new_count

    # --- Periodic sorting -------------------------------------------------

    def _load_last_sort_time(self):
        if os.path.exists(self._sort_marker_path):
            try:
                with open(self._sort_marker_path, "r") as f:
                    return float(f.read().strip())
            except (ValueError, OSError):
                return 0.0
        return 0.0

    def _save_last_sort_time(self, ts):
        with open(self._sort_marker_path, "w") as f:
            f.write(str(ts))

    def maybe_sort(self, force=False):
        """Re-sorts the log file on disk if the sort interval has elapsed.
        Cheap to call every loop iteration — it's a no-op until the interval
        passes. Returns True if a sort actually happened."""
        now = time.time()
        if not force and (now - self._last_sort_time) < self.sort_interval_seconds:
            return False

        self._sort_file()
        self._last_sort_time = now
        self._save_last_sort_time(now)
        return True

    def _sort_file(self):
        if not os.path.exists(self.path):
            return

        entries = []
        with open(self.path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    entries.append(json.loads(line))
        entries.sort(key=lambda e: e.get("timestamp", ""))

        tmp_path = self.path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            for e in entries:
                f.write(json.dumps(e) + "\n")

        os.replace(tmp_path, self.path) 
    def load_all(self, exclude_user_id=None):
        """Returns stored messages as objects with the same interface as
        instagrapi's DirectMessage. Normalizes both old (naive) and new (aware)
        timestamps to consistent UTC-aware datetime objects."""
        exclude_user_id = str(exclude_user_id) if exclude_user_id is not None else None
        out = []
        if not os.path.exists(self.path):
            return out

        with open(self.path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                raw = json.loads(line)
                if exclude_user_id and raw["user_id"] == exclude_user_id:
                    continue

                dt = datetime.fromisoformat(raw["timestamp"])
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                else:
                    dt = dt.astimezone(timezone.utc)

                out.append(SimpleNamespace(
                    id=raw["id"],
                    user_id=raw["user_id"],
                    text=raw["text"],
                    timestamp=dt,
                ))
        return out