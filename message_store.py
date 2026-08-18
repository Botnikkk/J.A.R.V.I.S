import json
import os
from datetime import datetime
from types import SimpleNamespace

class MessageStore:
    """Accumulates messages locally over time so analytics don't depend on
    a single deep live fetch (which Instagram caps server-side)."""

    def __init__(self, path="message_log.jsonl"):
        self.path = path
        self.seen_ids = set()
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    msg = json.loads(line)
                    self.seen_ids.add(msg["id"])

    def append_new(self, messages, user_mapping, exclude_user_id=None):
        """Appends new, real text messages (skips reactions/media/action
        logs and, optionally, a given user_id). Returns count added.

        Timestamps are stripped of timezone info before storage (converted
        to naive UTC) so every entry in the log stays in a consistent
        format — instagrapi returns timezone-aware datetimes, but earlier
        entries in this log were written naive, so we normalize going
        forward rather than leave a mixed format."""
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
                if ts.tzinfo is not None:
                    ts = ts.replace(tzinfo=None)

                f.write(json.dumps({
                    "id": msg_id,
                    "user_id": user_id,
                    "username": user_mapping.get(user_id, "Unknown"),
                    "text": text,
                    "timestamp": ts.isoformat(),
                }) + "\n")
                new_count += 1
        return new_count

    def load_all(self, exclude_user_id=None):
        """Returns stored messages as objects with the same interface as
        instagrapi's DirectMessage (.id, .user_id, .text, .timestamp)."""
        exclude_user_id = str(exclude_user_id) if exclude_user_id is not None else None
        out = []
        with open(self.path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                raw = json.loads(line)
                if exclude_user_id and raw["user_id"] == exclude_user_id:
                    continue
                out.append(SimpleNamespace(
                    id=raw["id"],
                    user_id=raw["user_id"],
                    text=raw["text"],
                    timestamp=datetime.fromisoformat(raw["timestamp"]),
                ))
        return out